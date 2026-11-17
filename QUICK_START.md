# Cohortiva - Quick Start Guide

## For Local Development

### Backend
```bash
cd app/backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python manage.py runserver
```
Access at: http://localhost:8000/api/

### Frontend
```bash
cd app/frontend
npm start
```
Access at: http://localhost:3000

### Create Test Users
```bash
cd app/backend
source venv/bin/activate
python manage.py shell
```

Then in Python shell:
```python
from django.contrib.auth.models import User
from Users.models import Profile, Role

# Create learner
learner_user = User.objects.create_user(username='learner1', password='test123', email='learner@test.com', first_name='John', last_name='Learner')
student_role = Role.objects.get(name='Student')
Profile.objects.create(user=learner_user, role=student_role, student_id='2021001')

# Create coach
coach_user = User.objects.create_user(username='coach1', password='test123', email='coach@test.com', first_name='Jane', last_name='Coach')
tutor_role = Role.objects.get(name='Tutor')
Profile.objects.create(user=coach_user, role=tutor_role)

# Create admin
admin_user = User.objects.create_superuser(username='admin', password='admin123', email='admin@test.com')
admin_role = Role.objects.get(name='Admin')
Profile.objects.create(user=admin_user, role=admin_role)
```

## For Production Deployment

### Required Services
1. **Neon PostgreSQL**: https://console.neon.tech
2. **Render**: https://dashboard.render.com
3. **Vercel**: https://vercel.com/dashboard

### Environment Variables Needed

**Backend (Render):**
```env
SECRET_KEY=<generate-random-string>
DEBUG=False
DATABASE_URL=postgresql://...
ALLOWED_HOSTS=your-backend.onrender.com,your-frontend.vercel.app
FRONTEND_URL=https://your-frontend.vercel.app
```

**Frontend (Vercel):**
```env
REACT_APP_API_URL=https://your-backend.onrender.com/api/
```

### Deployment Steps Summary

1. **Database**: Create Neon project, get connection string
2. **Backend**: Deploy to Render with environment variables
3. **Frontend**: Deploy to Vercel with API URL
4. **Update**: Set CORS in backend to allow frontend domain
5. **Test**: Complete end-to-end workflow

See [PRE_DEPLOYMENT_CHECKLIST.md](./PRE_DEPLOYMENT_CHECKLIST.md) for detailed steps.

## Common Commands

### Backend Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations  # Check status
```

### Load Fixtures
```bash
python load_fixtures.py
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Frontend Build
```bash
npm run build
```

### Git Workflow
```bash
git add -A
git commit -m "feat: description"
git push origin main
```

## Test Credentials (Development Only)

After loading fixtures and creating test users:

| Role | Username | Password |
|------|----------|----------|
| Learner | learner1 | test123 |
| Coach | coach1 | test123 |
| Admin | admin | admin123 |

## Key URLs

### Local Development
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/
- Admin Panel: http://localhost:8000/admin/

### Production (Update after deployment)
- Frontend: https://your-app.vercel.app
- Backend API: https://your-api.onrender.com/api/
- Admin Panel: https://your-api.onrender.com/admin/

## Troubleshooting

### Backend won't start
- Check virtual environment is activated
- Verify `.env` file exists with correct settings
- Run `pip install -r requirements.txt`
- Check migrations: `python manage.py migrate`

### Frontend won't start
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Check `.env` file has `REACT_APP_API_URL`
- Clear browser cache and localStorage

### CORS errors
- Verify `FRONTEND_URL` in backend `.env`
- Check `ALLOWED_HOSTS` includes frontend domain
- Restart backend after changing `.env`

### Database errors
- Check `DATABASE_URL` format
- Verify database connection (try connecting with psql or DBeaver)
- Run migrations: `python manage.py migrate`
- Check Neon database isn't paused

### 401 Unauthorized errors
- Check JWT tokens in localStorage (F12 → Application → Local Storage)
- Try logging out and logging in again
- Verify `SECRET_KEY` hasn't changed (invalidates all tokens)

## Project Structure Quick Reference

