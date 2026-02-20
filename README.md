# Backend - Bus Ticket Booking System

Django REST backend for authentication, route/schedule management, seat holding, and booking workflows.

## Tech Stack

- Python 3.8+
- Django 5.x
- Django REST Framework
- SimpleJWT + Djoser
- SQLite (default dev database)

## Getting Started

1. Navigate to backend:
   ```bash
   cd backend
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```bash
   python manage.py migrate
   ```
5. Run server:
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create `backend/.env` with:

```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
```

## Development / Coding

- Keep business rules in `api/services.py` and keep views thin.
- Use serializers for request/response validation and shaping.
- Keep booking and seat-hold operations atomic (`transaction.atomic`) to avoid race conditions.
- Add/update migrations for every model change; do not edit old migrations directly.
- Prefer explicit permissions per view/viewset rather than relying on global defaults.
- Keep API contracts stable for frontend consumers (`/api/...` endpoints).

## Useful Commands

```bash
python manage.py check
python manage.py test
python manage.py makemigrations
python manage.py migrate
```

## Project Structure

- `core/` Django settings, URL config, ASGI/WSGI
- `accounts/` auth, custom user, JWT cookie flow
- `api/` domain models, serializers, views, services, management commands

## API Docs

- Swagger: `http://localhost:8000/`
- ReDoc: `http://localhost:8000/redoc/`
