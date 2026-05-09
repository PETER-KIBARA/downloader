# Universal Media Downloader - Technical Blueprint

## Executive Summary
A unified web application enabling users to download media from major social platforms through a single, intuitive interface with format/quality options while maintaining user privacy and platform compliance.

---

## 1. HIGH-LEVEL ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React/Vue 3 Frontend (Mobile-Responsive)               │   │
│  │  • Link Input Field                                      │   │
│  │  • Platform Detection                                    │   │
│  │  • Format/Quality Selector                               │   │
│  │  • Download Progress Tracker                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
                    [API Gateway / REST]
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Link Validation & Platform Detection Service           │   │
│  │  • Regex pattern matching for URLs                       │   │
│  │  • Platform identification logic                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Media Extraction Engine (Router)                        │   │
│  │  ├─ YouTube Handler → yt-dlp                             │   │
│  │  ├─ TikTok Handler → TikTok API / yt-dlp                 │   │
│  │  ├─ Instagram Handler → instagrapi / Instagram API       │   │
│  │  ├─ X (Twitter) Handler → tweepy / x-downloader          │   │
│  │  ├─ Facebook Handler → facebook-sdk / yt-dlp             │   │
│  │  ├─ Pinterest Handler → Pinterest API / selenium         │   │
│  │  └─ LinkedIn Handler → linkedin-api / browser automation │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Format & Quality Processor                              │   │
│  │  • FFmpeg integration for transcoding                    │   │
│  │  • Quality preset generation                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  File Management & Delivery                              │   │
│  │  • Temporary storage (Redis/temp files)                  │   │
│  │  • Cleanup scheduler                                     │   │
│  │  • Direct download links                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DATA & STORAGE LAYER                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │   PostgreSQL   │  │     Redis      │  │  File Storage  │   │
│  │  (Metadata)    │  │  (Cache/Queue) │  │   (S3/Local)   │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. SYSTEM ARCHITECTURE FLOW

```
User Input (URL) 
    ↓
[Validate URL Format]
    ↓
[Detect Platform Type]
    ↓
[Route to Platform Handler]
    ↓
[Fetch Media Metadata (title, duration, available formats)]
    ↓
[Present Options to User]
    ↓
[User Selects Format & Quality]
    ↓
[Queue Download Job]
    ↓
[Download Media]
    ↓
[Process/Transcode if needed]
    ↓
[Generate Download Link]
    ↓
[Client Downloads File]
    ↓
[Schedule Cleanup]
```

---

## 3. TECHNOLOGY STACK RECOMMENDATIONS

### Frontend
- **Framework**: React 18 or Vue 3
- **Styling**: Tailwind CSS (responsive, modern)
- **State Management**: Zustand (React) or Pinia (Vue)
- **HTTP Client**: Axios or React Query
- **Progress Tracking**: Custom hooks or libraries (react-circular-progressbar)
- **Mobile**: Responsive design + PWA capabilities

### Backend
- **Runtime**: Node.js (Express/Fastify) or Python (FastAPI/Flask)
- **Queue System**: Bull (Node.js) or Celery (Python)
- **Caching**: Redis
- **Database**: PostgreSQL

### Media Processing
- **Video Download**: `yt-dlp` (YouTube, TikTok, Instagram, Facebook, Twitter, Pinterest)
- **Transcoding**: `FFmpeg`
- **Instagram**: `instagrapi` (Python) for Stories/Reels
- **LinkedIn**: Browser automation with Playwright/Puppeteer
- **X/Twitter**: `tweepy` API or custom scraper

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose (local), Kubernetes (production)
- **Reverse Proxy**: Nginx
- **File Storage**: AWS S3 or local NAS

---

## 4. DETAILED TECH STACK BY PLATFORM