```
Cohortiva/
├── app/
│   ├── backend/              # Django REST API
│   │   ├── Backend/          # Settings & URLs
│   │   ├── Users/            # User, Profile, Role
│   │   ├── Tutoring/         # Coach, Learner, Session
│   │   ├── Feedback/         # Ratings & Comments
│   │   ├── .env              # Environment variables (don't commit!)
│   │   ├── manage.py         # Django management
│   │   ├── requirements.txt  # Python dependencies
│   │   └── build.sh          # Render build script
│   │
│   └── frontend/             # React SPA
│       ├── src/
│       │   ├── components/   # Reusable UI components
│       │   ├── pages/        # Page components
│       │   ├── services/     # API communication
│       │   └── config/       # Configuration
│       ├── .env              # Local development (don't commit!)
│       ├── .env.production   # Production config
│       └── package.json      # Node dependencies
│
├── README.md                 # Main documentation
├── ARCHITECTURE.md           # Technical deep dive
├── DEPLOYMENT_GUIDE.md       # Detailed deployment steps
├── PRE_DEPLOYMENT_CHECKLIST.md  # Pre-deploy checklist
└── QUICK_START.md            # This file
```

## API Endpoints Quick Reference

### Authentication
- `POST /api/token/` - Login (get JWT tokens)
- `POST /api/token/refresh/` - Refresh access token
- `POST /api/users/register/student/` - Register new learner

### Users
- `GET /api/users/profiles/me/` - Get current user profile
- `GET /api/users/faculties/` - List faculties
- `GET /api/users/majors/` - List majors
- `GET /api/users/roles/` - List roles

### Coaching
- `GET /api/tutoring/tutors/` - List all coaches
- `GET /api/tutoring/tutors/me/` - Get my coach profile
- `PATCH /api/tutoring/tutors/me/` - Update availability
- `GET /api/tutoring/sessions/` - List sessions (role-filtered)
- `POST /api/tutoring/sessions/` - Book new session
- `PATCH /api/tutoring/sessions/{id}/` - Update/cancel session
- `DELETE /api/tutoring/sessions/{id}/` - Delete session (admin)

### Feedback
- `GET /api/feedback/feedback/` - List feedback
- `POST /api/feedback/feedback/` - Submit feedback
- `PATCH /api/feedback/feedback/{id}/` - Update feedback

### Admin
- `GET /api/tutoring/reports/overview/` - Platform statistics

## For Your Technical Interview

### Key Talking Points

**Architecture:**
> "Cohortiva uses a three-tier architecture: React frontend on Vercel, Django REST backend on Render, and Neon PostgreSQL database. Communication is via RESTful APIs with JWT authentication."

**Security:**
> "I implemented JWT tokens for stateless authentication, Django ORM to prevent SQL injection, React's auto-escaping for XSS protection, HTTPS enforcement, and strict CORS policies."

**Database Design:**
> "The schema is normalized to 3NF with proper foreign key relationships. User has one Profile, Profile can be Learner or Coach (one-to-one), and Sessions link Coaches to Learners with many-to-one relationships."

**Scalability:**
> "The architecture is stateless and horizontally scalable. To scale, I'd add read replicas, implement Redis caching, use Celery for async tasks, and deploy multiple backend instances behind a load balancer."

### Demo Workflow
1. Show registration → login → JWT storage
2. Coach sets availability (JSON field in database)
3. Learner books session (RBAC ensures only learners can book)
4. Session appears in both dashboards (filtered by role)
5. After completion, learner submits feedback

### Technical Depth Questions
- **N+1 queries?** "I use select_related() to join tables in single query"
- **Token refresh?** "Axios interceptor automatically refreshes on 401"
- **Role-based access?** "Queryset filtering + permission checks in views"
- **Database indexes?** "Foreign keys + composite indexes on frequently-queried fields"

## Getting Help

- Check documentation: README.md, ARCHITECTURE.md, DEPLOYMENT_GUIDE.md
- Review test report: `.agents/tasks/rebrand-test/test-report.md`
- Django docs: https://docs.djangoproject.com/
- React docs: https://react.dev/
- DRF docs: https://www.django-rest-framework.org/

## What's Next?

After deployment:
1. ✅ Monitor logs for first 24-48 hours
2. ✅ Set up UptimeRobot for backend pinging
3. ✅ Enable Vercel Analytics
4. ✅ Gather user feedback
5. ✅ Plan feature enhancements (notifications, calendar integration)
6. ✅ Consider custom domain
7. ✅ Add error tracking (Sentry)
8. ✅ Set up automated backups

---

**You're ready to deploy! Follow PRE_DEPLOYMENT_CHECKLIST.md for step-by-step instructions.**

Good luck! 🚀
