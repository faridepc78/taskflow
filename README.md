# TaskFlow

TaskFlow is a full-stack Django project and task management application built as a practical learning project. It combines project and task workflows, notifications, activity tracking, background jobs, caching, email flows, responsive UI, automated tests, and Docker-based local development.

## Tech Stack

- Python 3.13
- Django 6.1
- MySQL 8.4
- Redis
- Celery + Celery Beat
- Tailwind CSS 4
- Mailtrap / SMTP
- Ruff
- Docker + Docker Compose

## Main Features

### Accounts and Profile
- Registration with email OTP verification
- Login and logout
- Forgot/reset password with OTP
- Change password
- User profile and avatar

### Projects and Tasks
- Project CRUD
- Archive and restore projects
- Task CRUD
- Task status, priority and due date
- Project progress tracking
- Kanban board with drag and drop
- Task search, filtering and ordering
- Categories with per-user ownership
- Task attachments

### Notifications and Automation
- In-app notifications
- Read/unread state and unread counter
- Due tomorrow reminders
- Due today notifications
- Overdue notifications
- Duplicate notification prevention
- Celery background tasks
- Celery Beat scheduled checks

### Activity and Security
- Activity log for tracked project data
- Field-level change history
- User and timestamp tracking
- Ownership checks for projects, tasks, categories, attachments and notifications
- CSRF protection and Django password hashing

### UI
- Responsive dashboard
- Light and dark themes
- Sidebar navigation
- Modern Kanban interface
- Responsive authentication pages
- Pagination
- HTML email templates
- Tailwind-based local stylesheet build

### Performance and Quality
- Redis caching
- Automatic cache invalidation
- Automated Django tests
- Ruff formatting and linting

## Local Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create the environment file

Copy `.env.example` to `.env` and update the values for your local MySQL, Redis and SMTP setup.

```powershell
Copy-Item .env.example .env
```

### 4. Run migrations

```powershell
python manage.py migrate
```

### 5. Build the Tailwind stylesheet

```powershell
cd frontend
npm install
npm run build
cd ..
```

For active frontend development:

```powershell
cd frontend
npm run watch
```

### 6. Start Django

```powershell
python manage.py runserver
```

### 7. Start Celery

Open another terminal:

```powershell
celery -A config worker -l info --pool=solo
```

### 8. Start Celery Beat

Open another terminal:

```powershell
celery -A config beat -l info
```

## Docker Setup

Docker Compose starts these services together:

- Django web app
- MySQL
- Redis
- Celery worker
- Celery Beat

Start everything:

```powershell
docker compose up --build
```

Then open:

```text
http://127.0.0.1:8000
```

Stop the stack:

```powershell
docker compose down
```

Remove containers and persisted Docker data:

```powershell
docker compose down -v
```

The Docker setup uses the console email backend by default when SMTP settings are not supplied, so verification/reset emails are visible in the web container logs during local development.

## Environment Variables

Important variables are documented in `.env.example`:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DB_NAME
DB_USER
DB_PASSWORD
DB_ROOT_PASSWORD
DB_HOST
DB_PORT
REDIS_URL
EMAIL_BACKEND
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS
DEFAULT_FROM_EMAIL
```

## Frontend

The editable Tailwind source is:

```text
frontend/input.css
```

The generated stylesheet used by Django is:

```text
static/css/app.css
```

After changing the Tailwind source, rebuild it with:

```powershell
cd frontend
npm run build
```

Do not edit the generated stylesheet manually.

## Tests and Quality Checks

Run the full automated test suite:

```powershell
python manage.py test
```

Run Django system checks:

```powershell
python manage.py check
```

Verify that models do not require an uncommitted migration:

```powershell
python manage.py makemigrations --check --dry-run
```

Format and lint:

```powershell
ruff format .
ruff check .
```

Recommended final verification:

```powershell
ruff format .
ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Project Structure

```text
accounts/          Authentication, profile and account flows
projects/          Projects, tasks, categories, attachments and activity log
notifications/     In-app notifications and scheduled reminder logic
config/            Django and Celery configuration
frontend/          Tailwind source and frontend build configuration
static/            Generated CSS, JavaScript and static assets
templates/         Application and email templates
```

## Exporting the Project

`export-project.ps1` creates a clean ZIP while excluding local or generated content such as:

- `.env`
- virtual environments
- Git metadata
- IDE folders
- caches
- uploaded media
- collected static files
- frontend `node_modules`
- previous ZIP exports

Run:

```powershell
.\export-project.ps1
```

## Notes

- Never commit `.env`.
- `frontend/node_modules` is intentionally ignored.
- `static/css/app.css` is committed because Django serves the prebuilt stylesheet.
- The Docker Compose configuration is intended for local/development use.
