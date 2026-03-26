# 🚀 LIVE DEPLOYMENT STEPS

## Step 1: Deploy Backend to Render (5 minutes)

### 1.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Sign up" (free)
3. Sign up with GitHub (recommended)

### 1.2 Create Web Service
1. Click "+ New" → "Web Service"
2. Connect your GitHub account
3. Select your repository: `AnandSaurabhShah/enterprise-ai-dashboard`
4. Click "Connect"

### 1.3 Configure Service
Render will auto-detect your settings:
- **Name**: `enterprise-ai-backend` (keep this)
- **Environment**: Docker (auto-detected)
- **Branch**: main
- **Root Directory**: `./` (keep default)
- **Plan**: Free (keep default)

### 1.4 Add Environment Variables
Scroll to "Environment Variables" and add:
```
PYTHON_VERSION = 3.11
PORT = 8000
ENVIRONMENT = production
```

### 1.5 Deploy
Click "Create Web Service" → Render will build and deploy!

## Step 2: Get Backend URL (2 minutes)

### 2.1 Wait for Deployment
- Build takes 2-5 minutes
- Watch the progress in Render dashboard
- You'll see "Live" when ready

### 2.2 Copy Your Backend URL
Your URL will be: `https://enterprise-ai-backend.onrender.com`
(Or similar if name is taken)

### 2.3 Test Backend
Visit: `https://your-backend-url.onrender.com/health`
Should return: `{"status":"healthy","timestamp":"..."}`

## Step 3: Deploy Frontend to Vercel (3 minutes)

### 3.1 Create Vercel Account
1. Go to [vercel.com](https://vercel.com)
2. Click "Sign up"
3. Sign up with GitHub (recommended)

### 3.2 Import Project
1. Click "New Project"
2. Select your repository: `AnandSaurabhShah/enterprise-ai-dashboard`
3. Click "Import"

### 3.3 Configure Vercel
Vercel will auto-detect your settings:
- **Framework**: Vite (auto-detected)
- **Root Directory**: `./` (keep default)
- **Build Command**: `npm run build` (auto-detected)
- **Output Directory**: `dist` (auto-detected)

### 3.4 Add Environment Variable
Scroll to "Environment Variables" and add:
```
VITE_API_URL = https://your-backend-url.onrender.com
```
(Replace with your actual backend URL from Step 2)

### 3.5 Deploy
Click "Deploy" → Vercel will build and deploy!

## Step 4: Test Full Deployment (2 minutes)

### 4.1 Wait for Frontend Build
- Build takes 1-2 minutes
- You'll see "Ready" when complete

### 4.2 Test Your Live App
Visit your Vercel URL: `https://your-app-name.vercel.app`

### 4.3 Verify API Integration
1. Open browser dev tools (F12)
2. Go to Network tab
3. Use the app - you should see API calls to your backend

## 🎯 SUCCESS! Your App is Live!

### What You Get:
- **Backend**: FastAPI on Render (free tier)
- **Frontend**: React/Vite on Vercel (free tier)
- **Database**: Ready for future integration
- **SSL**: Automatic HTTPS on both services
- **Auto-deployment**: Push to Git → auto-redeploy

### Your URLs:
- **Frontend**: `https://your-app-name.vercel.app`
- **Backend**: `https://your-backend.onrender.com`
- **API Docs**: `https://your-backend.onrender.com/docs`

## 🔄 Next Steps

### If You Need Changes:
1. Make code changes locally
2. Commit to Git: `git add . && git commit -m "Update" && git push`
3. Both services auto-redeploy

### Monitor Your Apps:
- **Render**: Dashboard shows logs and health
- **Vercel**: Dashboard shows builds and analytics

## 🆘 Troubleshooting

### Backend Issues:
- Check Render logs in dashboard
- Verify health endpoint works
- Make sure Dockerfile is correct

### Frontend Issues:
- Check Vercel build logs
- Verify API URL environment variable
- Check CORS configuration

### Integration Issues:
- Verify backend URL is correct
- Check API proxy in vercel.json
- Test endpoints directly

## 💡 Pro Tips

- Both services have generous free tiers
- Apps may "sleep" after inactivity (normal for free tier)
- First visit might be slower (cold start)
- Monitor usage to stay within free limits

---

## 🎉 START DEPLOYMENT NOW!

**Time Required**: 10-15 minutes total
**Cost**: $0 (free tiers)
**Difficulty**: Easy - just follow the steps!

Go to Step 1 and start with Render.com! 🚀
