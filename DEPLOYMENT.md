# 🚀 Deployment Guide: Docker Backend + Vercel Frontend

## 📋 Overview
This guide shows how to deploy your Enterprise AI Dashboard with:
- **Backend**: FastAPI on Render (Free Tier) using Docker
- **Frontend**: React/Vite on Vercel (Free Tier)

## 🔧 Configuration Files Created

### 1. Dockerfile (Optimized for Render)
- Uses Python 3.11-slim base image
- Supports Render's PORT environment variable
- Includes health checks
- Optimized for free-tier constraints

### 2. render.yaml (Render Configuration)
- Free-tier optimized settings
- Auto-deployment from Git
- Health check configuration
- Environment variables setup

### 3. vercel.json (Vercel Configuration)
- API proxy to Render backend
- Build optimization
- Environment variable handling
- Regional deployment settings

### 4. .env.production (Environment Template)
- Production environment variables
- API key placeholders
- CORS configuration

## 🚀 Deployment Steps

### Step 1: Deploy Backend to Render
1. Push your code to GitHub/GitLab
2. Sign up at [render.com](https://render.com)
3. Click "New" → "Web Service"
4. Connect your Git repository
5. Render will automatically detect `render.yaml`
6. Deploy with free tier

### Step 2: Deploy Frontend to Vercel
1. Sign up at [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your Git repository
4. Vercel will detect `vercel.json`
5. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`
6. Deploy

### Step 3: Update Backend URL
After Render deployment:
1. Get your backend URL (e.g., `https://enterprise-ai-backend.onrender.com`)
2. Update `vercel.json` with the actual URL
3. Redeploy Vercel frontend

## 🔄 Free Tier Limitations

### Render (Backend)
- **RAM**: 512MB
- **CPU**: Shared
- **Sleep**: Apps sleep after 15min idle
- **Bandwidth**: 100GB/month
- **Build time**: 15min limit

### Vercel (Frontend)
- **Bandwidth**: 100GB/month
- **Build time**: 45s limit
- **Function execution**: 10s limit
- **Serverless**: 100k invocations/month

## 🛠️ Optimization Tips

### Backend Optimizations
- Lightweight dependencies (already configured)
- Efficient data structures
- Response caching
- Minimal logging

### Frontend Optimizations
- Code splitting (Vite handles this)
- Image optimization
- Lazy loading
- Bundle size monitoring

## 🔍 Testing

### Local Testing
```bash
# Build frontend
npm run build

# Test backend locally
python main.py

# Test with Docker (if Docker Desktop available)
docker build -t enterprise-ai-backend .
docker run -p 8000:8000 enterprise-ai-backend
```

### Production Testing
1. Check backend health: `https://your-backend.onrender.com/health`
2. Test API endpoints: `https://your-backend.onrender.com/docs`
3. Verify frontend: `https://your-frontend.vercel.app`
4. Test API integration through frontend

## 📁 Important Files

```
├── Dockerfile              # Backend container config
├── render.yaml            # Render deployment config
├── vercel.json            # Vercel deployment config
├── .env.production        # Production env template
├── main.py               # FastAPI backend
├── src/app/lib/api.ts    # Frontend API client
└── package.json          # Frontend dependencies
```

## 🎯 Next Steps

1. **Deploy Backend**: Push to Git → Render deployment
2. **Get Backend URL**: Copy from Render dashboard
3. **Update Vercel Config**: Edit vercel.json with actual URL
4. **Deploy Frontend**: Vercel deployment
5. **Test Integration**: Verify full stack functionality

## 💡 Pro Tips

- Use GitHub Actions for automated deployments
- Monitor free tier usage to avoid surprises
- Implement error handling for cold starts
- Consider CDN for static assets
- Set up uptime monitoring for backend

## 🆘 Troubleshooting

### Backend Issues
- Check Render logs for deployment errors
- Verify health endpoint is working
- Ensure PORT environment variable usage

### Frontend Issues
- Check Vercel build logs
- Verify API URL environment variable
- Test CORS configuration

### Integration Issues
- Verify API proxy configuration
- Check network requests in browser
- Test individual endpoints directly

Your deployment is now configured and ready for production! 🎉