| Platform | Primary Library | Fallback | Notes |
|----------|-----------------|----------|-------|
| YouTube | yt-dlp | pytube | 4K support, best quality options |
| TikTok | yt-dlp | TikTok API | Watermark removal via yt-dlp |
| Instagram | instagrapi | instagram-scraper | Stories & Reels support |
| X/Twitter | tweepy | x-downloader | Official API (Premium tier) |
| Facebook | yt-dlp | facebook-downloader | Limited by platform restrictions |
| Pinterest | yt-dlp | pinterest-downloader | Pin/video extraction |
| LinkedIn | Playwright/Puppeteer | selenium | Professional videos only |

---

## 5. USER INTERFACE WIREFRAME

### Main Screen (Desktop & Mobile)

```
╔═════════════════════════════════════════════
║  📱 UniDownload - Universal Media Downloader║
╚════════════════════════════════════════════╛

┌─────────────────────────────────────────────┐
│  🔗 Paste Media Link Here                   │
│  ┌──────────────────────────────────────┐   │
│  │ https://www.youtube.com/watch?v=... │   │
│  └──────────────────────────────────────┘   │
│  [👁️ Detect] [✖ Clear]                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  ✅ Platform Detected: YouTube              │
│  📹 Title: Sample Video [1:23:45]           │
│  
│  Format Selection:                          │
│  ◉ MP4 ○ MP3 ○ MOV                        │
│  
│  Quality Preset:                            │
│  ○ 720p  ○ 1080p  ◉ 4K (2160p) [Best]    │
│  
│  Audio Quality: ○ 128kbps ◉ 256kbps       │
│  
│  [📥 Download] [⚙️ More Options]           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Status: Processing...                      │
│  [====░░░░░░░░░░░░] 35% Complete          │
│  Estimated Time: 2m 45s                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  💾 Downloads (Last 24h)                    │
│  • my_video.mp4 (2.3 GB) - 2h ago         │
│  • song_audio.mp3 (8.5 MB) - 5h ago       │
└─────────────────────────────────────────────┘
```

### Mobile View (Single Column)
- Optimized input field with keyboard detection
- Stacked format/quality selectors
- Touch-friendly download buttons
- Minimal layout, maximum functionality

---

## 6. APIs & LIBRARIES COMPREHENSIVE LIST

### Core Libraries

```python
# Python Backend Recommendations
yt-dlp==2024.01.01              # Multi-platform downloader
instagrapi==2.0.0                # Instagram scraping
tweepy==4.14.0                   # Twitter/X API
fastapi==0.104.0                 # Web framework
redis==5.0.0                     # Caching
celery==5.3.0                    # Task queue
sqlalchemy==2.0.0                # ORM
pydantic==2.0.0                  # Data validation
requests==2.31.0                 # HTTP client
ffmpeg-python==0.2.1             # FFmpeg wrapper
python-dotenv==1.0.0             # Environment vars
```

### JavaScript/Node.js Alternatives
```json
{
  "yt-dlp-wrap": "^0.8.0",        // JavaScript wrapper for yt-dlp
  "express": "^4.18.0",
  "redis": "^4.6.0",
  "bull": "^4.10.0",
  "puppeteer": "^21.0.0",
  "fluent-ffmpeg": "^2.1.2",
  "axios": "^1.6.0",
  "multer": "^1.4.0"
}
```

---

## 7. USER FLOW DIAGRAM

```
START
  ↓
[User Opens App]
  ↓
[Paste Media Link]
  ↓
[VALIDATE URL] → Invalid? → Show Error → Paste New Link ↶
  ↓
[DETECT PLATFORM]
  ↓
[FETCH METADATA] 
  ├─ Title, Duration, Thumbnail
  ├─ Available Formats
  └─ Quality Options
  ↓
[DISPLAY OPTIONS TO USER]
  ├─ Format: MP4 / MP3 / MOV
  ├─ Quality Presets
  └─ Audio Options
  ↓
[User Selects & Confirms]
  ↓
[QUEUE DOWNLOAD JOB]
  ↓
[SHOW PROGRESS BAR]
  ├─ Real-time % completion
  ├─ Estimated time
  └─ Speed/bandwidth info
  ↓
[PROCESS COMPLETE]
  ↓
[GENERATE DOWNLOAD LINK]
  ↓
[Auto-Download to Client]
  ↓
[Show Success Message]
  ├─ File size
  ├─ Save location
  └─ Option to download again
  ↓
[CLEANUP] (Delete temp file after 24h)
  ↓
END
```

