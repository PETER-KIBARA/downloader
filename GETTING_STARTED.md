# Universal Media Downloader - Getting Started Guide

## 📋 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/universal-media-downloader.git
cd universal-media-downloader

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Initialize database
docker-compose exec backend alembic upgrade head

# Create tables
docker-compose exec backend python -c "from backend_starter import *; create_tables()"

# Check status
docker-compose ps
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Option 2: Manual Setup (Development)

#### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../.env.example .env

# Start Redis
# On macOS: brew services start redis
# On Linux: sudo systemctl start redis-server
# Or use Docker: docker run -d -p 6379:6379 redis:7-alpine

# Run migrations
alembic upgrade head

# Start backend server
uvicorn backend_starter:app --reload

# In another terminal, start Celery worker
celery -A backend_starter worker --loglevel=info
```

#### Frontend Setup
```bash
# Navigate to frontend (ensure Node.js installed)
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Open browser to http://localhost:3000
```

---

## 🏗️ Project Structure

```
universal-media-downloader/
├── backend/
│   ├── backend_starter.py       # Main FastAPI application
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile.backend       # Docker configuration
│   └── tests/
│       └── test_api.py          # API tests
│
├── frontend/
│   ├── frontend_starter.jsx     # Main React component
│   ├── styles.css               # Styling
│   ├── package.json             # Node dependencies
│   └── Dockerfile.frontend      # Docker configuration
│
├── docker-compose.yml           # Multi-container setup
├── .env.example                 # Environment template
├── requirements.txt             # Python deps
├── TECHNICAL_BLUEPRINT.md       # Full technical documentation
└── README.md                    # This file
```

---

## 🔐 Security Checklist

### Before Production Deployment
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Update database credentials
- [ ] Configure HTTPS/SSL certificates
- [ ] Enable rate limiting
- [ ] Enable ClamAV virus scanning
- [ ] Setup logging and monitoring
- [ ] Configure CORS for production domain
- [ ] Enable security headers in Nginx
- [ ] Setup backup strategy
- [ ] Review privacy policy

### Commands to Run
```bash
# Generate strong secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SSL certificates (self-signed for testing)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

---

## 🧪 Testing

### Run Tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov

# Frontend tests
cd frontend
npm test -- --coverage
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## 📊 Monitoring & Debugging

### View Logs
```bash
# Docker
docker-compose logs backend -f
docker-compose logs frontend -f
docker-compose logs celery-worker -f

# Manual
tail -f /var/log/umd/app.log
```

### Database Access
```bash
# PostgreSQL
docker-compose exec postgres psql -U umd_user -d umd_db

# Redis
docker-compose exec redis redis-cli
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🚀 Deployment

### Production Deployment (Ubuntu/AWS)

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y \
  docker.io \
  docker-compose \
  nginx \
  certbot \
  python3-certbot-nginx \
  ffmpeg

# 2. Clone repository
git clone https://github.com/yourusername/universal-media-downloader.git
cd universal-media-downloader

# 3. Configure environment
cp .env.example .env
# Edit .env with production values

# 4. Setup SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Setup automatic updates
0 2 * * * cd /app && git pull && docker-compose up -d
```

### Cloud Deployment Options
- **AWS**: ECS, Lambda, RDS
- **Google Cloud**: Cloud Run, Cloud SQL
- **Azure**: App Service, SQL Database
- **Heroku**: Buildpacks with Procfile
- **DigitalOcean**: App Platform + Managed Databases

### Render Deployment (No Timeout Setup)

This repo includes `render.yaml` with two services:
- `umd-api` (**Web Service**): FastAPI app, binds to `$PORT`, health check at `/api/health`
- `umd-telegram-bot` (**Background Worker**): Telegram polling bot (`python telegram_bot.py`)

Deploy steps:
```bash
# Push repo to GitHub, then create Blueprint on Render
# Render will detect render.yaml automatically
```

Important rules:
- Do **not** deploy `telegram_bot.py` as a Web Service.
- Polling bots must run as **Background Workers**.
- Web services must listen on `0.0.0.0:$PORT`.

---

## 🐛 Troubleshooting

### "Connection refused" on Port 8000
```bash
# Check if service is running
docker-compose ps

# View logs
docker-compose logs backend

# Restart service
docker-compose restart backend
```

### Redis Connection Error
```bash
# Verify Redis is running
docker-compose exec redis redis-cli ping
# Should respond with PONG

# Restart Redis
docker-compose restart redis
```

### Database Migration Issues
```bash
# Reset database (CAUTION: deletes data)
docker-compose exec postgres dropdb -U umd_user umd_db
docker-compose exec postgres createdb -U umd_user umd_db
docker-compose exec backend alembic upgrade head
```

### Frontend not connecting to backend
- Check CORS settings in `.env`
- Verify `REACT_APP_API_URL` is correct
- Check browser console for CORS errors
- Ensure backend service is running

---

## 📈 Performance Optimization

### Backend
```python
# Enable caching
REDIS_CACHE_ENABLED=True

# Use connection pooling
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600
```

### Frontend
```bash
# Build for production
npm run build

# Use CDN for static assets
export CDN_URL="https://cdn.yourdomain.com"
npm run build
```

### Infrastructure
- Use CloudFlare for DDoS protection
- Enable gzip compression in Nginx
- Use CDN for media files
- Implement auto-scaling for Celery workers

---

## 📝 API Reference

### Initiate Download
```bash
curl -X POST http://localhost:8000/api/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "mp4",
    "quality": "1080p"
  }'
```

### Check Status
```bash
curl http://localhost:8000/api/download/{job_id}/status
```

### Download File
```bash
curl http://localhost:8000/api/download/{job_id}/file --output video.mp4
```

---

## 📞 Support & Contributing

### Report Issues
Open an issue on GitHub with:
- Error message/logs
- Steps to reproduce
- Environment (OS, Python version, etc.)

### Contributing
1. Fork repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

### Code Guidelines
- Follow PEP 8 (Python)
- Use ESLint config (JavaScript)
- Add tests for new features
- Document API changes

---

## 📄 License

MIT License - See LICENSE.md

---

## 🎯 Roadmap

- [x] MVP - YouTube & TikTok support
- [x] Architecture & security design
- [ ] Phase 2 - Instagram, X, Facebook support
- [ ] Phase 3 - Pinterest, LinkedIn support
- [ ] Phase 4 - Advanced features (batch downloads, scheduling)
- [ ] Phase 5 - Mobile app (React Native)

---

## 📧 Contact

**Maintainer**: Senior Full-Stack Developer
**Email**: your-email@example.com
**Documentation**: https://docs.yourdomain.com

---

## Changed on: 2024
## Version: 0.1.0 (MVP)
