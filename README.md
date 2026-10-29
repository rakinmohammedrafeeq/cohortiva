<div align="center">

<pre align="center">
 ██████╗ ██████╗ ██╗  ██╗ ██████╗ ██████╗ ████████╗██╗██╗   ██╗ █████╗
██╔════╝██╔═══██╗██║  ██║██╔═══██╗██╔══██╗╚══██╔══╝██║██║   ██║██╔══██╗
██║     ██║   ██║███████║██║   ██║██████╔╝   ██║   ██║██║   ██║███████║
██║     ██║   ██║██╔══██║██║   ██║██╔══██╗   ██║   ██║╚██╗ ██╔╝██╔══██║
╚██████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║   ██║   ██║ ╚████╔╝ ██║  ██║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝  ╚═╝  ╚═╝
</pre>

# COHORTIVA — Coaching Session & Feedback Portal

**Full-Stack Coaching Workflows • Session Scheduling • Feedback Management • REST API Integration**

[![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=20232A)](#8-technology-stack)
[![Backend](https://img.shields.io/badge/Backend-Django%20REST%20Framework-092E20?logo=django&logoColor=white)](#8-technology-stack)
[![Language](https://img.shields.io/badge/Language-Python-3776AB?logo=python&logoColor=white)](#8-technology-stack)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20Target-4169E1?logo=postgresql&logoColor=white)](#8-technology-stack)
[![API](https://img.shields.io/badge/API-RESTful-0F766E)](#7-api-and-data-flow)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[![Portfolio](https://img.shields.io/badge/Portfolio-rakinmohammedrafeeq.vercel.app-10B981?logo=vercel&logoColor=white)](https://rakinmohammedrafeeq.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-rakinmohammedrafeeq-181717?logo=github&logoColor=white)](https://github.com/rakinmohammedrafeeq)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Rakin%20Mohammed%20Rafeeq-0A66C2?logo=linkedin&logoColor=white)](https://linkedin.com/in/rakinmohammedrafeeq)

</div>

---

> **Cohortiva** is a coaching session and feedback portal being customized from an existing open-source peer-tutoring platform. Its intended workflow brings session scheduling, session lifecycle management, learner feedback, and database-backed operations together through a React frontend and Django REST API backend.
>
> **Project integrity note:** The upstream project already provides peer-tutoring workflows, including user roles, availability, booking/cancellation, and feedback. Cohortiva-specific changes should be implemented and tested before being described as original functionality. The upstream code currently documents React (not a verified TypeScript conversion), SQLite for local development, and PostgreSQL-ready deployment configuration.

---

## 📑 Table of Contents

1. [Overview](#1-overview)
2. [Goals and Scope](#2-goals-and-scope)
3. [Key Workflows](#3-key-workflows)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Technology Stack](#6-technology-stack)
7. [API and Data Flow](#7-api-and-data-flow)
8. [Requirements](#8-requirements)
9. [Installation](#9-installation)
10. [Configuration](#10-configuration)
11. [Running the Backend](#11-running-the-backend)
12. [Running the Frontend](#12-running-the-frontend)
13. [Usage Walkthrough](#13-usage-walkthrough)
14. [Testing and Verification](#14-testing-and-verification)
15. [Security and Data Handling](#15-security-and-data-handling)
16. [Current Starter vs. Cohortiva Customization](#16-current-starter-vs-cohortiva-customization)
17. [Limitations](#17-limitations)
18. [Roadmap](#18-roadmap)
19. [Screenshots](#19-screenshots)
20. [Contributing, Attribution, License & Author](#20-contributing-attribution-license--author)

---

## 1. Overview

Coaching programs often involve coordinating people, availability, scheduled sessions, and post-session feedback. When these activities are handled across separate tools, it becomes harder to maintain consistent records and provide a clear experience for participants.

Cohortiva focuses on a single workflow for coaching-session coordination:

- **Session coordination:** keep session details and lifecycle actions organized.
- **Feedback collection:** associate feedback with the relevant completed session.
- **Frontend/backend separation:** use a React client to communicate with a Django REST API over HTTP and JSON.
- **Relational persistence:** represent users, sessions, and feedback as related database records.
- **Maintainable development:** keep UI components, backend logic, configuration, and documentation in separate areas of the repository.

### Project Context

Cohortiva is based on the public [Peer Tutoring Platform](https://github.com/phucuongtran/tutoring-platform) by `phucuongtran`. The source project provides the foundation for role-aware user flows, tutor availability, session booking and cancellation, and feedback. This repository is intended to adapt those workflows to the coaching-session use case and document the changes made.

---

## 2. Goals and Scope

### Primary Goals

1. Present a clear interface for managing coaching sessions.
2. Support session creation, retrieval, updating, and cancellation through backend APIs.
3. Connect feedback records to the sessions they describe.
4. Validate inputs and handle API errors consistently.
5. Maintain relational data through Django models and the Django ORM.
6. Test the frontend/backend integration and document local setup.

### Intended User Flow

- A user signs in and accesses the functions allowed by their role.
- A coaching session is created or selected from the available sessions.
- Session details can be viewed and updated; a session may be cancelled when appropriate.
- A participant submits feedback for a relevant session.
- The application sends requests to the Django REST API and displays success or error states from the response.

The exact screens and permissions should match the implementation in this repository. Do not assume every workflow above is complete until it has been checked and tested locally.

---

## 3. Key Workflows

### 🗓️ Session Management

The target coaching workflow covers the following operations:

- Create a coaching session.
- Retrieve session details and session lists.
- Update session information and scheduling details.
- Cancel a session and reflect its updated status.
- Validate incoming data before persisting changes.

### 💬 Feedback Management

- Submit feedback associated with a session.
- Retrieve feedback records using the application's available views and API routes.
- Preserve the relationship between a session and its feedback.
- Handle invalid input and failed requests with understandable messages.

### 🔐 Accounts and Role-Aware Access

The upstream starter includes registration/login and role-aware student, tutor, and admin flows. As Cohortiva is customized, review the role names and permissions so that they accurately represent the intended coaching participants and administrators.

### 🔌 Frontend–Backend Integration

- Use HTTP requests and JSON payloads to communicate with the REST API.
- Keep API calls separate from presentation components where practical.
- Handle loading states, failed requests, and validation feedback.
- Verify request and response formats against the actual Django serializers and views.

---

## 4. Architecture

The intended application architecture separates the browser interface from backend business logic and data persistence.

```text
┌─────────────────────────────────────────────────────────────┐
│                        USER / BROWSER                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                           │
│  Pages • Components • Forms • API Client • Error States      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                DJANGO REST FRAMEWORK API                    │
│  Authentication • Serializers • Views • Validation          │
├──────────────────────┬─────────────────────┬────────────────┤
│ User / Role Flows    │ Session Workflows   │ Feedback       │
└──────────────────────┴─────────────────────┴────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      DJANGO ORM                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLITE (LOCAL STARTER) / POSTGRESQL            │
└─────────────────────────────────────────────────────────────┘
```

### Request Lifecycle

1. A user interacts with a React page or form.
2. The frontend sends an HTTP request to the configured Django API URL.
3. Django routes the request to the relevant view.
4. Serializer and application validation check the request data.
5. Django ORM reads or updates the relevant records.
6. The API returns a JSON response and appropriate HTTP status.
7. The frontend updates the UI or presents an error state.

This diagram describes the intended design. Confirm the request lifecycle against the actual code as features are adapted.

---

## 5. Project Structure

The upstream project documents the following repository layout. Individual files may change as Cohortiva is customized.

```text
cohortiva/
├── .github/                     # CI workflow and contribution templates
├── backend/                     # Django REST API
│   ├── Backend/                 # Django settings and root URL configuration
│   ├── Users/                   # Users, roles, profiles, and lookup modules
│   ├── Tutoring/                # Tutor, availability, and session workflows
│   ├── Feedback/                # Feedback-related models and views
│   ├── Fixture/                 # Seed/fixture data
│   ├── .env.example              # Backend environment template
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md
├── frontend/                    # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── config/              # Frontend configuration
│   │   ├── pages/               # Page-level views
│   │   └── services/            # API integration
│   ├── .env.example              # Frontend environment template
│   ├── package.json
│   └── README.md
├── docs/                        # Architecture, API, deployment notes
├── .editorconfig
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE                      # Preserve upstream MIT notices
└── README.md
```

> If your local tree differs, use the actual files and package scripts as the source of truth; update this diagram after renaming or reorganizing modules.

---

## 6. Technology Stack

| Layer | Technology | Purpose / status |
|---|---|---|
| Frontend | React | Browser UI and reusable components in the starter |
| Routing / API calls | React Router, Axios | Client navigation and HTTP API integration in the starter |
| Styling | CSS | Frontend presentation in the starter |
| Backend | Python, Django | Backend application and request handling |
| API | Django REST Framework | REST endpoints and serialized responses |
| Authentication | Simple JWT | JWT-based authentication in the starter |
| Filtering / CORS | `django-filter`, CORS headers | API filtering and cross-origin configuration in the starter |
| Local database | SQLite | Documented local development database |
| Deployment database | PostgreSQL | PostgreSQL-ready deployment configuration; verify actual connection settings before using it locally |
| Version control | Git, GitHub | Source control and collaboration |

### TypeScript and PostgreSQL Note

The source repository currently documents a React frontend and SQLite local development; its public README does not verify that TypeScript is already configured. If TypeScript and PostgreSQL are part of the Cohortiva implementation, migrate/confirm the frontend and database configuration, run the app and tests, and then update this table to reflect the actual state.

---

## 7. API and Data Flow

The application uses a React client communicating with Django REST endpoints. The upstream code groups backend functionality around user, tutoring/session, and feedback modules.

### Functional API Areas

| Area | Intended responsibility |
|---|---|
| Authentication / users | Registration, login, profiles, and role-aware access |
| Coaching sessions | Listing, creation, retrieval, updates, and cancellation |
| Availability | Representing available times or session slots where supported |
| Feedback | Submitting and retrieving feedback connected to sessions |
| Administration | Basic reporting or management workflows present in the starter |

**Do not hard-code API paths from this table.** Inspect the Django URL configuration and serializers in the local repository to confirm exact endpoint paths, request fields, response formats, authentication requirements, and status codes. Update the API documentation as you modify the application.

### API Verification Checklist

- [ ] Confirm the API base URL used by the frontend.
- [ ] Record the actual authentication and token-refresh flow.
- [ ] Document the implemented session endpoints and payloads.
- [ ] Document the implemented feedback endpoints and payloads.
- [ ] Verify permission rules for each user role.
- [ ] Verify response status codes and error structures.

---

## 8. Requirements

### Required Tools

- **Python:** install a version compatible with `backend/requirements.txt`.
- **Node.js and npm:** required for the React frontend.
- **Git:** required to clone the repository and track changes.
- **Database:** SQLite for the starter's documented local setup; PostgreSQL for a configured PostgreSQL environment.

### Recommended Development Setup

- A code editor such as Visual Studio Code.
- Separate terminals for backend and frontend development servers.
- A local `.env` file for development settings.
- Browser developer tools for inspecting network requests and frontend errors.

Check `frontend/package.json` and `backend/requirements.txt` for the exact package and runtime requirements before installing.

---

## 9. Installation

### 1. Clone Cohortiva

```bash
git clone https://github.com/rakinmohammedrafeeq/cohortiva.git
cd cohortiva
```

If you are still working from your local clone of the upstream source, use that local folder instead of cloning the destination repository again.

### 2. Create a Python Virtual Environment

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

For macOS/Linux, activate the environment with:

```bash
source .venv/bin/activate
```

### 3. Install Backend Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Backend Environment

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` with local values. Never commit secret keys, passwords, tokens, or production credentials.

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

The upstream README also documents a fixture-loading script:

```bash
python load_fixtures.py
```

Run this only if the script exists in your checked-out backend directory and you want to load the provided development data.

### 6. Start the Backend

```bash
python manage.py runserver
```

The Django development server normally starts at `http://127.0.0.1:8000/`.

### 7. Install and Start the Frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm start
```

For macOS/Linux, replace `Copy-Item` with `cp .env.example .env`.

The upstream README documents the frontend at `http://localhost:3000/`. If `npm start` is not defined, inspect `frontend/package.json` and use the available development script.

---

## 10. Configuration

### Backend Environment

Create `backend/.env` from `backend/.env.example`. The upstream README identifies these variables as required or commonly used:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Enables/disables Django debug mode |
| `ALLOWED_HOSTS` | Hosts allowed to serve the Django application |
| `FRONTEND_URL` | Frontend origin used by backend/CORS settings |
| `DATABASE_URL` | Database URL for PostgreSQL deployment where configured |
| `DB_ENGINE` | Database engine setting where used |
| `DB_NAME` | Database name where manual settings are used |
| `DB_USER` | Database user where manual settings are used |
| `DB_PASSWORD` | Database password where manual settings are used |
| `DB_HOST` | Database host where manual settings are used |
| `DB_PORT` | Database port where manual settings are used |

The supported variables depend on the checked-out settings module. Review `backend/Backend/` and `.env.example` before changing configuration.

### Frontend Environment

Create `frontend/.env` from `frontend/.env.example`. The upstream README documents:

```env
REACT_APP_API_URL=http://localhost:8000/api/
```

Use the variable name expected by the current frontend build tooling. Do not assume a Create React App variable will work unchanged if the frontend tooling has been migrated.

---

## 11. Running the Backend

From `backend/`, activate your virtual environment and run:

```bash
python manage.py runserver
```

Useful development checks include:

```bash
python manage.py check
python manage.py showmigrations
```

To inspect available API routes, review the root URL configuration and each app's `urls.py`. Use the Django REST Framework browsable API where enabled.

---

## 12. Running the Frontend

From `frontend/`, install dependencies and start the available development script:

```bash
npm install
npm start
```

Check `package.json` if the script differs. Confirm that the frontend's API base URL points to the Django server, and inspect the browser Network tab if requests fail.

### Common Integration Issues

- **Connection refused:** verify that Django is running at the configured host and port.
- **CORS error:** verify the frontend origin and backend CORS settings.
- **401/403 response:** check the authentication token and the endpoint's permission requirements.
- **404 response:** compare the frontend request path with the configured Django URL patterns.
- **Unexpected validation response:** compare the submitted JSON fields with the serializer's required fields.

---

## 13. Usage Walkthrough

The exact interface depends on the current frontend code. Use the following as a workflow checklist rather than a claim that every step is already available in the UI.

1. **Create an account or sign in** using the authentication flow available in the starter.
2. **Review the relevant dashboard** and role-specific profile.
3. **Explore available sessions or times** using the implemented availability/session pages.
4. **Create or book a session** and verify that the backend stores the corresponding record.
5. **Update or cancel a session** and verify the updated status in both the UI and API response.
6. **Submit feedback** for the relevant session where permitted by the implemented rules.
7. **Check the result** by reloading the view and confirming persistence in the database.

---

## 14. Testing and Verification

Test the real behavior of the local codebase after adapting it. Do not add a passing-test badge or report test counts until the test suite has actually been executed.

### Manual Verification Checklist

- [ ] Registration and login work in the configured environment.
- [ ] Protected API routes require the expected authentication.
- [ ] Session creation persists valid data.
- [ ] Session retrieval returns the expected records.
- [ ] Updating a session changes the intended fields.
- [ ] Cancellation updates the session correctly.
- [ ] Feedback is connected to the correct session.
- [ ] Invalid input produces a useful validation response.
- [ ] Frontend forms display API errors clearly.
- [ ] Database migrations work from a fresh local database.
- [ ] The app still works after restarting backend and frontend servers.

### Suggested Commands

Backend:

```bash
python manage.py check
python manage.py test
```

Frontend:

```bash
npm test
```

Run `npm test` only if the frontend's `package.json` defines a test script. Add specific tests for the behavior you implement and update this section with the real command and test results.

---

## 15. Security and Data Handling

- Keep `SECRET_KEY`, database passwords, and deployment credentials out of source control.
- Use environment variables for local and deployed configuration.
- Verify authentication and authorization for any endpoint that reads or changes user, session, or feedback data.
- Validate all inputs on the backend; frontend validation alone is not a security boundary.
- Apply production-appropriate settings for `DEBUG`, `ALLOWED_HOSTS`, CORS, and HTTPS before deployment.
- Review role and object-level permissions to prevent users from accessing or modifying another participant's records.
- Use synthetic development data in screenshots and demo environments; avoid publishing real personal feedback or account data.

The upstream starter includes JWT-oriented authentication and role-aware flows. Verify the actual permission implementation during customization rather than assuming the presence of a UI control guarantees authorization.

---

## 16. Current Starter vs. Cohortiva Customization

| Area | Documented in upstream starter | Cohortiva work to verify or complete |
|---|---|---|
| Frontend | React, React Router, Axios, CSS | Coaching-specific interface wording, flow, and styling |
| Language | JavaScript frontend is documented | TypeScript conversion/configuration if TypeScript is retained in the target stack |
| Backend | Django and Django REST Framework | Confirm coaching-specific naming, API payloads, and behavior |
| Session workflow | Tutor availability, booking, and cancellation | Verify full session CRUD and map tutor/session terminology to coaching |
| Feedback | Feedback submission foundation | Verify session-linked feedback retrieval, validation, and editing behavior as required |
| Authentication | JWT and role-aware flows | Review coaching roles and permissions end-to-end |
| Database | SQLite local; PostgreSQL-ready deployment configuration | Verify PostgreSQL driver, connection settings, migrations, and tests |
| Quality | CI and repository templates are present in the starter | Run actual checks, add feature tests, and document verified results |
| Documentation | Existing README/docs cover the starter platform | Replace screenshots, endpoint details, and feature descriptions with verified Cohortiva behavior |

This table is intentionally explicit so the repository documentation can evolve with the actual implementation.

---

## 17. Limitations

1. **Starter domain:** The source project is a peer-tutoring platform. Some labels, models, and flows may still use tutoring-specific terminology until customized.
2. **TypeScript status:** The upstream public README describes React but does not verify a TypeScript-based frontend. Check the source files and build configuration before claiming TypeScript support.
3. **Database configuration:** The upstream project documents SQLite for local development and PostgreSQL-ready deployment. A PostgreSQL deployment still requires valid configuration, dependencies, migrations, and testing.
4. **API details:** Endpoint paths and payloads must be read from the actual Django URL and serializer definitions.
5. **Test status:** No test count is claimed here. Run the checks and document the verified results after customization.
6. **Deployment status:** Deployment-oriented configuration is not the same as a confirmed production deployment. Add live URLs only after deploying and testing the application.

---

## 18. Roadmap

- [ ] Rename tutoring-specific labels and copy to Cohortiva coaching terminology.
- [ ] Verify and complete session create/read/update/cancel workflows.
- [ ] Verify feedback creation and session-to-feedback relationships.
- [ ] Improve React form validation and request error handling.
- [ ] Complete TypeScript setup if TypeScript is part of the final frontend.
- [ ] Configure and test PostgreSQL locally.
- [ ] Add endpoint documentation with example requests and responses.
- [ ] Add backend tests for session and feedback permissions.
- [ ] Add frontend/API integration checks.
- [ ] Add real screenshots under `docs/screenshots/`.
- [ ] Verify a clean setup using only the README instructions.
- [ ] Deploy only after the configuration and security review is complete.

---

## 19. Screenshots

Add screenshots after the relevant Cohortiva screens have been customized and tested. Store them in `docs/screenshots/` and update the image paths below.

| Screen | Screenshot |
|---|---|
| Login / registration | _Add `docs/screenshots/auth.png`_ |
| Coaching session dashboard | _Add `docs/screenshots/sessions.png`_ |
| Session details / scheduling | _Add `docs/screenshots/session-details.png`_ |
| Feedback submission | _Add `docs/screenshots/feedback.png`_ |

Example Markdown once an image exists:

```markdown
![Cohortiva session dashboard](docs/screenshots/sessions.png)
```

---

## 20. Contributing, Attribution, License & Author

### 🤝 Development and Contributions

For personal development, a simple feature-branch workflow is recommended:

1. Create a branch: `git checkout -b feat/coaching-session-workflow`.
2. Make a small, focused change.
3. Run the relevant backend or frontend checks.
4. Review the diff and ensure no secrets or local database files are staged.
5. Commit with a descriptive message, for example:
   - `feat: adapt session booking to coaching workflows`
   - `feat: connect feedback to coaching sessions`
   - `fix: handle invalid session update requests`
   - `docs: document local PostgreSQL setup`
6. Push the branch and review the changes before merging.

### 📌 Upstream Attribution

Cohortiva is adapted from the public project [Peer Tutoring Platform](https://github.com/phucuongtran/tutoring-platform) by `phucuongtran`.

The upstream project supplies the starting codebase for the React frontend, Django REST backend, role-aware user flows, availability/session booking, and feedback foundation. Cohortiva-specific contributions should be described separately from inherited functionality.

**License handling:** Retain the original `LICENSE` file and its existing copyright and permission notices. Do not overwrite the upstream author's notice with a new name. Add a separate notice for your own modifications only if appropriate, and only claim copyright over your original contributions.

### 📄 License

The upstream repository is released under the **MIT License**. See [`LICENSE`](LICENSE) for the complete license text and applicable notices.

### 👨‍💻 Maintainer

<div align="center">

### **Rakin Mohammed Rafeeq**

[![Portfolio](https://img.shields.io/badge/Portfolio-rakinmohammedrafeeq.vercel.app-10B981?style=for-the-badge&logo=vercel&logoColor=white)](https://rakinmohammedrafeeq.vercel.app)
[![GitHub](https://img.shields.io/badge/GitHub-rakinmohammedrafeeq-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rakinmohammedrafeeq)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Rakin%20Mohammed%20Rafeeq-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/rakinmohammedrafeeq)

📧 **Email:** [rakinmohammedrafeeq@gmail.com](mailto:rakinmohammedrafeeq@gmail.com)

</div>

---

<div align="center">

**Cohortiva — bringing coaching sessions and feedback into one workflow.**

</div>
