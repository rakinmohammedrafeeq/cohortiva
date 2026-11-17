# Pre-Deployment Checklist - Cohortiva

Complete this checklist before deploying to production.

## ✅ Phase 1-3: Complete (Development & Testing)

- [x] Git repository initialized
- [x] Backend dependencies installed
- [x] Frontend dependencies installed
- [x] Database migrations run successfully
- [x] Fixture data loaded (roles, faculties, majors)
- [x] Backend health check verified (http://localhost:8000/api/)
- [x] Frontend builds without errors
- [x] User authentication flow tested
- [x] Role-based dashboards tested
- [x] Session booking workflow tested
- [x] Feedback system tested
- [x] UI rebranding completed (Tutor → Coach, Student → Learner)
- [x] Comprehensive documentation written
- [x] Test report generated

## 📝 Phase 4: Database Configuration (Neon PostgreSQL)

### Step 1: Create Neon Database
- [ ] Sign up at https://console.neon.tech
- [ ] Create new project: `cohortiva-db`
- [ ] Select region closest to Render deployment
- [ ] Note down connection string

**Connection String Format:**
```
postgresql://username:password@ep-xxxxx.region.aws.neon.tech/database?sslmode=require
```

### Step 2: Test Connection Locally (Optional but Recommended)
- [ ] Update `app/backend/.env`:
  ```env
  DATABASE_URL=postgresql://your_connection_string_here
  ```
- [ ] Run migrations: `python manage.py migrate`
- [ ] Load fixtures: `python load_fixtures.py`
- [ ] Verify data in Neon console
- [ ] Create test user and verify persistence

**IMPORTANT:** Do NOT commit the production DATABASE_URL to Git!

## 🚀 Phase 5: Backend Deployment (Render)

### Step 1: Prepare Repository
- [ ] Push all changes to GitHub:
  ```bash
  git add -A
  git commit -m "chore: Ready for production deployment"
  git push origin main
  ```

### Step 2: Create Render Web Service
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Web Service"
- [ ] Connect GitHub repository
- [ ] Configure service:
  - **Name:** `cohortiva-backend`
  - **Region:** (Same as Neon if possible)
  - **Branch:** `main`
  - **Root Directory:** `app/backend`
  - **Runtime:** Python 3
  - **Build Command:** `chmod +x build.sh && ./build.sh`
  - **Start Command:** `gunicorn Backend.wsgi:application --bind 0.0.0.0:$PORT --timeout 120`

### Step 3: Configure Environment Variables in Render
Add these in Render dashboard → Environment:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | `<generate-random-64-char-string>` | Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | **CRITICAL: Must be False!** |
| `DATABASE_URL` | `<neon-connection-string>` | From Phase 4 |
| `ALLOWED_HOSTS` | `cohortiva-backend.onrender.com` | Update after deployment |
| `FRONTEND_URL` | `http://localhost:3000` | Update after Vercel deployment |
| `PYTHON_VERSION` | `3.11.0` | Or your version |

### Step 4: Deploy Backend
- [ ] Click "Create Web Service"
- [ ] Wait for build (3-5 minutes)
- [ ] Check logs for errors
- [ ] Note your backend URL: `https://cohortiva-backend.onrender.com`

### Step 5: Verify Backend Deployment
- [ ] Test health endpoint:
  ```bash
  curl https://cohortiva-backend.onrender.com/api/
  # Should return: {"status": "ok"}
  ```
- [ ] Test another endpoint:
  ```bash
  curl https://cohortiva-backend.onrender.com/api/users/faculties/
  # Should return list of faculties
  ```
- [ ] Check Render logs for any errors

## 🌐 Phase 6: Frontend Deployment (Vercel)

### Step 1: Prepare Frontend Environment
- [ ] Create `app/frontend/.env.production`:
  ```env
  REACT_APP_API_URL=https://cohortiva-backend.onrender.com/api/
  ```
- [ ] Commit this file:
  ```bash
  git add app/frontend/.env.production
  git commit -m "feat: Add production environment configuration"
  git push origin main
  ```

### Step 2: Deploy to Vercel
- [ ] Go to https://vercel.com/dashboard
- [ ] Click "Add New..." → "Project"
- [ ] Import your GitHub repository
- [ ] Configure project:
  - **Framework Preset:** Create React App
  - **Root Directory:** `app/frontend`
  - **Build Command:** `npm run build`
  - **Output Directory:** `build`

### Step 3: Configure Environment Variables in Vercel
- [ ] In Vercel project settings → Environment Variables:
  
| Key | Value | Environment |
|-----|-------|-------------|
| `REACT_APP_API_URL` | `https://cohortiva-backend.onrender.com/api/` | Production |

### Step 4: Deploy Frontend
- [ ] Click "Deploy"
- [ ] Wait for deployment (1-2 minutes)
- [ ] Note your frontend URL: `https://cohortiva-frontend.vercel.app`

### Step 5: Update Backend CORS Settings
- [ ] Go back to Render → cohortiva-backend → Environment
- [ ] Update these variables:
  - `ALLOWED_HOSTS`: `cohortiva-backend.onrender.com,cohortiva-frontend.vercel.app`
  - `FRONTEND_URL`: `https://cohortiva-frontend.vercel.app`
- [ ] Redeploy backend service (Manual Deploy button)

## ✅ Phase 7: Production Verification

### Test 1: Health Check
- [ ] Visit: `https://cohortiva-backend.onrender.com/api/`
- [ ] Expected: `{"status": "ok"}`

### Test 2: Frontend Access
- [ ] Visit: `https://cohortiva-frontend.vercel.app`
- [ ] Should see Cohortiva login page
- [ ] Check browser console (F12) - no errors

### Test 3: User Registration
- [ ] Click "Register"
- [ ] Fill out form (use test email)
- [ ] Select faculty and major
- [ ] Submit registration
- [ ] Should succeed and redirect

### Test 4: User Login
- [ ] Login with registered credentials
- [ ] Should redirect to dashboard
- [ ] Verify JWT tokens in localStorage (F12 → Application → Local Storage)

### Test 5: API Integration
- [ ] Navigate to "Availability" section
- [ ] Check Network tab (F12) - should see API calls to Render backend
- [ ] All requests should return 200/201
- [ ] CORS headers should be present

### Test 6: Coach Workflow
- [ ] Create superuser via Render shell:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Login to admin panel: `https://cohortiva-backend.onrender.com/admin/`
- [ ] Change your test user's role to "Tutor"
- [ ] Logout and login again
- [ ] Verify Coach dashboard appears
- [ ] Test setting availability
- [ ] Verify availability saves to database

### Test 7: Booking Workflow
- [ ] Login as learner (student role)
- [ ] Navigate to "Book Session"
- [ ] Select a coach with availability
- [ ] Book a session
- [ ] Verify success message
- [ ] Check "Schedule" - session should appear

### Test 8: Database Persistence
- [ ] Perform action (book session, add feedback)
- [ ] Logout
- [ ] Login again
- [ ] Verify data persists

### Test 9: Different Browsers
- [ ] Test on Chrome
- [ ] Test on Firefox
- [ ] Test on Safari (if available)
- [ ] Test on mobile browser

### Test 10: Error Scenarios
- [ ] Try logging in with wrong password
- [ ] Try booking without selecting coach
- [ ] Try submitting feedback without rating
- [ ] Verify proper error messages

## 📊 Phase 8: Post-Deployment Tasks

### Monitoring Setup
- [ ] Set up UptimeRobot to ping backend every 10 minutes (prevents cold starts)
- [ ] Enable Vercel Analytics
- [ ] Check Render logs regularly for first few days

### Documentation Updates
- [ ] Update README.md with live URLs
- [ ] Document any deployment issues encountered
- [ ] Update ARCHITECTURE.md if architecture changed

### Security Review
- [ ] Verify `DEBUG=False` in production
- [ ] Verify no secrets in Git history
- [ ] Verify HTTPS enforced on all domains
- [ ] Verify CORS only allows your frontend domain
- [ ] Verify database uses SSL connection

### Performance Baseline
- [ ] Measure initial page load time
- [ ] Measure API response times
- [ ] Note database query counts
- [ ] Monitor backend memory usage

## 🎯 Success Criteria

All these must be TRUE before considering deployment complete:

- [ ] Backend responds at production URL
- [ ] Frontend loads at production URL
- [ ] User can register and login
- [ ] JWT authentication works end-to-end
- [ ] Session booking workflow functional
- [ ] Feedback submission works
- [ ] Database persists data correctly
- [ ] No console errors in production
- [ ] CORS configured correctly
- [ ] All environment variables set
- [ ] Documentation reflects production setup

## 🔧 Rollback Plan (If Something Goes Wrong)

### Frontend Issues
1. Revert last commit: `git revert HEAD`
2. Push to trigger re-deploy: `git push origin main`
3. Or use Vercel's "Instant Rollback" feature

### Backend Issues
1. Check Render logs for error details
2. Roll back to previous deployment in Render dashboard
3. Or fix and redeploy from GitHub

### Database Issues
1. Neon provides point-in-time recovery
2. Use Neon console → Restore to restore backup
3. Re-run migrations if needed

## 📞 Support Resources

- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **Neon Docs:** https://neon.tech/docs
- **Django Deployment:** https://docs.djangoproject.com/en/5.2/howto/deployment/
- **Render Community:** https://community.render.com/

## 🎉 Deployment Complete!

Once all checkboxes are complete, you have a fully functional, production-ready Cohortiva platform!

**Live URLs:**
- Frontend: `https://cohortiva-frontend.vercel.app`
- Backend API: `https://cohortiva-backend.onrender.com/api/`
- Admin Panel: `https://cohortiva-backend.onrender.com/admin/`

**Next Steps:**
- Monitor for first 24-48 hours
- Gather user feedback
- Plan feature enhancements
- Consider custom domain
- Set up analytics

---

**IMPORTANT REMINDERS:**
1. Never commit `.env` files with production secrets
2. Keep `DEBUG=False` in production
3. Use strong `SECRET_KEY`
4. Monitor logs regularly
5. Set up automated backups

**Good luck with your deployment! 🚀**
