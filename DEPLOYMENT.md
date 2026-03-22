# Cloud Deployment Guide

Step-by-step deployment for the AI Timetable Generation System MVP.

## Architecture Overview

```
┌─────────────┐     HTTPS      ┌────────────────┐     SQL       ┌──────────────┐
│   Frontend   │ ◄────────────► │    Backend     │ ◄────────────► │  PostgreSQL  │
│  (Vercel)    │   REST API     │  (Render)      │               │ (Supabase)   │
│  React+Vite  │                │  FastAPI       │               │              │
└─────────────┘                └────────────────┘               └──────────────┘
```

---

## 1. Database — Supabase (PostgreSQL)

### Setup
1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Name it `timetable-db`, set a strong DB password, choose a region
3. Once created, navigate to **Settings → Database → Connection string (URI)**
4. Copy the URI — it looks like:
   ```
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### Run Schema
5. Go to **SQL Editor** in Supabase dashboard
6. Paste the contents of `schema.sql`
7. Click **Run** — all tables, enums, indexes, and seed data will be created

> [!TIP]
> Alternatively, connect with `psql` locally:
> ```bash
> psql "your-connection-string" -f schema.sql
> ```

---

## 2. Backend — Render (FastAPI)

### Prepare
1. Push the `backend/` folder to a GitHub repository
2. Add a `Procfile` (or use Render's start command):
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Deploy
3. Go to [render.com](https://render.com) → **New Web Service**
4. Connect your GitHub repo, select the `backend/` root directory
5. Settings:
   | Setting | Value |
   |---|---|
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

6. Add **Environment Variables**:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Your Supabase connection string |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app` |

7. Click **Deploy** → wait for the build to complete
8. Note your backend URL: `https://your-backend.onrender.com`

### Verify
```bash
curl https://your-backend.onrender.com/api/health
# → {"status": "ok"}
```

---

## 3. Frontend — Vercel

### Prepare
1. Push the `frontend/` folder to a GitHub repository (same or separate)

### Deploy
2. Go to [vercel.com](https://vercel.com) → **Import Project** → select your repo
3. Set the **Root Directory** to `frontend/`
4. Add **Environment Variable**:
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | `https://your-backend.onrender.com` |

5. Click **Deploy** → Vercel auto-detects Vite and builds
6. Your frontend is live at `https://your-project.vercel.app`

### CORS Checklist
- ✅ `CORS_ORIGINS` on Render includes your Vercel URL
- ✅ `VITE_API_URL` on Vercel points to your Render URL
- ✅ No trailing slashes on either URL

---

## 4. Post-Deployment Verification

| Check | Command / Action |
|---|---|
| Health | `GET /api/health` → `{"status": "ok"}` |
| DB seed | `GET /api/academic-years` → 3 years |
| Add teacher | Use the Manage Data page |
| Add workload | Use the Teacher Workload page |
| Generate | Click "Generate Timetable" |

---

## Alternative Providers

| Component | Alternative | Notes |
|---|---|---|
| Database | [Neon](https://neon.tech) | Free tier, serverless PostgreSQL |
| Backend | [Railway](https://railway.app) | Easy Python deploys |
| Frontend | [Netlify](https://netlify.com) | Set `VITE_API_URL` in build env |
