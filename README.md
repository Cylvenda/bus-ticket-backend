# Backend - Bus Ticket Booking System

Django-based backend for the Bus Ticket Booking System.

## Technologies

- Django 4.2
- Django REST Framework
- SQLite (development)
- Python 3.8+

## Getting Started

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

- `core/` - Main Django project settings
  - `settings/` - Configuration files
  - `urls.py` - Main URL configuration
- `accounts/` - User authentication app
- `tickets/` - Bus tickets management app

## API Documentation

API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Testing

To run tests:
```bash
python manage.py test
```