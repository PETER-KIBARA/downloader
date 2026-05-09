"""
Universal Media Downloader - Backend Starter Code (Python/FastAPI)
Author: Senior Full-Stack Developer
Version: 0.1.0 (MVP)
"""

import os
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from enum import Enum
import subprocess
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, HttpUrl, validator
import yt_dlp
import redis
from celery import Celery

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Media Downloader", version="0.1.0")

# CORS Configuration (restrict to frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Redis connection
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Celery configuration for background jobs
celery_app = Celery(
    "umd_downloader",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_BACKEND_URL", "redis://localhost:6379/1"),
)

STORAGE_PATH = os.getenv("STORAGE_PATH", "/tmp/umd_downloads")
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
DOWNLOAD_TIMEOUT = 1800  # 30 minutes


# ============================================================================
# DATA MODELS
# ============================================================================

class PlatformEnum(str, Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    PINTEREST = "pinterest"
    LINKEDIN = "linkedin"


class FormatEnum(str, Enum):
    MP4 = "mp4"
    MP3 = "mp3"
    MOV = "mov"


class QualityEnum(str, Enum):
    HD_720P = "720p"
    FULL_HD = "1080p"
    UHD_4K = "4k"


class DownloadRequest(BaseModel):
    """Request model for download initiation"""
    url: HttpUrl
    format: FormatEnum = FormatEnum.MP4
    quality: QualityEnum = QualityEnum.FULL_HD

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format and platform support"""
        url_str = str(v)
        supported_domains = [
            "youtube.com", "youtu.be",
            "tiktok.com", "vm.tiktok.com",
            "instagram.com",
            "twitter.com", "x.com",
            "facebook.com",
            "pinterest.com",
            "linkedin.com"
        ]
        
        if not any(domain in url_str for domain in supported_domains):
            raise ValueError("URL is from an unsupported platform")
        
        return v


class DownloadResponse(BaseModel):
    """Response model for download jobs"""
    job_id: str
    platform: PlatformEnum
    title: Optional[str] = None
    status: str  # queued, processing, completed, failed
    progress: int = 0  # 0-100
    estimated_time: Optional[int] = None  # seconds


class StatusResponse(BaseModel):
    """Response for status check"""
    job_id: str
    status: str
    progress: int
    estimated_time: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# PLATFORM DETECTION
# ============================================================================

def detect_platform(url: str) -> PlatformEnum:
    """Detect which platform the URL belongs to"""
    url_lower = url.lower()
    
    platform_patterns = {
        PlatformEnum.YOUTUBE: r"(youtube\.com|youtu\.be)",
        PlatformEnum.TIKTOK: r"(tiktok\.com|vm\.tiktok\.com)",
        PlatformEnum.INSTAGRAM: r"instagram\.com",
        PlatformEnum.TWITTER: r"(twitter\.com|x\.com)",
        PlatformEnum.FACEBOOK: r"facebook\.com",
        PlatformEnum.PINTEREST: r"pinterest\.com",
        PlatformEnum.LINKEDIN: r"linkedin\.com",
    }
    
    for platform, pattern in platform_patterns.items():
        if re.search(pattern, url_lower):
            return platform
    
    raise ValueError(f"Could not detect platform for URL: {url}")


# ============================================================================
# YT-DLP HANDLERS
# ============================================================================

class MediaExtractor:
    """Main media extraction handler using yt-dlp"""
    
    def __init__(self):
        self.ydl_opts = {
            "quiet": False,
            "no_warnings": False,
            "outtmpl": os.path.join(STORAGE_PATH, "%(title)s.%(ext)s"),
            "socket_timeout": DOWNLOAD_TIMEOUT,
        }
    
    def extract_metadata(self, url: str) -> Dict:
        """Extract metadata without downloading"""
        opts = {**self.ydl_opts, "skip_download": True}
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "formats": self._parse_formats(info.get("formats", [])),
                }
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            raise
    
    def _parse_formats(self, formats: List[Dict]) -> List[Dict]:
        """Parse available formats from yt-dlp response"""
        available_formats = []
        
        for fmt in formats:
            if fmt.get("vcodec") != "none" and fmt.get("acodec") != "none":
                height = fmt.get("height", 0)
                if height in [720, 1080, 2160]:
                    available_formats.append({
                        "format_id": fmt.get("format_id"),
                        "quality": f"{height}p",
                        "ext": fmt.get("ext"),
                    })
        
        return available_formats
    
    def download_media(self, url: str, quality: str = "1080") -> str:
        """Download media file"""
        opts = {
            **self.ydl_opts,
            "format": f"bestvideo[height<={quality}]+bestaudio/best",
            "merge_output_format": "mp4",
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise


# ============================================================================
# CELERY BACKGROUND TASKS
# ============================================================================

@celery_app.task(bind=True)
def download_media_task(self, job_id: str, url: str, quality: str, format_type: str):
    """Background task for media download and processing"""
    try:
        redis_client.hset(f"job:{job_id}", "status", "processing")
        redis_client.hset(f"job:{job_id}", "progress", "10")
        
        extractor = MediaExtractor()
        
        # Extract metadata
        metadata = extractor.extract_metadata(url)
        redis_client.hset(f"job:{job_id}", "title", metadata["title"])
        redis_client.hset(f"job:{job_id}", "progress", "25")
        
        # Download media
        media_file = extractor.download_media(url, quality)
        redis_client.hset(f"job:{job_id}", "progress", "75")
        
        # Process/transcode if needed
        if format_type != "mp4":
            media_file = transcode_media(media_file, format_type)
        
        redis_client.hset(f"job:{job_id}", "progress", "90")
        redis_client.hset(f"job:{job_id}", "file_path", media_file)
        redis_client.hset(f"job:{job_id}", "status", "completed")
        redis_client.hset(f"job:{job_id}", "progress", "100")
        
        # Schedule cleanup after 24 hours
        cleanup_task.apply_async((job_id,), countdown=86400)
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        redis_client.hset(f"job:{job_id}", "status", "failed")
        redis_client.hset(f"job:{job_id}", "error", str(e))
        raise


@celery_app.task
def cleanup_task(job_id: str):
    """Cleanup temporary files after 24 hours"""
    try:
        file_path = redis_client.hget(f"job:{job_id}", "file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file for job {job_id}")
    except Exception as e:
        logger.error(f"Cleanup failed for job {job_id}: {str(e)}")


def transcode_media(file_path: str, target_format: str) -> str:
    """Transcode media to target format using FFmpeg"""
    output_path = file_path.replace(".mp4", f".{target_format}")
    
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", file_path,
        "-codec:v", "libx264" if target_format == "mp4" else "mpeg4",
        "-crf", "23",
        "-codec:a", "aac",
        "-b:a", "192k",
        output_path,
        "-y"  # Overwrite output file
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=DOWNLOAD_TIMEOUT)
        return output_path
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Transcoding timeout for {file_path}")
    except Exception as e:
        raise RuntimeError(f"Transcoding failed: {str(e)}")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/api/download", response_model=DownloadResponse)
async def initiate_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Initiate a media download
    
    POST /api/download
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "format": "mp4",
        "quality": "1080p"
    }
    """
    try:
        url = str(request.url)
        platform = detect_platform(url)
        
        # Generate unique job ID
        job_id = f"{platform.value}_{int(datetime.now().timestamp())}"
        
        # Store job metadata in Redis
        redis_client.hset(f"job:{job_id}", mapping={
            "platform": platform.value,
            "url": url,
            "format": request.format.value,
            "quality": request.quality.value,
            "status": "queued",
            "progress": "0",
            "created_at": datetime.now().isoformat(),
        })
        
        # Queue background task
        download_media_task.delay(job_id, url, request.quality.value, request.format.value)
        
        logger.info(f"Download initiated - Job ID: {job_id}, Platform: {platform.value}")
        
        return DownloadResponse(
            job_id=job_id,
            platform=platform,
            status="queued",
            progress=0
        )
    
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Download initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/download/{job_id}/status", response_model=StatusResponse)
async def get_download_status(job_id: str):
    """
    Check download job status
    
    GET /api/download/{job_id}/status
    """
    try:
        job_data = redis_client.hgetall(f"job:{job_id}")
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job_data.get(b"status", b"unknown").decode()
        progress = int(job_data.get(b"progress", b"0"))
        error = job_data.get(b"error", b"").decode() or None
        
        return StatusResponse(
            job_id=job_id,
            status=status,
            progress=progress,
            error=error
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/download/{job_id}/file")
async def download_file(job_id: str):
    """
    Download the processed file
    
    GET /api/download/{job_id}/file
    """
    try:
        job_data = redis_client.hgetall(f"job:{job_id}")
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job_data.get(b"status", b"unknown").decode()
        
        if status != "completed":
            raise HTTPException(status_code=400, detail=f"Job status is {status}")
        
        file_path = job_data.get(b"file_path", b"").decode()
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path, filename=os.path.basename(file_path))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
        },
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    os.makedirs(STORAGE_PATH, exist_ok=True)
    logger.info(f"Application started. Storage path: {STORAGE_PATH}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    redis_client.close()
    logger.info("Application shutdown")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend_starter:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development"
    )
