# Cohortiva - Professional Coaching Session & Feedback Management Platform

> A full-stack web application connecting learners with professional coaches through intelligent session scheduling, availability management, and comprehensive feedback systems.

[![Django](https://img.shields.io/badge/Django-5.2.7-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-19.0.0-blue.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-blue.svg)](https://neon.tech/)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Project Overview

Cohortiva is a modern coaching management platform designed to streamline the connection between learners and coaches. Built with enterprise-grade technologies and best practices, it demonstrates:

- **Full-stack development** with React and Django REST Framework
- **Secure authentication** using JWT tokens
- **Role-based access control** (Learner, Coach, Admin)
- **Real-time availability management** with JSON-based scheduling
- **RESTful API design** following industry standards
- **Production deployment** on Render (backend) and Vercel (frontend)

### Why Cohortiva?

This project showcases professional-level software engineering:
- Clean separation of concerns (frontend/backend)
- Database-driven architecture with proper relationships
- Secure authentication and authorization flows
- Responsive UI with modern React practices
- Production-ready deployment configuration
- Comprehensive testing and documentation

## ✨ Key Features

### For Learners
- 📝 **User Registration**: Create account with faculty and major selection
- 🔍 **Browse Coaches**: View available coaches with expertise and availability
- 📅 **Book Sessions**: Schedule coaching sessions with preferred coaches
- ❌ **Manage Bookings**: Cancel or reschedule sessions as needed
- ⭐ **Provide Feedback**: Rate and comment on completed sessions

### For Coaches
- 📆 **Availability Management**: Set weekly availability schedule
- 👥 **View Sessions**: Track upcoming, ongoing, and completed sessions
- 📊 **Receive Feedback**: View ratings and comments from learners
- ✏️ **Profile Management**: Update expertise, bio, and coaching information

### For Administrators
- 📈 **Analytics Dashboard**: View platform statistics and usage metrics
- 👁️ **Monitor Sessions**: Oversee all coaching sessions across the platform
- 📊 **Generate Reports**: Access comprehensive reports on sessions, feedback, and users
- 🔧 **Manage Data**: CRUD operations on faculties, majors, and roles

## 🛠 Technology Stack

### Frontend
- **React 19** - Latest React with improved performance
- **React Router v7** - Client-side routing
- **Axios** - HTTP client with interceptors for JWT
- **CSS3** - Modern styling with responsive design

### Backend
- **Django 5.2.7** - High-level Python web framework
- **Django REST Framework 3.16** - Powerful API toolkit
- **SimpleJWT 5.5** - JWT authentication for Django
- **django-filter** - Powerful filtering system
- **django-cors-headers** - CORS handling

### Database
- **SQLite** - Local development
- **Neon PostgreSQL** - Production database
- **psycopg 3** - PostgreSQL adapter

### Deployment & DevOps
- **Render** - Backend hosting
- **Vercel** - Frontend hosting
- **Gunicorn** - WSGI HTTP server
- **Whitenoise** - Static file serving
- **Git** - Version control

## 🏗 Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                          │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           React 19 Single Page Application           │   │
│  │                                                       │   │
│  │  - React Router (Client-side routing)               │   │
│  │  - Axios (API communication with JWT interceptors)   │   │
│  │  - Local Storage (Token persistence)                 │   │
│  │  - Responsive UI Components                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │ HTTPS / JSON
                            │ JWT Bearer Token
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                      APPLICATION TIER                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │         Django REST Framework API Server              │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │          Authentication Layer                 │   │    │
│  │  │  - SimpleJWT (Access & Refresh Tokens)       │   │    │
│  │  │  - Token Validation & Renewal                │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │           Authorization Layer                 │   │    │
│  │  │  - Role-Based Access Control (RBAC)          │   │    │
│  │  │  - Permission Checks                          │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                        │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │             Business Logic                    │   │    │
│  │  │                                                │   │    │
│  │  │  ┌──────────────────────────────────────┐   │   │    │
│  │  │  │        Users App                      │   │   │    │
│  │  │  │  - Profile Management                 │   │   │    │
│  │  │  │  - Faculty & Major Lookup             │   │   │    │
│  │  │  │  - Role Assignment                    │   │   │    │
│  │  │  └──────────────────────────────────────┘   │   │    │
│  │  │                                                │   │    │
│  │  │  ┌──────────────────────────────────────┐   │   │    │
│  │  │  │      Tutoring (Coaching) App          │   │   │    │
│  │  │  │  - Coach/Learner Profiles             │   │   │    │
│  │  │  │  - Availability Management            │   │   │    │
│  │  │  │  - Session CRUD                       │   │   │    │
│  │  │  │  - Auto Status Updates                │   │   │    │
│  │  │  └──────────────────────────────────────┘   │   │    │
│  │  │                                                │   │    │
│  │  │  ┌──────────────────────────────────────┐   │   │    │
│  │  │  │         Feedback App                  │   │   │    │
│  │  │  │  - Session Ratings                    │   │   │    │
│  │  │  │  - Comments & Reviews                 │   │   │    │
│  │  │  └──────────────────────────────────────┘   │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              │ ORM (Django Models)
                              │ SQL Queries
                              │
┌─────────────────────────────▼─────────────────────────────────┐
│                         DATA TIER                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐    │
│  │         Neon PostgreSQL Database                      │    │
│  │                                                        │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │    │
│  │  │   Users    │  │  Tutoring  │  │  Feedback  │     │    │
│  │  │            │  │            │  │            │     │    │
│  │  │ - User     │  │ - Tutor    │  │ - Feedback │     │    │
│  │  │ - Profile  │  │ - Student  │  │ - Rating   │     │    │
│  │  │ - Faculty  │  │ - Session  │  │ - Comment  │     │    │
│  │  │ - Major    │  │ - Registr. │  │            │     │    │
│  │  │ - Role     │  │            │  │            │     │    │
│  │  └────────────┘  └────────────┘  └────────────┘     │    │
│  │                                                        │    │
│  │  Foreign Keys & Relationships:                        │    │
│  │  - User ←→ Profile (One-to-One)                     │    │
│  │  - Profile ←→ Tutor/Student (One-to-One)           │    │
│  │  - Session → Tutor, Student (Many-to-One)           │    │
│  │  - Feedback → Session, User (Many-to-One)           │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

### Request Flow Example: Booking a Session

```
1. Learner clicks "Book Session" button in frontend
   └─> React component calls bookSession() in authService.js

2. Axios intercepts request and adds JWT token
   └─> Authorization: Bearer <access_token>

3. Request sent to Django API
   └─> POST /api/tutoring/sessions/
       Body: { tutor: 5, start_time: "2025-01-20T10:00:00Z", ... }

4. Django middleware processes request
   ├─> CORS middleware validates origin
   ├─> Authentication middleware validates JWT
   └─> Extracts user from token payload

5. View layer (SessionViewSet.perform_create)
   ├─> Checks user role == "student"
   ├─> Gets or creates Student record for user
   └─> Validates tutor availability

6. Database layer
   ├─> INSERT INTO Tutoring_session (...)
   └─> Returns session ID

7. Serializer formats response
   └─> Returns JSON: { id: 42, tutor: {...}, start_time: "...", ...}

8. Response travels back through middleware
   └─> CORS headers added
   └─> JSON response with 201 Created

9. Axios receives response in frontend
   └─> Updates UI state
   └─> Shows success message
   └─> Refreshes session list
```

### Database Schema

```sql
-- Users App
User (Django built-in)
  ├─ id, username, email, password, first_name, last_name

Profile
  ├─ id, user_id (FK → User)
  ├─ role_id (FK → Role)
  ├─ faculty_id (FK → Faculty)
  ├─ major_id (FK → Major)
  └─ student_id, created_at

Role
  └─ id, name (Student, Tutor, Admin)

Faculty
  └─ id, code, name

Major
  └─ id, faculty_id (FK → Faculty), name

-- Tutoring App
Tutor
  ├─ id, profile_id (FK → Profile)
  ├─ expertise, bio
  └─ availability (JSON)

Student
  ├─ id, profile_id (FK → Profile)
  ├─ study_year
  └─ support_need

Session
  ├─ id
  ├─ tutor_id (FK → Tutor)
  ├─ student_id (FK → Student)
  ├─ start_time, end_time
  ├─ location, mode (online/offline)
  └─ status (scheduled/ongoing/completed/cancelled)

Registration
  ├─ id
  ├─ student_id (FK → Student)
  ├─ tutor_id (FK → Tutor)
  ├─ status (pending/approved/rejected)
  └─ created_at

-- Feedback App
Feedback
  ├─ id
  ├─ session_id (FK → Session)
  ├─ from_user_id (FK → User)
  ├─ rating (1-5)
  ├─ comment
  └─ created_at
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 16+** and npm
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cohortiva.git
cd cohortiva/app
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set SECRET_KEY

# Run migrations
python manage.py migrate

# Load initial data (roles, faculties, majors)
python load_fixtures.py

# Create superuser (optional, for admin panel)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Backend will run at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Verify REACT_APP_API_URL=http://localhost:8000/api/

# Start development server
npm start
```

Frontend will open at `http://localhost:3000`

### 4. Test the Application

1. Open browser to `http://localhost:3000`
2. Click "Register" and create a Student (Learner) account
3. Login with your credentials
4. Explore the dashboard

**To test Coach features:**
1. Go to admin panel: `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Navigate to Users → Profiles
4. Change your user's role to "Tutor" (Coach)
5. Logout and login again
6. You'll now see Coach dashboard with availability management

## 📦 Deployment

See detailed deployment guide: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

### Quick Deploy Commands

**Backend (Render):**
```bash
# Ensure build.sh is executable
chmod +x backend/build.sh

# Render will automatically:
# 1. Run: ./build.sh
# 2. Collect static files
# 3. Run migrations
# 4. Start: gunicorn Backend.wsgi:application
```

**Frontend (Vercel):**
```bash
# Vercel will automatically:
# 1. npm install
# 2. npm run build
# 3. Deploy to CDN
```

## 📚 API Documentation

### Authentication Endpoints

#### POST `/api/token/`
Obtain JWT access and refresh tokens.

**Request:**
```json
{
  "username": "learner1",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### POST `/api/token/refresh/`
Refresh expired access token.

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### User Endpoints

#### GET `/api/users/profiles/me/`
Get current user's profile (requires authentication).

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 5,
    "username": "learner1",
    "email": "learner1@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "role": 1,
  "faculty": 5,
  "major": 24,
  "student_id": "2021001234"
}
```

#### GET `/api/users/faculties/`
List all faculties (public endpoint).

#### GET `/api/users/majors/?faculty=5`
List majors, optionally filtered by faculty.

### Session Endpoints

#### GET `/api/tutoring/sessions/`
List sessions (filtered by user role).

**Query Parameters:**
- `status`: Filter by status (scheduled, completed, cancelled)
- `tutor`: Filter by tutor ID
- `student`: Filter by student ID

**Response:**
```json
[
  {
    "id": 42,
    "tutor": {
      "id": 3,
      "profile": {
        "user": {
          "first_name": "Jane",
          "last_name": "Coach"
        }
      },
      "expertise": "Data Science"
    },
    "student": {
      "id": 7,
      "profile": {
        "user": {
          "first_name": "John",
          "last_name": "Learner"
        }
      }
    },
    "start_time": "2025-01-20T10:00:00Z",
    "end_time": "2025-01-20T11:00:00Z",
    "location": "Zoom Meeting",
    "mode": "online",
    "status": "scheduled"
  }
]
```

#### POST `/api/tutoring/sessions/`
Book a new session (Learner/Student role required).

**Request:**
```json
{
  "tutor": 3,
  "start_time": "2025-01-20T10:00:00Z",
  "end_time": "2025-01-20T11:00:00Z",
  "location": "Zoom: https://zoom.us/j/123456",
  "mode": "online"
}
```

#### PATCH `/api/tutoring/sessions/{id}/`
Update session (cancel, reschedule).

**Request (Cancel):**
```json
{
  "status": "cancelled"
}
```

#### GET `/api/tutoring/tutors/me/`
Get logged-in coach's profile (Coach role required).

#### PATCH `/api/tutoring/tutors/me/`
Update coach availability (Coach role required).

**Request:**
```json
{
  "availability": {
    "monday": ["08:00-10:00", "14:00-16:00"],
    "wednesday": ["09:00-11:00"],
    "friday": ["13:30-15:00"]
  },
  "expertise": "Machine Learning, Python, Data Analysis",
  "bio": "Experienced data scientist with 5 years in ML"
}
```

### Feedback Endpoints

#### POST `/api/feedback/feedback/`
Submit feedback for a completed session.

**Request:**
```json
{
  "session": 42,
  "rating": 5,
  "comment": "Excellent coaching session! Very helpful explanations."
}
```

### Admin Endpoints

#### GET `/api/tutoring/reports/overview/`
Get platform statistics (Admin role required).

**Response:**
```json
{
  "total_students": 156,
  "total_tutors": 23,
  "total_sessions": 487,
  "sessions_by_status": {
    "completed": 320,
    "scheduled": 45,
    "cancelled": 122
  },
  "sessions_by_mode": {
    "online": 380,
    "offline": 107
  },
  "total_feedback": 298,
  "average_rating": 4.6
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing Checklist
- [ ] User registration (all roles)
- [ ] Login/logout flow
- [ ] JWT token refresh
- [ ] Role-based dashboard access
- [ ] Coach availability management
- [ ] Session booking (Learner)
- [ ] Session cancellation
- [ ] Feedback submission
- [ ] Admin reports view
- [ ] Responsive design (mobile/tablet/desktop)

## 🤝 Contributing

This project follows industry-standard contribution guidelines:

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'feat: Add amazing feature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

### Commit Message Convention
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎤 Presenting This Project

### For Technical Interviews

**Elevator Pitch:**
> "Cohortiva is a full-stack coaching management platform I built using React and Django REST Framework. It demonstrates enterprise-level architecture with JWT authentication, role-based access control, and real-time availability management. The system handles complex workflows like session booking with validation, automated status updates, and comprehensive feedback collection. I deployed it to production using Render for the backend, Vercel for the frontend, and Neon PostgreSQL for the database."

**Technical Highlights to Mention:**
1. **Architecture**: Clean separation between React frontend and Django REST backend
2. **Security**: JWT-based authentication with automatic token refresh
3. **Database Design**: Normalized schema with proper foreign key relationships
4. **API Design**: RESTful endpoints with filtering, pagination, and role-based permissions
5. **State Management**: Efficient React state management with hooks and context
6. **Deployment**: Production-ready with environment-based configuration
7. **Code Quality**: Follows PEP 8, uses Django ORM efficiently, implements DRY principles

**Questions You Might Get:**
- "How does the JWT refresh mechanism work?" → Explain the Axios interceptor pattern
- "How did you handle CORS?" → django-cors-headers with environment-specific origins
- "What if two learners book the same time slot?" → Explain database constraints and transaction handling
- "How do you prevent SQL injection?" → Django ORM with parameterized queries
- "How would you scale this?" → Caching, database indexing, load balancing, CDN for static files

## 📞 Contact & Links

- **GitHub**: [github.com/yourusername/cohortiva](https://github.com/yourusername/cohortiva)
- **Live Demo**: [cohortiva-frontend.vercel.app](https://cohortiva-frontend.vercel.app)
- **API Docs**: [cohortiva-backend.onrender.com/api/](https://cohortiva-backend.onrender.com/api/)

---

**Built with ❤️ by [Your Name]**

*Cohortiva - Empowering learners and coaches through intelligent session management.*