---

## 8. PRIVACY & SECURITY MEASURES

### Privacy Protection
1. **No Account Required**
   - Completely anonymous downloads
   - No user tracking or analytics
   - No cookies unless explicitly consented (GDPR compliant)

2. **Data Handling**
   - Minimal server-side logging (only errors)
   - No storage of downloaded media beyond processing
   - Temporary files encrypted at rest
   - 24-hour automatic cleanup

3. **HTTPS Only**
   - All communications encrypted TLS 1.3
   - Certificate pinning for API calls

### Security Measures
1. **Input Validation**
   - Strict URL format validation (regex + URI parsing)
   - Blacklist suspicious domains
   - Rate limiting (max 30 requests/hour per IP)

2. **Malware Prevention**
   - Scan files with ClamAV before download
   - Verify file signatures
   - Sandboxed video processing
   - yt-dlp kept updated (automatic daily checks)

3. **Resource Protection**
   - Max file size: 5GB per download
   - Timeout protection: 30-minute max execution
   - CPU/memory limits per job
   - Queue system prevents DDoS

4. **CORS & API Security**
   - Strict CORS policy (whitelist origins)
   - API key rotation
   - JWT authentication for premium features
   - Rate limiting per user/IP

---

## 9. ERROR HANDLING STRATEGY

### Error Detection & Response

| Error Scenario | Detection | User Response |
|---|---|---|
| **Invalid URL** | Regex validation fails | "Please enter a valid URL (e.g., youtube.com/watch?v=...)" |
| **Unsupported Platform** | Domain not in whitelist | "Platform not supported. Try: YouTube, TikTok, Instagram, X, Facebook, LinkedIn, Pinterest" |
| **Private Content** | 403/401 from platform API | "This content is private. Only the owner can download it." |
| **Deleted Content** | 404 from platform | "Video no longer exists. It may have been deleted or removed." |
| **Region Blocking** | Geo-restricted error | "This content is not available in your region." |
| **Age Restriction** | Platform age gate | "This content requires age verification on the platform." |
| **Copyright Strike** | Platform refusal | "This content cannot be downloaded due to copyright protection." |
| **Network Timeout** | Connection timeout | "Download timed out. Please try again or check your connection." |
| **Server Overloaded** | Queue full | "System is busy. Queued #45. Estimated wait: 12 minutes." |
| **Storage Full** | Disk space error | "Server storage is full. Please try again later." |
| **FFmpeg Failure** | Transcoding error | "Format conversion failed. Try a different quality option." |

### Error Recovery Strategies
```
1. Automatic Retry (3x with exponential backoff)
   → 2s delay → 8s delay → 32s delay

2. Fallback Options
   → Can't get 4K? → Try 1080p
   → Platform API down? → Try yt-dlp scraper

3. Graceful Degradation
   → If format transcoding fails, offer original format
   → If metadata fetch slow, show generic options

4. User Notifications
   → Toasts for recoverable errors
   → Modal dialogs for blocking issues
   → Email backup for session recovery
```

---

## 10. IMPLEMENTATION ROADMAP

### Phase 1: MVP (Weeks 1-2)
- [x] Design architecture
- [ ] Setup environment (Node/Python, Docker)
- [ ] Basic React frontend with input field
- [ ] YouTube + TikTok support via yt-dlp
- [ ] Single quality/format option
- [ ] Basic error handling

### Phase 2: Enhanced (Weeks 3-4)
- [ ] Format selector (MP4, MP3)
- [ ] Quality presets (720p, 1080p, 4K)
- [ ] Instagram + X support
- [ ] Progress tracking UI
- [ ] File cleanup scheduler

### Phase 3: Advanced (Weeks 5-6)
- [ ] Facebook + Pinterest + LinkedIn
- [ ] Audio extraction/codec selection
- [ ] Download history feature
- [ ] Advanced error handling
- [ ] Security scanning (ClamAV)

