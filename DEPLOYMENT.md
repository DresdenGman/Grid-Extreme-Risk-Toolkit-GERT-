# GERT Deployment Guide

## 🚀 Quick Start

### Option 1: Using Startup Script (Recommended)

```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Startup

#### 1. Start Backend Service

```bash
# Activate virtual environment
source .venv/bin/activate

# Start backend (port 8000 by default — set PORT env var to customise)
python main.py
```

Backend service will start at `http://localhost:8000`.

#### 2. Start Frontend Service

In a **new terminal window**:

```bash
# Install dependencies (first run only)
npm install

# Start frontend (port 3000)
npm run dev
```

Frontend service will start at `http://localhost:3000`.

---

## ✅ Verify Service Status

### Check Backend

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "ok",
  "timestamp": "...",
  "backend": "stub-v1",
  "env": "dev"
}
```

### Check Frontend

Open in browser: `http://localhost:3000`

You should see the GERT control room interface.

---

## 🔧 Troubleshooting

### 1. Backend Startup Failure

**Error**: `ModuleNotFoundError` or `ImportError`

**Solution**:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Initialization Failure

**Error**: `Database initialization failed`

**Solution**:
- SQLite (default): Ensure write permissions
- PostgreSQL: Check `DATABASE_URL` environment variable and database connection

### 3. Frontend Cannot Connect to Backend

**Error**: Frontend shows "Failed to fetch" or API errors

**Solution**:
1. Confirm backend is running at `http://localhost:8000`
2. Check `API_BASE` configuration in `lib/api.ts`
3. Confirm no CORS issues (development environment is configured to allow all origins)

### 4. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process
kill -9 <PID>
```

---

## 📊 Service Addresses

- **Frontend Interface**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health

---

## 🛑 Stop Services

### Option 1: Using Ctrl+C

Press `Ctrl+C` in the terminal running the service

### Option 2: Find and Kill Processes

```bash
# Find processes
ps aux | grep -E "(python.*main.py|next|npm)"

# Kill processes
pkill -f "python.*main.py"
pkill -f "next"
```

---

## 🔄 Restart Services

```bash
# Stop all services
pkill -f "python.*main.py"
pkill -f "next"

# Restart
./start.sh
```

---

## 📝 View Logs

### Backend Logs

Backend logs are output to console. If running in background:

```bash
tail -f /tmp/gert_backend.log
```

### Frontend Logs

Frontend logs are displayed in the terminal running `npm run dev`.

---

## 🎯 Production Deployment

### Backend (Using Gunicorn + Uvicorn)

```bash
pip install gunicorn
gunicorn api.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Build Static Files)

```bash
npm run build
npm start
```

Or use Nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 🔐 Environment Variables Configuration

Create `.env` file (optional):

```bash
# Database
DATABASE_URL=sqlite:///./gert.db  # or postgresql://user:pass@localhost/gert

# Alert System (optional)
ALERT_EMAIL_ENABLED=false
ALERT_WEBHOOK_ENABLED=false

```

---

## Deployment status

- **Hosted demo**: https://gert-d.vercel.app — historical lab and review surfaces.
- **Local development**: backend at `http://localhost:8000` and frontend at `http://localhost:3000`, after you start them with the steps above. Nothing runs until you start it.
- **Data**: ERCOT official API only (any fallback is returned as a clearly labeled `estimated_fallback`). The CAISO/PJM/NYISO adapters return clearly labeled estimates (`estimated_fallback`), not live feeds.
- **Model inference**: gated. The ERCOT v1.4 candidate failed its preregistered validation gate (see `docs/DECISION_RECORD_ERCOT_v1_4.md`), so prediction endpoints return HTTP 503 until a candidate passes. Demo mode (`?demo=1`) shows clearly labeled simulated data instead.
- **Database**: SQLite by default (auto-initialized); PostgreSQL via `DATABASE_URL`.
- **Alerts and persistence**: available when enabled through the environment variables above; both are off unless you configure them.

---

## After it is running

1. Open **http://localhost:3000** (or the hosted demo at https://gert-d.vercel.app).
2. Start with the **Historical Lab** — a deterministic replay of 216 recorded ERCOT hours that works without a model.
3. Use the **Review** surfaces to walk through the v1.4 validation evidence, including why the candidate was rejected.
4. Live Monitor, Scenario Lab, and Benchmarks depend on model inference and stay gated (HTTP 503) until a candidate passes the validation gate; add `?demo=1` to explore them with labeled simulated data.
