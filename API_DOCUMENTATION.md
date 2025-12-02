# Employee Management System API Documentation

## Overview
This is a REST API for an Employee Management System built with Django REST Framework. It provides JWT-based authentication with role-based access control for Employee and HR users.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
The API uses JWT (JSON Web Token) authentication. Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## User Roles
- **EMPLOYEE**: Basic access to profile and dashboard
- **HR**: Full access to employee management, statistics, and departments

---

## API Endpoints

### Authentication

#### POST `/auth/login/`
Login with username and password to get JWT tokens.

**Request Body:**
```json
{
    "username": "hr_manager",
    "password": "hr123456"
}
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "username": "hr_manager",
        "email": "hr@company.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "role": "HR",
        "employee_id": "HR001",
        "department": "Human Resources",
        "phone_number": "+1-555-0101",
        "hire_date": "2023-01-15",
        "is_active": true,
        "date_joined": "2023-01-01T00:00:00Z",
        "last_login": "2023-12-02T10:00:00Z"
    },
    "tokens": {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
}
```

#### POST `/auth/logout/`
Logout and blacklist refresh token.

**Request Body:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/auth/refresh/`
Refresh access token using refresh token.

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### User Management

#### GET `/profile/`
Get current user profile information.

**Response:**
```json
{
    "id": 1,
    "username": "hr_manager",
    "email": "hr@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "HR",
    "employee_id": "HR001",
    "department": "Human Resources",
    "phone_number": "+1-555-0101",
    "hire_date": "2023-01-15",
    "is_active": true,
    "date_joined": "2023-01-01T00:00:00Z",
    "last_login": "2023-12-02T10:00:00Z"
}
```

#### PUT `/profile/`
Update current user profile.

**Request Body:**
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@company.com",
    "phone_number": "+1-555-0101"
}
```

#### POST `/change-password/`
Change current user password.

**Request Body:**
```json
{
    "old_password": "oldpassword123",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
}
```

#### GET `/user-info/`
Get basic current user information.

---

### Dashboard

#### GET `/dashboard/`
Get dashboard data based on user role.

**HR Response:**
```json
{
    "user": { /* user object */ },
    "stats": {
        "total_employees": 5,
        "total_hr": 2,
        "total_departments": 4,
        "active_employees": 4,
        "recent_logins": 3
    },
    "role": "HR"
}
```

**Employee Response:**
```json
{
    "user": { /* user object */ },
    "role": "EMPLOYEE"
}
```

---

### Employee Management (HR Only)

#### GET `/employees/`
List all employees with optional filtering.

**Query Parameters:**
- `search`: Search by username, name, employee_id, or email
- `department`: Filter by department
- `active`: Filter by active status (true/false)
- `page`: Page number for pagination

**Response:**
```json
{
    "count": 10,
    "next": "http://localhost:8000/api/employees/?page=2",
    "previous": null,
    "results": [
        {
            "id": 2,
            "username": "employee1",
            "email": "john.doe@company.com",
            "full_name": "John Doe",
            "employee_id": "EMP001",
            "department": "Engineering",
            "role": "EMPLOYEE",
            "role_display": "Employee",
            "hire_date": "2023-03-01",
            "is_active": true,
            "last_login": "2023-12-01T09:00:00Z"
        }
    ]
}
```

#### POST `/employees/`
Create a new employee (HR only).

**Request Body:**
```json
{
    "username": "newemployee",
    "email": "new@company.com",
    "password": "password123",
    "first_name": "New",
    "last_name": "Employee",
    "employee_id": "EMP003",
    "department": "Marketing",
    "phone_number": "+1-555-0104",
    "hire_date": "2023-12-01"
}
```

#### GET `/employees/{id}/`
Get specific employee details (HR only).

#### PUT `/employees/{id}/`
Update specific employee (HR only).

#### DELETE `/employees/{id}/`
Delete/deactivate specific employee (HR only).

#### GET `/employees/stats/`
Get employee statistics (HR only).

**Response:**
```json
{
    "total_employees": 10,
    "active_employees": 9,
    "inactive_employees": 1,
    "employees_by_department": [
        {
            "department": "Engineering",
            "count": 5
        },
        {
            "department": "Sales",
            "count": 3
        }
    ]
}
```

---

### Department Management (HR Only)

#### GET `/departments/`
List all departments.

**Response:**
```json
[
    {
        "id": 1,
        "name": "Human Resources",
        "description": "Manages employee relations and company policies",
        "created_at": "2023-01-01T00:00:00Z"
    }
]
```

#### POST `/departments/`
Create a new department (HR only).

#### GET `/departments/{id}/`
Get specific department details (HR only).

#### PUT `/departments/{id}/`
Update specific department (HR only).

#### DELETE `/departments/{id}/`
Delete specific department (HR only).

---

## Error Responses

### Authentication Error
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Permission Error
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Validation Error
```json
{
    "field_name": [
        "This field is required."
    ]
}
```

---

## Demo Users

After running `python manage.py create_demo_data`, you can use these credentials:

- **Admin**: `admin` / `admin123` (Superuser with HR role)
- **HR Manager**: `hr_manager` / `hr123456` (HR role)
- **Employee 1**: `employee1` / `emp123456` (Employee role)
- **Employee 2**: `employee2` / `emp123456` (Employee role)

---

## Getting Started

1. Run migrations: `python manage.py migrate`
2. Create demo data: `python manage.py create_demo_data`
3. Start server: `python manage.py runserver`
4. Login at: `POST http://localhost:8000/api/auth/login/`
5. Use access token for authenticated requests

## Frontend Integration

This API is designed to be consumed by a separate frontend application (React, Vue, Angular, etc.). The JWT tokens should be stored securely in the frontend and included in all API requests.

CORS is configured for common development ports (3000, 8080, 4200) for frontend development.