### Phase 4: Polish (Weeks 7-8)
- [ ] Mobile responsiveness
- [ ] PWA implementation
- [ ] Performance optimization
- [ ] Analytics (privacy-respecting)
- [ ] Production deployment

---

## 11. DATABASE SCHEMA (PostgreSQL)

```sql
-- Downloads metadata
CREATE TABLE downloads (
    id UUID PRIMARY KEY,
    user_ip INET,
    platform VARCHAR(50),
    original_url TEXT,
    media_title VARCHAR(500),
    duration_seconds INT,
    format VARCHAR(10),
    quality VARCHAR(20),
    file_size_bytes BIGINT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Platform tokens (API keys)
CREATE TABLE platform_tokens (
    id UUID PRIMARY KEY,
    platform VARCHAR(50),
    access_token TEXT ENCRYPTED,
    refresh_token TEXT ENCRYPTED,
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Error logs
CREATE TABLE error_logs (
    id UUID PRIMARY KEY,
    download_id UUID REFERENCES downloads(id),
    error_type VARCHAR(100),
    error_message TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP
);
```

---

## 12. DEPLOYMENT CONSIDERATIONS

### Local Development
```bash
docker-compose up -d
# Services: backend (FastAPI), frontend (React dev), Redis, PostgreSQL
```

### Production
- **Hosting**: AWS EC2 / DigitalOcean / Render
- **CDN**: CloudFlare (DDoS protection + caching)
- **File Storage**: AWS S3 (temporary media)
- **Database**: AWS RDS (PostgreSQL)
- **Monitoring**: Datadog / New Relic
- **CI/CD**: GitHub Actions

### Legal Compliance
- **ToS**: Clearly state platform ToS compliance obligation
- **GDPR**: Privacy policy + data handling transparency
- **DMCA**: Include DMCA takedown process
- **Licensing**: Open-source components properly attributed

---

## 13. PERFORMANCE OPTIMIZATION STRATEGIES

### Backend
- Async/await for I/O operations
- Caching metadata in Redis (24h TTL)
- Parallel format detection
- Connection pooling for databases
- Lazy loading of video metadata

### Frontend
- Code splitting at route level
- Image lazy loading
- Service worker for offline detection
- IndexedDB for download history cache

### Media Processing
- Stream processing (don't wait for full download)
- Quality downsampling on-the-fly
- Parallel FFmpeg jobs
- Hardware acceleration (GPU transcoding)

---

## 14. TESTING STRATEGY

```
Unit Tests
├─ URL validation logic
├─ Platform detection
├─ Format conversion rules
└─ Error message mapping

Integration Tests
├─ Download → Upload → Cleanup
├─ Multi-platform workflows
└─ API response handling

E2E Tests (Selenium/Playwright)
├─ Full download workflows per platform
├─ Error scenarios
└─ Mobile responsiveness

Load Tests
├─ 100 concurrent downloads
├─ Server capacity determination
└─ Queue behavior under stress
```

---

## 15. COST ESTIMATION (Monthly, Production Scale)

| Component | Cost | Notes |
|-----------|------|-------|
| AWS EC2 (2x t3.medium) | $80 | Backend servers |
| RDS PostgreSQL (db.t3.small) | $60 | Database |
| S3 Storage + Transfer | $200 | 1TB stored, 500GB/month out |
| CloudFlare Pro | $20 | DDoS + caching |
| Bandwidth (500GB) | $100 | Additional egress |
| **Total** | **~$460** | Scales to $1000+ at 100M users/mo |

---

## CONCLUSION

This blueprint provides a scalable, privacy-focused, and user-friendly media downloader. Key differentiators:
- **Single interface** for 7+ platforms
- **Privacy-first** design (no tracking, encrypted)
- **Robust error handling** for all edge cases
- **Modular architecture** allowing easy addition of new platforms
- **Production-ready** security and compliance

Next step: Begin Phase 1 MVP development with YouTube + TikTok support.
