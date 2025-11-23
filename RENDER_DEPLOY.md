# Python RAG API - Deployment Guide

## Deploy to Render

### Prerequisites
- GitHub account
- Render account (free tier available)

### Files Required
✅ `requirements.txt` - Python dependencies
✅ `Procfile` - Render start command
✅ `runtime.txt` - Python version
✅ `app/personalize_api.py` - Main API
✅ `app/search_api.py` - Search utilities
✅ `data/` - CSV and JSON data files

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy Python API"
   git push origin phong
   ```

2. **Create Render Web Service**
   - Go to https://render.com/dashboard
   - Click "New" → "Web Service"
   - Connect GitHub repository
   - Select `ttvKieran/Naver-TMW`

3. **Configure Service**
   - **Name**: `naver-tmw-api`
   - **Region**: Singapore
   - **Branch**: `phong`
   - **Root Directory**: `clova-rag-roadmap`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.personalize_api:app --host 0.0.0.0 --port $PORT`

4. **Select Plan**
   - Free: 750 hours/month, sleeps after 15min inactivity
   - Starter ($7/mo): Always on, faster

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first build
   - URL: `https://naver-tmw-api.onrender.com`

### Testing

Test the API at: `https://your-app.onrender.com/docs`

You should see FastAPI Swagger UI with endpoints:
- POST `/roadmap/personalized`
- GET `/health` (if exists)

### Troubleshooting

**Build Failed?**
- Check `requirements.txt` format
- Check Python version in `runtime.txt`
- View build logs in Render dashboard

**Cold Start Slow?**
- Free tier sleeps after 15min
- First request takes 30-60s to wake up
- Upgrade to Starter plan to avoid sleep

**Import Errors?**
- Make sure all dependencies are in `requirements.txt`
- Check data files are committed to Git

### Monitoring

View logs in Render dashboard:
- Real-time logs
- Past 7 days of logs
- Filter by severity

### Update Deployment

When you update code:
```bash
git add .
git commit -m "Update API"
git push origin phong
```

Render will auto-deploy on push (if enabled).

### Environment Variables

If needed, add in Render dashboard:
- Settings → Environment
- Add key-value pairs
- Redeploy to apply changes
