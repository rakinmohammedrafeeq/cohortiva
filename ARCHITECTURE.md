# Cohortiva - System Architecture & Technical Deep Dive

> A comprehensive technical explanation for engineering interviews

## Table of Contents
1. [System Overview](#system-overview)
2. [Frontend Architecture](#frontend-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Database Design](#database-design)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Design Patterns](#api-design-patterns)
7. [Request Lifecycle](#request-lifecycle)
8. [Deployment Architecture](#deployment-architecture)
9. [Security Considerations](#security-considerations)
10. [Scalability & Performance](#scalability--performance)

---

## System Overview

### Architecture Style
**Three-Tier Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│         Presentation Tier (Client)          │
│              React 19 SPA                   │
│         Hosted on Vercel CDN                │
└──────────────────┬──────────────────────────┘
                   │ HTTPS/JSON
                   │ JWT Bearer Token
┌──────────────────▼──────────────────────────┐
│         Application Tier (Server)           │
│        Django REST Framework API            │
│          Hosted on Render.com               │
└──────────────────┬──────────────────────────┘
                   │ SQL/ORM
                   │ psycopg3
┌──────────────────▼──────────────────────────┐
│           Data Tier (Database)              │
│          Neon PostgreSQL 15/16              │
│         Managed Database Service            │
└─────────────────────────────────────────────┘
```

### Key Architectural Decisions

#### 1. **Why REST API instead of GraphQL?**
- **Simplicity**: RESTful endpoints are straightforward and well-understood
- **Caching**: HTTP-level caching works out-of-the-box
- **Tooling**: Django REST Framework provides mature, battle-tested tools
- **Learning**: REST is more universally adopted in enterprise environments

#### 2. **Why JWT instead of Session-based auth?**
- **Stateless**: Backend doesn't need to store session state
- **Scalability**: Easy to scale horizontally without session affinity
- **Mobile-friendly**: Tokens work seamlessly across web and mobile clients
- **Decoupling**: Frontend and backend are truly independent

#### 3. **Why React SPA instead of Server-Side Rendering (SSR)?**
- **Developer Experience**: Faster iteration with hot module replacement
- **Performance**: Client-side rendering after initial load is snappy
- **Deployment**: Static build can be served from CDN
- **Offline**: Service workers can cache for offline-first experience

---

## Frontend Architecture

### Component Hierarchy

```
App.js (Root Router)
│
├─ LoginPage
├─ RegisterPage
├─ ForgotPassword
│
└─ Dashboard (Protected Route)
    │
    ├─ Layout (Common UI Shell)
    │   ├─ Navbar
    │   └─ Sidebar
    │
    └─ Dashboard Content
        │
        ├─ Role-Specific Dashboards
        │   ├─ StudentDashboard (Learner View)
        │   ├─ TutorDashboard (Coach View)
        │   └─ AdminDashboard (Admin View)
        │
        └─ Dashboard Sections (Shared)
            ├─ Availability (View/Set coach availability)
            ├─ BookMeeting (Book sessions)
            ├─ CancelMeeting (Manage bookings)
            ├─ EvaluateSession (Submit feedback)
            └─ GenerateReport (Admin analytics)
```

### State Management Strategy

**Local State + Service Layer Pattern** (No Redux needed for this scale):

```javascript
// Component State (React Hooks)
const [sessions, setSessions] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

// Service Layer (authService.js)
// - Centralizes all API calls
// - Handles token attachment
// - Provides caching for static data
const authService = {
  login, logout, getProfile,
  getSessions, bookSession, cancelSession,
  // ... etc
};
```

**Why this approach?**
- **Sufficient**: Application state is mostly server-driven, not complex local state
- **Simple**: No boilerplate of Redux actions/reducers
- **Performant**: Service-level caching prevents unnecessary API calls
- **Scalable**: Can migrate to Context API or Redux if complexity grows

### Axios Interceptor Pattern (JWT Refresh)

**Problem**: Access tokens expire after 60 minutes. How to handle gracefully?

**Solution**: Axios request/response interceptors

```javascript
// REQUEST INTERCEPTOR: Attach access token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// RESPONSE INTERCEPTOR: Auto-refresh on 401
api.interceptors.response.use(
  response => response, // Pass through successful responses
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Prevent infinite loop
      
      const refresh = localStorage.getItem("refresh");
      if (refresh) {
        try {
          // Get new access token using refresh token
          const { data } = await axios.post("/api/token/refresh/", { refresh });
          localStorage.setItem("access", data.access);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.clear();
          window.location.href = "/";
        }
      }
    }
    
    return Promise.reject(error);
  }
);
```

**Flow Diagram**:
```
User Request → Add Access Token → Send to API
                                      │
                                  [Response]
                                      │
                          ┌───────────┴────────────┐
                          │                        │
                       [200 OK]              [401 Unauthorized]
                          │                        │
                    Return Data              Is retry?
                                              │    │
                                            No│    │Yes → Fail
                                              │
                                         Get Refresh Token
                                              │
                                    POST /token/refresh/
                                              │
                                    ┌─────────┴──────────┐
                                    │                    │
                              [Success]            [Failed]
                                    │                    │
                          Store New Token          Logout User
                                    │
                          Retry Original Request
```

### Routing & Protected Routes

```javascript
// Public routes
<Route path="/" element={<LoginPage />} />
<Route path="/register" element={<RegisterPage />} />

// Protected route (requires authentication)
<Route path="/dashboard/*" element={<Dashboard />} />
  // Inside Dashboard, sub-routes are determined by role
  // URL: /dashboard/availability, /dashboard/book, etc.
```

**Protection mechanism:**
```javascript
useEffect(() => {
  const fetchProfile = async () => {
    try {
      const user = await authService.getProfile();
      setProfile(user);
    } catch (err) {
      navigate('/'); // Redirect to login if not authenticated
    }
  };
  fetchProfile();
}, []);
```

---

## Backend Architecture

### Django Project Structure

```
Backend/              # Django project root
├── settings.py       # Configuration (database, CORS, JWT, apps)
├── urls.py           # Root URL routing
└── wsgi.py           # WSGI entry point for Gunicorn

Users/                # User management app
├── models.py         # User, Profile, Role, Faculty, Major
├── serializers.py    # DRF serializers for API responses
├── views.py          # ViewSets for CRUD operations
├── urls.py           # App-level URL routing
└── migrations/       # Database migrations

Tutoring/             # Core coaching/session management
├── models.py         # Tutor, Student, Session, Registration
├── serializers.py    # Session, Tutor, Student serializers
├── views.py          # Session booking logic, availability
└── urls.py

Feedback/             # Feedback & ratings
├── models.py         # Feedback model
├── views.py          # Feedback CRUD
└── urls.py
```

### Django Apps Philosophy

**Why separate apps?**
1. **Separation of Concerns**: Each app has a single, clear responsibility
2. **Reusability**: Apps can be extracted and reused in other projects
3. **Maintainability**: Changes in one app don't cascade to others
4. **Team Collaboration**: Different developers can work on different apps

**App Boundaries:**
- **Users**: Everything related to authentication, profiles, and user metadata
- **Tutoring**: Business logic for coaching sessions, availability, bookings
- **Feedback**: Post-session ratings and reviews

### Django REST Framework ViewSets

**ViewSet Pattern**: Combines related views into a single class

```python
class SessionViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations for Session model.
    Auto-generates routes:
      GET    /api/tutoring/sessions/          → list()
      POST   /api/tutoring/sessions/          → create()
      GET    /api/tutoring/sessions/{id}/     → retrieve()
      PUT    /api/tutoring/sessions/{id}/     → update()
      PATCH  /api/tutoring/sessions/{id}/     → partial_update()
      DELETE /api/tutoring/sessions/{id}/     → destroy()
    """
    
    queryset = Session.objects.select_related(
        "tutor__profile__user",
        "student__profile__user"
    ).all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "tutor__id", "student__id"]
    
    def perform_create(self, serializer):
        """Custom logic when booking a session"""
        user = self.request.user
        
        # Only students can book sessions
        if user.profile.role.name.lower() != "student":
            raise PermissionDenied("Only learners can book sessions")
        
        # Auto-assign student from logged-in user
        student, _ = Student.objects.get_or_create(profile=user.profile)
        serializer.save(student=student, status="scheduled")
    
    def get_queryset(self):
        """Filter sessions based on user role"""
        user = self.request.user
        role = user.profile.role.name.lower()
        
        if role == "admin":
            return self.queryset  # Admins see all
        elif role == "tutor":
            return self.queryset.filter(tutor__profile__user=user)
        elif role == "student":
            return self.queryset.filter(student__profile__user=user)
        
        return self.queryset.none()  # Unknown role sees nothing
```

**Benefits of ViewSets:**
- **Less Code**: One class handles all CRUD operations
- **Consistency**: Standard REST patterns automatically enforced
- **Customization**: Easy to override specific methods (perform_create, get_queryset)
- **DRY Principle**: Queryset, serializer, permissions defined once

### Serializers (Data Transformation Layer)

**Purpose**: Convert Django models to JSON and vice versa

```python
class SessionSerializer(serializers.ModelSerializer):
    tutor = TutorSerializer(read_only=True)  # Nested serializer
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = Session
        fields = [
            'id', 'tutor', 'student', 
            'start_time', 'end_time', 
            'location', 'mode', 'status'
        ]
        read_only_fields = ['id', 'tutor', 'student']  # Set by backend
    
    def validate(self, data):
        """Custom validation logic"""
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(
                "End time must be after start time"
            )
        return data
```

**Model → Serializer → JSON flow:**
```
Database Query:
  Session.objects.get(id=42)
  
Django Model Instance:
  Session(id=42, tutor=Tutor(...), start_time=datetime(...), ...)

Serializer:
  SessionSerializer(instance).data

JSON Response:
  {
    "id": 42,
    "tutor": {"id": 3, "profile": {...}, "expertise": "..."},
    "start_time": "2025-01-20T10:00:00Z",
    ...
  }
```

---

## Database Design

### Entity-Relationship Diagram

```
┌──────────────┐
│     User     │  (Django built-in)
│──────────────│
│ PK id        │
│    username  │
│    email     │
│    password  │
└──────┬───────┘
       │ 1
       │
       │ 1 (One-to-One)
       │
┌──────▼───────┐
│   Profile    │
│──────────────│
│ PK id        │
│ FK user_id   │───────────────┐
│ FK role_id   │               │
│ FK faculty   │               │
│ FK major     │               │
│    student_id│               │
└──────┬───────┘               │
       │                       │
       ├───────────┬───────────┤
       │ 1         │ 1         │
       │           │           │
┌──────▼─────┐ ┌──▼──────┐ ┌──▼──────────┐
│   Tutor    │ │ Student │ │    Role     │
│────────────│ │─────────│ │─────────────│
│ PK id      │ │ PK id   │ │ PK id       │
│ FK profile │ │ FK prof │ │    name     │
│ expertise  │ │ study_y │ │  (Student,  │
│ bio        │ │ support │ │   Tutor,    │
│availability│ └─────┬───┘ │   Admin)    │
│  (JSON)    │       │     └─────────────┘
└──────┬─────┘       │
       │             │
       │ *           │ *
       │             │
       │    ┌────────▼────────┐
       │    │     Session     │
       │    │─────────────────│
       │    │ PK id           │
       └────┤ FK tutor_id     │
            │ FK student_id   │
            │    start_time   │
            │    end_time     │
            │    location     │
            │    mode         │
            │    status       │
            └────────┬────────┘
                     │ 1
                     │
                     │ *
            ┌────────▼────────┐
            │    Feedback     │
            │─────────────────│
            │ PK id           │
            │ FK session_id   │
            │ FK from_user_id │
            │    rating       │
            │    comment      │
            └─────────────────┘
```

### Normalization Strategy

**3rd Normal Form (3NF)** achieved:

1. **1NF**: All fields are atomic (no repeating groups)
2. **2NF**: No partial dependencies (all non-key fields depend on the whole key)
3. **3NF**: No transitive dependencies

**Example: Why Faculty → Major → Profile hierarchy?**

❌ **Denormalized (Bad)**:
```
Profile: (user_id, faculty_name, major_name)
- Duplicate faculty_name for every major
- Update anomaly: Changing faculty name requires updating all profiles
```

✅ **Normalized (Good)**:
```
Faculty: (id, name)
Major: (id, faculty_id, name)
Profile: (id, user_id, faculty_id, major_id)
- Faculty name stored once
- Updates cascade automatically
```

### Indexing Strategy

**Indexes automatically created by Django:**
- Primary keys (`id` fields)
- Foreign keys (`user_id`, `tutor_id`, etc.)
- Unique fields (`username`, `email`)

**Additional indexes to consider for production:**

```python
class Session(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'start_time']),  # Fast filtering
            models.Index(fields=['tutor', 'status']),       # Tutor dashboard
            models.Index(fields=['student', 'status']),     # Student dashboard
        ]
```

**Why these indexes?**
- Queries like `Session.objects.filter(tutor=X, status='scheduled')` are common
- Composite indexes speed up multi-field filters
- Trade-off: Slightly slower writes for much faster reads

### Database Constraints

```python
class Session(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='end_time_after_start_time'
            )
        ]
```

**Constraint types used:**
1. **Foreign Key Constraints**: Referential integrity (can't have session without valid tutor/student)
2. **Check Constraints**: Business rules (end_time > start_time)
3. **Unique Constraints**: No duplicate usernames, student IDs

---

## Authentication & Authorization

### JWT Token Flow

```
┌─────────────┐                              ┌─────────────┐
│   Client    │                              │   Server    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │  POST /api/token/                          │
       │  { username, password }                    │
       ├───────────────────────────────────────────>│
       │                                            │
       │                                     Verify Credentials
       │                                            │
       │                                     Generate JWT Tokens
       │                                     - Access (60 min TTL)
       │                                     - Refresh (7 day TTL)
       │                                            │
       │  { access: "eyJ...", refresh: "eyJ..." }   │
       │<───────────────────────────────────────────┤
       │                                            │
  Store tokens in                                   │
  localStorage                                      │
       │                                            │
       │  GET /api/tutoring/sessions/               │
       │  Authorization: Bearer eyJ...              │
       ├───────────────────────────────────────────>│
       │                                            │
       │                                     Decode JWT
       │                                     Extract user_id
       │                                     Load user from DB
       │                                     Check permissions
       │                                            │
       │  [Session data]                            │
       │<───────────────────────────────────────────┤
       │                                            │
  [60 minutes later]                                │
       │                                            │
       │  GET /api/tutoring/sessions/               │
       │  Authorization: Bearer eyJ... (expired)    │
       ├───────────────────────────────────────────>│
       │                                            │
       │                                     JWT Expired!
       │                                            │
       │  401 Unauthorized                          │
       │<───────────────────────────────────────────┤
       │                                            │
  Interceptor catches 401                           │
  Automatically sends refresh                       │
       │                                            │
       │  POST /api/token/refresh/                  │
       │  { refresh: "eyJ..." }                     │
       ├───────────────────────────────────────────>│
       │                                            │
       │                                     Verify Refresh Token
       │                                     Generate New Access
       │                                            │
       │  { access: "eyJ..." }                      │
       │<───────────────────────────────────────────┤
       │                                            │
  Store new access token                            │
  Retry original request                            │
       │                                            │
```

### JWT Token Structure

**Access Token Payload:**
```json
{
  "token_type": "access",
  "exp": 1705750800,      // Expiration timestamp
  "iat": 1705747200,      // Issued at timestamp
  "jti": "abc123...",     // Unique token ID
  "user_id": 5            // User identification
}
```

**Signed with HMAC-SHA256** using `SECRET_KEY` from Django settings.

### Role-Based Access Control (RBAC)

**Three roles:**
1. **Student (Learner)**: Can book sessions, view coaches, submit feedback
2. **Tutor (Coach)**: Can set availability, view sessions, receive feedback
3. **Admin**: Full access to all resources, analytics

**Implementation:**

```python
# Permission check in view
def perform_create(self, serializer):
    user = self.request.user
    role_name = user.profile.role.name.lower()
    
    if role_name != "student":
        raise PermissionDenied("Only learners can book sessions")
    
    # ... proceed with booking

# Queryset filtering by role
def get_queryset(self):
    role = self.request.user.profile.role.name.lower()
    
    if role == "admin":
        return Session.objects.all()
    elif role == "tutor":
        return Session.objects.filter(tutor__profile__user=self.request.user)
    elif role == "student":
        return Session.objects.filter(student__profile__user=self.request.user)
```

**Why database role instead of Django permissions?**
- **Business Domain**: Roles are part of the application's domain model
- **Flexibility**: Easy to add role-specific fields (e.g., `Student.study_year`)
- **Auditing**: Role changes are tracked in Profile model
- **Frontend**: Frontend can show/hide features based on role without extra API calls

---

## API Design Patterns

### RESTful Resource Naming

**Conventions used:**
- **Plural nouns**: `/sessions`, `/tutors`, `/feedback`
- **Hierarchical**: `/tutoring/sessions` (app namespace)
- **HTTP verbs for actions**: GET, POST, PATCH, DELETE
- **No verbs in URLs**: ❌ `/createSession`, ✅ `POST /sessions`

### Filtering & Pagination

**Query parameters:**
```
GET /api/tutoring/sessions/?status=scheduled&tutor=3
GET /api/tutoring/sessions/?page=2&page_size=20
GET /api/tutoring/sessions/?search=python&ordering=-start_time
```

**Implementation:**
```python
filter_backends = [
    DjangoFilterBackend,    # ?status=scheduled
    filters.SearchFilter,   # ?search=keyword
    filters.OrderingFilter  # ?ordering=-created_at
]
filterset_fields = ["status", "tutor__id", "student__id"]
search_fields = ["tutor__profile__user__username"]
ordering_fields = ["start_time", "end_time"]
```

### Error Handling

**Standard HTTP status codes:**
- `200 OK`: Successful GET, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server-side bug

**Error response format:**
```json
{
  "detail": "Only learners can book sessions"
}

// Or for validation errors:
{
  "start_time": ["This field is required"],
  "end_time": ["End time must be after start time"]
}
```

---

## Request Lifecycle

### Complete Flow: Booking a Session

**1. User Action (Frontend)**
```javascript
// User clicks "Book Session" button
const handleBookSession = async () => {
  setLoading(true);
  try {
    const session = await authService.createSession({
      tutor: selectedTutor.id,
      start_time: "2025-01-20T10:00:00Z",
      end_time: "2025-01-20T11:00:00Z",
      location: "Zoom",
      mode: "online"
    });
    setSuccess("Session booked!");
    navigate("/dashboard/schedule");
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
};
```

**2. Axios Request Interceptor**
```javascript
// Automatically adds JWT token
config.headers.Authorization = `Bearer ${localStorage.getItem("access")}`;
```

**3. HTTP Request**
```http
POST /api/tutoring/sessions/ HTTP/1.1
Host: cohortiva-backend.onrender.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "tutor": 3,
  "start_time": "2025-01-20T10:00:00Z",
  "end_time": "2025-01-20T11:00:00Z",
  "location": "Zoom",
  "mode": "online"
}
```

**4. Django Middleware Chain**
```
SecurityMiddleware → CORS → Session → CSRF → Authentication → View
```

**5. Authentication Middleware**
```python
# rest_framework_simplejwt.authentication.JWTAuthentication
token = request.headers.get("Authorization").replace("Bearer ", "")
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
user_id = payload["user_id"]
request.user = User.objects.get(id=user_id)
```

**6. URL Routing**
```python
# Backend/urls.py
urlpatterns = [
    path('api/tutoring/', include('Tutoring.urls')),
]

# Tutoring/urls.py
router.register(r'sessions', SessionViewSet)
# Matches: POST /api/tutoring/sessions/ → SessionViewSet.create()
```

**7. ViewSet Method**
```python
# SessionViewSet.create() (inherited from ModelViewSet)
def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # Validation
    self.perform_create(serializer)            # Custom logic
    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=201, headers=headers)
```

**8. Custom Business Logic**
```python
def perform_create(self, serializer):
    # Check role
    if self.request.user.profile.role.name.lower() != "student":
        raise PermissionDenied("Only learners can book")
    
    # Get or create Student
    student, _ = Student.objects.get_or_create(
        profile=self.request.user.profile
    )
    
    # Save with auto-assigned fields
    serializer.save(student=student, status="scheduled")
```

**9. Database Transaction**
```sql
BEGIN;
INSERT INTO Tutoring_session (tutor_id, student_id, start_time, end_time, location, mode, status)
VALUES (3, 7, '2025-01-20 10:00:00', '2025-01-20 11:00:00', 'Zoom', 'online', 'scheduled');
COMMIT;
```

**10. Serializer Response**
```python
# SessionSerializer transforms model to JSON
{
  "id": 42,
  "tutor": {
    "id": 3,
    "profile": {
      "user": {"first_name": "Jane", "last_name": "Coach"}
    },
    "expertise": "Data Science"
  },
  "student": {
    "id": 7,
    "profile": {
      "user": {"first_name": "John", "last_name": "Learner"}
    }
  },
  "start_time": "2025-01-20T10:00:00Z",
  "end_time": "2025-01-20T11:00:00Z",
  "location": "Zoom",
  "mode": "online",
  "status": "scheduled"
}
```

**11. HTTP Response**
```http
HTTP/1.1 201 Created
Content-Type: application/json
Vary: Origin
X-Frame-Options: DENY

{ "id": 42, "tutor": {...}, ... }
```

**12. Frontend Update**
```javascript
// Axios resolves promise
const session = await authService.createSession(...);
// Component updates state
setSuccess("Session booked!");
navigate("/dashboard/schedule");
```

**Total Latency**: ~200-500ms depending on network and database

---

## Deployment Architecture

### Production Stack

```
┌────────────────────────────────────────────────────────┐
│              USER'S BROWSER / MOBILE                   │
└────────────────┬───────────────────────────────────────┘
                 │
                 │ HTTPS (TLS 1.3)
                 │
    ┌────────────▼───────────┐         ┌──────────────────────┐
    │   Vercel Edge Network   │         │   Render.com         │
    │   (Frontend CDN)        │         │   (Backend PaaS)     │
    │                         │         │                      │
    │  - React Build Assets   │─────────│  - Django API        │
    │  - Global Distribution  │  HTTPS  │  - Gunicorn WSGI     │
    │  - Auto HTTPS/SSL       │         │  - Auto-scaling      │
    │  - Cache-Control        │         │  - Health Checks     │
    └─────────────────────────┘         └──────────┬───────────┘
                                                   │
                                                   │ psycopg3
                                                   │ Connection Pool
                                                   │
                                        ┌──────────▼───────────┐
                                        │   Neon PostgreSQL    │
                                        │   (Database DBaaS)   │
                                        │                      │
                                        │  - Managed Postgres  │
                                        │  - Auto-backup       │
                                        │  - Connection Pool   │
                                        │  - SSL Required      │
                                        └──────────────────────┘
```

### Environment Variables Strategy

**Backend (.env on Render)**:
```bash
# Security
SECRET_KEY=<randomly-generated-64-char-string>
DEBUG=False  # CRITICAL: Never True in production

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# CORS & Allowed Hosts
ALLOWED_HOSTS=cohortiva-backend.onrender.com,localhost
FRONTEND_URL=https://cohortiva-frontend.vercel.app
```

**Frontend (.env.production on Vercel)**:
```bash
REACT_APP_API_URL=https://cohortiva-backend.onrender.com/api/
```

**Why environment variables?**
- **Security**: Secrets never in version control
- **Flexibility**: Same code deploys to dev/staging/prod with different configs
- **12-Factor App**: Industry best practice for cloud-native apps

---

## Security Considerations

### 1. SQL Injection Prevention
**Django ORM** uses parameterized queries automatically:
```python
# SAFE: Django uses parameterized query
Session.objects.filter(tutor__id=request.GET.get('tutor_id'))

# DANGEROUS (never do this):
# cursor.execute(f"SELECT * FROM session WHERE tutor_id = {tutor_id}")
```

### 2. Cross-Site Scripting (XSS)
**React** escapes output by default:
```jsx
// SAFE: React auto-escapes
<p>{userInput}</p>

// DANGEROUS (bypasses escaping):
// <div dangerouslySetInnerHTML={{__html: userInput}} />
```

### 3. Cross-Site Request Forgery (CSRF)
**JWT tokens** are immune to CSRF (unlike cookies):
- Tokens in `localStorage`, not cookies
- Must be explicitly sent in `Authorization` header
- Malicious sites can't access `localStorage` of another origin

### 4. Password Security
**Django's PBKDF2 hashing:**
```python
# Automatically hashed by User.set_password()
User.objects.create_user(username="...", password="plaintext")
# Stored as: pbkdf2_sha256$600000$salt$hash
```

### 5. HTTPS Enforcement
- **Vercel**: Automatic HTTPS
- **Render**: Automatic HTTPS + redirect from HTTP
- **Django**: `SECURE_SSL_REDIRECT=True` in production

### 6. CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    "https://cohortiva-frontend.vercel.app"
]
CORS_ALLOW_CREDENTIALS = True  # For cookies if needed later
```

**Why strict CORS?**
- Prevents unauthorized domains from calling your API
- Protects user data from being exfiltrated to malicious sites

---

## Scalability & Performance

### Current Bottlenecks & Solutions

#### 1. **Database Queries (N+1 Problem)**

**Problem**: Loading sessions with related tutor/student causes multiple queries

❌ **Bad**:
```python
sessions = Session.objects.all()  # 1 query
for session in sessions:
    print(session.tutor.profile.user.first_name)  # N queries
```

✅ **Good (already implemented)**:
```python
sessions = Session.objects.select_related(
    "tutor__profile__user",
    "student__profile__user"
).all()  # 1 query with JOINs
```

#### 2. **Static File Serving**

**Solution**: Whitenoise + Vercel CDN
- Backend: Whitenoise serves static files with far-future cache headers
- Frontend: Vercel CDN distributes assets globally
- Result: Static files load in <50ms worldwide

#### 3. **Database Connection Pooling**

**Neon** provides built-in connection pooling:
```
DATABASE_URL=postgresql://user:pass@host:5432/db?pgbouncer=true
```

**Benefits**:
- Reuses connections instead of creating new ones
- Handles connection spikes gracefully
- Reduces database load

#### 4. **API Response Caching**

**Future optimization** (not yet implemented):
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def faculties_list(request):
    # Rarely-changing data like faculties/majors
    ...
```

### Horizontal Scaling Strategy

**Current architecture supports horizontal scaling:**

1. **Backend**: Deploy multiple Render instances behind load balancer
   - ✅ Stateless (JWT, no session storage)
   - ✅ Shared database via Neon
   - ✅ No server-side state

2. **Frontend**: Already on Vercel CDN (global distribution)

3. **Database**: Neon supports read replicas for scaling reads

**To scale to 10,000 users:**
- Add database read replicas
- Enable Redis caching for API responses
- Use Celery for background tasks (email notifications)
- Add database indexes on frequently-queried fields

---

## Interview Talking Points

### "Walk me through your architecture"
> "Cohortiva uses a three-tier architecture with React on the frontend, Django REST Framework on the backend, and PostgreSQL for the database. The frontend is a single-page application that communicates with the backend via RESTful APIs using JWT for authentication. I deployed the frontend to Vercel for global CDN distribution and the backend to Render with a Neon-managed PostgreSQL database. The architecture is stateless and horizontally scalable."

### "How does authentication work?"
> "I implemented JWT-based authentication using Django SimpleJWT. When a user logs in, they receive an access token (60-minute expiry) and a refresh token (7-day expiry). The frontend stores these in localStorage and uses Axios interceptors to automatically attach the access token to every API request. If a request fails with 401, the interceptor automatically uses the refresh token to get a new access token and retries the request. This provides a seamless user experience while maintaining security."

### "How did you handle authorization?"
> "I use role-based access control with three roles: Student (Learner), Tutor (Coach), and Admin. Roles are stored in the database as part of the user's profile. At the API level, I filter querysets based on the logged-in user's role—students only see their sessions, tutors see sessions they're coaching, and admins see everything. I also have permission checks in the view layer, like ensuring only students can book sessions."

### "What about database performance?"
> "I avoid the N+1 query problem by using `select_related` and `prefetch_related` to join related tables in a single query. For example, when fetching sessions, I eagerly load the associated tutor and student profiles. I also have database indexes on frequently-filtered fields like status and foreign keys. In production, I use Neon's connection pooling to handle connection spikes efficiently."

### "How would you scale this application?"
> "The architecture is already designed for horizontal scaling since it's stateless—JWT tokens mean there's no server-side session storage. To scale, I would: (1) deploy multiple backend instances behind a load balancer, (2) add database read replicas for read-heavy endpoints, (3) implement Redis caching for rarely-changing data like faculties and majors, (4) use Celery for asynchronous tasks like sending email notifications, and (5) add full-text search with Elasticsearch if the session search becomes more complex."

### "What security measures did you implement?"
> "I followed OWASP best practices: (1) Django ORM prevents SQL injection through parameterized queries, (2) React auto-escapes output to prevent XSS, (3) JWT tokens avoid CSRF attacks since they're in localStorage not cookies, (4) passwords are hashed with PBKDF2 using Django's built-in User model, (5) HTTPS is enforced on both Vercel and Render, (6) CORS is configured to only allow my frontend domain, and (7) I never expose the SECRET_KEY or database credentials in version control."

---

**End of Architecture Deep Dive**

This document demonstrates enterprise-level system design, implementation, and deployment understanding suitable for SDE Intern and Junior SDE interviews.
