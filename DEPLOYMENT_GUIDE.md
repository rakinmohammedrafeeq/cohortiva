# Cohortiva Deployment Guide

This guide covers deploying Cohortiva to production: Backend on Render, Frontend on Vercel, Database on Neon PostgreSQL.

## Prerequisites

1. **Neon PostgreSQL Account**: [neon.tech](https://neon.tech)
2. **Render Account**: [render.com](https://render.com)
3. **Vercel Account**: [vercel.com](https://vercel.com)
4. **GitHub Repository**: Your code must be in a GitHub repository

## Phase 1: Database Setup (Neon PostgreSQL)

### Step 1: Create Neon Project
1. Go to https://console.neon.tech
2. Click "New Project"
3. Name: `cohortiva-db`
4. Region: Choose closest to your backend deployment
5. PostgreSQL version: 15 or 16
6. Click "Create Project"

### Step 2: Get Database Connection String
1. In your Neon project dashboard, go to "Connection Details"
2. Copy the **connection string** (format: `postgresql://user:password@host/database?sslmode=require`)
3. Save this - you'll need it for Render configuration

Example format:
```
postgresql://cohortiva_user:AbCd1234XyZ@ep-example-123456.us-east-2.aws.neon.tech/cohortiva?sslmode=require
```

## Phase 2: Backend Deployment (Render)

### Step 1: Create Web Service
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `cohortiva-backend`
   - **Region**: Same as Neon database if possible
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: `app/backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn Backend.wsgi:application --bind 0.0.0.0:$PORT --timeout 120`

### Step 2: Environment Variables
Add these in Render dashboard under "Environment":

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | (Generate a strong random string) | Use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | **CRITICAL**: Must be False in production |
| `DATABASE_URL` | (Your Neon connection string from Phase 1) | Paste the full PostgreSQL URL |
| `ALLOWED_HOSTS` | `cohortiva-backend.onrender.com,cohortiva-frontend.vercel.app` | Update with your actual domains |
| `FRONTEND_URL` | `https://cohortiva-frontend.vercel.app` | Update with your actual Vercel domain |
| `PYTHON_VERSION` | `3.11.0` | Or your preferred version |

### Step 3: Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Run `build.sh` (installs deps, collects static, runs migrations)
   - Start gunicorn server
3. Wait for deployment (usually 3-5 minutes)
4. Once live, note your backend URL: `https://cohortiva-backend.onrender.com`

### Step 4: Verify Backend
Test the health endpoint:
```bash
curl https://cohortiva-backend.onrender.com/api/
# Should return: {"status": "ok"}
```

## Phase 3: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend
Before deploying, update the API URL for production:

Create `app/frontend/.env.production`:
```env
REACT_APP_API_URL=https://cohortiva-backend.onrender.com/api/
```

Commit this file to your repository.

### Step 2: Deploy to Vercel
1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: `Create React App`
   - **Root Directory**: `app/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### Step 3: Environment Variables
Add in Vercel project settings:

| Key | Value |
|-----|-------|
| `REACT_APP_API_URL` | `https://cohortiva-backend.onrender.com/api/` |

### Step 4: Deploy
1. Click "Deploy"
2. Vercel will:
   - Install dependencies
   - Build React application
   - Deploy to CDN
3. Wait for deployment (usually 1-2 minutes)
4. Note your frontend URL: `https://cohortiva-frontend.vercel.app`

### Step 5: Update Backend CORS
Go back to Render and update these environment variables:
- `ALLOWED_HOSTS`: Add your Vercel domain
- `FRONTEND_URL`: Set to your Vercel URL

Redeploy the backend service in Render.

## Phase 4: Post-Deployment Verification

### 1. Test Backend Health
```bash
curl https://cohortiva-backend.onrender.com/api/
```
Expected: `{"status": "ok"}`

### 2. Test Frontend Access
1. Open `https://cohortiva-frontend.vercel.app` in browser
2. Should see Cohortiva login page
3. Check browser console for errors (F12)

### 3. Test Authentication
1. Register a new user as "Student" (Learner)
2. Login with credentials
3. Should redirect to dashboard
4. Verify JWT token stored in localStorage

### 4. Test API Integration
1. In dashboard, try to view available coaches (Availability section)
2. Try to book a session (Book Meeting section)
3. Check Network tab (F12) - all API calls should return 200/201

### 5. Test Database Persistence
1. Register a user
2. Log out
3. Log back in with same credentials
4. Should remember user and profile data

### 6. Test Different Roles
Create test users with different roles:
- **Learner**: Can book sessions, view coaches, submit feedback
- **Coach**: Can set availability, view scheduled sessions, receive feedback
- **Admin**: Can view reports, manage all users and sessions

## Phase 5: Production Data Setup

### Option A: Load Fixtures (Development/Demo)
SSH into Render or use Render Shell:
```bash
python manage.py shell
>>> from load_fixtures import main
>>> main()
```

### Option B: Admin Panel (Production)
1. Create superuser via Render Shell:
   ```bash
   python manage.py createsuperuser
   ```
2. Access admin: `https://cohortiva-backend.onrender.com/admin/`
3. Manually create roles, faculties, majors through admin interface

## Troubleshooting

### Issue: Backend 500 Error
**Check:**
- Render logs: Dashboard → Service → Logs
- `DATABASE_URL` is correctly formatted
- Migrations ran successfully during build
- `DEBUG=False` and `ALLOWED_HOSTS` includes your domain

### Issue: Frontend Can't Connect to Backend
**Check:**
- `REACT_APP_API_URL` in Vercel environment variables
- CORS configuration in Django settings
- Backend `FRONTEND_URL` and `ALLOWED_HOSTS` include Vercel domain
- Network tab in browser (F12) shows correct API URL

### Issue: CORS Errors
**Check:**
- Backend `FRONTEND_URL` environment variable
- Vercel domain in `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS` includes Vercel URL with https://

### Issue: Static Files Not Loading
**Check:**
- `build.sh` ran `collectstatic`
- Whitenoise installed and configured
- `STATIC_ROOT` and `STATIC_URL` in settings.py

### Issue: Database Connection Errors
**Check:**
- Neon database is active (not paused)
- Connection string includes `?sslmode=require`
- Neon firewall allows Render IP addresses (usually allowed by default)

## Render Free Tier Notes

1. **Cold Starts**: Free tier services sleep after 15 minutes of inactivity
   - First request after sleep takes ~30 seconds
   - Solution: Use a service like UptimeRobot to ping every 10 minutes
   
2. **Build Minutes**: Limited to 500 minutes/month
   - Each deployment uses ~2-3 minutes
   - Optimize by caching dependencies

3. **Database**: Use Neon free tier (1GB storage, 0.5GB RAM)
   - Scales to paid tier when needed

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] Database credentials not in code
- [ ] HTTPS enforced (automatic on Render/Vercel)
- [ ] CORS configured correctly
- [ ] Admin panel accessible only to superusers
- [ ] Environment variables never committed to Git
- [ ] Regular database backups configured in Neon

## Monitoring

### Render Logs
- Real-time: Dashboard → Service → Logs
- Download last 7 days of logs

### Neon Monitoring
- Query performance: Neon Console → Monitoring
- Connection pools: Check active connections

### Vercel Analytics
- Enable in Vercel project settings
- Monitor page load times, errors

## Updating After Deployment

### Backend Updates
1. Push changes to GitHub
2. Render auto-deploys (if enabled) or manual deploy
3. Migrations run automatically via `build.sh`

### Frontend Updates
1. Push changes to GitHub
2. Vercel auto-deploys
3. Cache cleared automatically

### Database Schema Changes
1. Create migration locally: `python manage.py makemigrations`
2. Test locally with PostgreSQL
3. Commit migration files
4. Push to GitHub
5. Render runs migrations during deployment

## Cost Estimates (When Scaling)

| Service | Free Tier | Paid Start |
|---------|-----------|------------|
| Render Web Service | 750 hours/month | $7/month |
| Neon PostgreSQL | 0.5GB RAM, 3GB storage | $19/month |
| Vercel Frontend | 100GB bandwidth | $20/month |

Total: Free to start, ~$46/month when scaling.

## Next Steps After Deployment

1. ✅ Custom domain (optional)
2. ✅ Email notifications (SendGrid/Mailgun)
3. ✅ File uploads (Cloudinary for media)
4. ✅ Monitoring (Sentry for error tracking)
5. ✅ Backup automation
6. ✅ CI/CD pipeline improvements

---

**Need Help?**
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs
- Neon Docs: https://neon.tech/docs
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/
