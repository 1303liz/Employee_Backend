# Employee Management System API

A comprehensive Django REST API for employee management with authentication, leave management, and attendance tracking.

## Base Information

- **Base URL**: `http://localhost:8000`
- **API Version**: 1.0.0
- **Authentication**: JWT (JSON Web Tokens)
- **Content Type**: `application/json`

## Authentication

All endpoints (except login, register, and root) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Quick Start

1. **Register/Login** to get JWT tokens
2. **Use access token** for authenticated requests  
3. **Refresh tokens** when access token expires
4. **Access Swagger UI** at `/api/schema/swagger/` for interactive testing

---

## 🔐 Authentication Endpoints

### Login
Authenticate user and receive JWT tokens.

| Method | Path | Authentication |
|--------|------|----------------|
| POST | `/api/login/` | None |

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Responses:**
- **200 OK**: Login successful
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "EMPLOYEE",
    "employee_id": "EMP001",
    "department": "Engineering",
    "phone_number": "+1234567890",
    "hire_date": "2023-01-15",
    "is_active": true
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```
- **400 Bad Request**: Invalid credentials

### Register
Register a new user account.

| Method | Path | Authentication |
|--------|------|----------------|
| POST | `/api/register/` | None |

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirm_password": "string",
  "first_name": "string",
  "last_name": "string",
  "employee_id": "string",
  "department": "string",
  "phone_number": "string",
  "hire_date": "2023-01-15"
}
```

**Responses:**
- **201 Created**: Registration successful (same format as login)
- **400 Bad Request**: Validation errors

### Logout
Blacklist refresh token to logout user.

| Method | Path | Authentication |
|--------|------|----------------|
| POST | `/api/logout/` | JWT Required |

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Responses:**
- **200 OK**: Successfully logged out
- **400 Bad Request**: Invalid token

### Token Refresh
Refresh access token using refresh token.

| Method | Path | Authentication |
|--------|------|----------------|
| POST | `/api/refresh/` | None |

**Request Body:**
```json
{
  "refresh": "string"
}
```

### Change Password
Change user password.

| Method | Path | Authentication |
|--------|------|----------------|
| POST | `/api/change-password/` | JWT Required |

**Request Body:**
```json
{
  "old_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

### User Profile
Manage user profile information.

| Method | Path | Authentication |
|--------|------|----------------|
| GET | `/api/profile/` | JWT Required |
| PUT | `/api/profile/` | JWT Required |
| PATCH | `/api/profile/` | JWT Required |

### Dashboard
Get dashboard statistics and user information.

| Method | Path | Authentication |
|--------|------|----------------|
| GET | `/api/dashboard/` | JWT Required |

---

## 👥 Employee Management

### Employee List & Creation
Manage employee records (HR only).

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employees/` | JWT Required | HR Only |
| POST | `/api/employees/` | JWT Required | HR Only |

**Query Parameters (GET):**
- `search` (string): Search by username, name, employee_id, email
- `department` (string): Filter by department
- `active` (boolean): Filter by active status

**Request Body (POST):**
```json
{
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "employee_id": "string",
  "department": "string",
  "role": "EMPLOYEE|HR|MANAGER",
  "phone_number": "string",
  "hire_date": "2023-01-15",
  "is_active": true
}
```

### Employee Details
Manage individual employee records (HR only).

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employees/{id}/` | JWT Required | HR Only |
| PUT | `/api/employees/{id}/` | JWT Required | HR Only |
| PATCH | `/api/employees/{id}/` | JWT Required | HR Only |
| DELETE | `/api/employees/{id}/` | JWT Required | HR Only |

### Employee Management Extended

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employee-management/` | JWT Required | HR Only |
| POST | `/api/employee-management/` | JWT Required | HR Only |
| GET | `/api/employee-management/{id}/` | JWT Required | HR Only |
| PUT | `/api/employee-management/{id}/` | JWT Required | HR Only |
| PATCH | `/api/employee-management/{id}/` | JWT Required | HR Only |
| DELETE | `/api/employee-management/{id}/` | JWT Required | HR Only |

### Employee Positions
Manage employee positions/roles.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employee-management/positions/` | JWT Required | HR Only |
| POST | `/api/employee-management/positions/` | JWT Required | HR Only |
| GET | `/api/employee-management/positions/{id}/` | JWT Required | HR Only |
| PUT | `/api/employee-management/positions/{id}/` | JWT Required | HR Only |
| PATCH | `/api/employee-management/positions/{id}/` | JWT Required | HR Only |
| DELETE | `/api/employee-management/positions/{id}/` | JWT Required | HR Only |

### Employee Documents
Manage employee documents.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employee-management/{employee_id}/documents/` | JWT Required | HR Only |
| POST | `/api/employee-management/{employee_id}/documents/` | JWT Required | HR Only |
| GET | `/api/employee-management/{employee_id}/documents/{id}/` | JWT Required | HR Only |
| PUT | `/api/employee-management/{employee_id}/documents/{id}/` | JWT Required | HR Only |
| PATCH | `/api/employee-management/{employee_id}/documents/{id}/` | JWT Required | HR Only |
| DELETE | `/api/employee-management/{employee_id}/documents/{id}/` | JWT Required | HR Only |

### Employee Notes
Manage employee notes and comments.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/employee-management/{employee_id}/notes/` | JWT Required | HR Only |
| POST | `/api/employee-management/{employee_id}/notes/` | JWT Required | HR Only |
| GET | `/api/employee-management/{employee_id}/notes/{id}/` | JWT Required | HR Only |
| PUT | `/api/employee-management/{employee_id}/notes/{id}/` | JWT Required | HR Only |
| PATCH | `/api/employee-management/{employee_id}/notes/{id}/` | JWT Required | HR Only |
| DELETE | `/api/employee-management/{employee_id}/notes/{id}/` | JWT Required | HR Only |

### Employee Statistics & Utilities

| Method | Path | Authentication | Permission | Description |
|--------|------|----------------|------------|-------------|
| GET | `/api/employees/stats/` | JWT Required | HR Only | Employee statistics |
| GET | `/api/employee-management/statistics/` | JWT Required | HR Only | Management statistics |
| POST | `/api/employee-management/bulk-update/` | JWT Required | HR Only | Bulk update employees |
| GET | `/api/employee-management/my-profile/` | JWT Required | All | Current user profile |

---

## 🏢 Department Management

### Department Operations
Manage organizational departments (HR only).

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/departments/` | JWT Required | HR Only |
| POST | `/api/departments/` | JWT Required | HR Only |
| GET | `/api/departments/{id}/` | JWT Required | HR Only |
| PUT | `/api/departments/{id}/` | JWT Required | HR Only |
| PATCH | `/api/departments/{id}/` | JWT Required | HR Only |
| DELETE | `/api/departments/{id}/` | JWT Required | HR Only |

**Request Body (POST/PUT):**
```json
{
  "name": "string",
  "description": "string"
}
```

---

## 🏖️ Leave Management

### Leave Applications
Manage leave requests and applications.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/leave-management/applications/` | JWT Required | All |
| POST | `/api/leave-management/applications/` | JWT Required | All |
| GET | `/api/leave-management/applications/{id}/` | JWT Required | All |
| PUT | `/api/leave-management/applications/{id}/` | JWT Required | Owner/HR |
| PATCH | `/api/leave-management/applications/{id}/` | JWT Required | Owner/HR |
| DELETE | `/api/leave-management/applications/{id}/` | JWT Required | Owner/HR |

**Request Body (POST):**
```json
{
  "leave_type": "string",
  "start_date": "2023-12-01",
  "end_date": "2023-12-05",
  "reason": "string",
  "emergency_contact": "string",
  "attachments": ["file_urls"]
}
```

### Leave Application Approval
Approve/reject leave applications (HR/Manager only).

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| POST | `/api/leave-management/applications/{id}/approve/` | JWT Required | HR/Manager |
| POST | `/api/leave-management/bulk-approve/` | JWT Required | HR/Manager |

**Request Body:**
```json
{
  "action": "approve|reject",
  "comment": "string"
}
```

### Leave Comments & Attachments
Manage leave application comments and attachments.

| Method | Path | Authentication |
|--------|------|----------------|
| GET/POST | `/api/leave-management/applications/{leave_app_id}/comments/` | JWT Required |
| GET/POST | `/api/leave-management/applications/{leave_app_id}/attachments/` | JWT Required |

### Leave Types
Manage leave types and categories.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/leave-management/types/` | JWT Required | All |
| POST | `/api/leave-management/types/` | JWT Required | HR Only |
| GET | `/api/leave-management/types/{id}/` | JWT Required | All |
| PUT | `/api/leave-management/types/{id}/` | JWT Required | HR Only |
| PATCH | `/api/leave-management/types/{id}/` | JWT Required | HR Only |
| DELETE | `/api/leave-management/types/{id}/` | JWT Required | HR Only |

### Leave Balances
View leave balances and entitlements.

| Method | Path | Authentication | Description |
|--------|------|----------------|-------------|
| GET | `/api/leave-management/balances/` | JWT Required | All leave balances (HR) |
| GET | `/api/leave-management/my-balances/` | JWT Required | Current user balances |

### Leave Reports & Statistics

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/leave-management/my-summary/` | JWT Required | All |
| GET | `/api/leave-management/statistics/` | JWT Required | HR Only |

---

## ⏰ Attendance Management

### Time Tracking
Basic attendance operations.

| Method | Path | Authentication | Description |
|--------|------|----------------|-------------|
| POST | `/api/attendance-management/check-in/` | JWT Required | Employee check-in |
| POST | `/api/attendance-management/check-out/` | JWT Required | Employee check-out |
| POST | `/api/attendance-management/break/start/` | JWT Required | Start break |
| POST | `/api/attendance-management/break/end/` | JWT Required | End break |

### Attendance Records
View and manage attendance records.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/attendance-management/records/` | JWT Required | HR/Manager |
| GET | `/api/attendance-management/records/{id}/` | JWT Required | Owner/HR |
| PUT | `/api/attendance-management/records/{id}/` | JWT Required | HR Only |
| PATCH | `/api/attendance-management/records/{id}/` | JWT Required | HR Only |
| DELETE | `/api/attendance-management/records/{id}/` | JWT Required | HR Only |

### Personal Attendance
Employee's personal attendance data.

| Method | Path | Authentication | Description |
|--------|------|----------------|-------------|
| GET | `/api/attendance-management/my/history/` | JWT Required | Personal attendance history |
| GET | `/api/attendance-management/my/today/` | JWT Required | Today's attendance status |
| GET | `/api/attendance-management/my/summary/` | JWT Required | Personal attendance summary |

### Schedules & Policies
Manage work schedules and attendance policies.

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/attendance-management/schedules/` | JWT Required | All |
| GET | `/api/attendance-management/employee-schedules/` | JWT Required | All |
| POST | `/api/attendance-management/employee-schedules/` | JWT Required | HR Only |
| GET | `/api/attendance-management/policies/` | JWT Required | All |
| POST | `/api/attendance-management/policies/` | JWT Required | HR Only |

### Holidays & Reports

| Method | Path | Authentication | Permission |
|--------|------|----------------|------------|
| GET | `/api/attendance-management/holidays/` | JWT Required | All |
| POST | `/api/attendance-management/holidays/` | JWT Required | HR Only |
| GET | `/api/attendance-management/statistics/` | JWT Required | HR Only |
| GET | `/api/attendance-management/reports/generate/` | JWT Required | HR Only |

---

## 📊 Common Response Formats

### Success Response
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2",
  "created_at": "2023-12-02T10:30:00Z",
  "updated_at": "2023-12-02T10:30:00Z"
}
```

### List Response (Paginated)
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/endpoint/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "field1": "value1"
    }
  ]
}
```

### Error Response
```json
{
  "field_name": ["Error message for this field"],
  "non_field_errors": ["General error message"]
}
```

---

## 🔒 Permission Levels

| Permission | Description | Access |
|------------|-------------|---------|
| **None** | Public access | Login, Register endpoints |
| **JWT Required** | Authenticated users | Most endpoints |
| **HR Only** | HR role required | Employee management, admin functions |
| **Owner/HR** | Resource owner or HR | Personal data modification |
| **HR/Manager** | HR or Manager role | Approval workflows |

---

## 📝 Common Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search across multiple fields | `?search=john` |
| `page` | integer | Page number for pagination | `?page=2` |
| `page_size` | integer | Items per page | `?page_size=50` |
| `ordering` | string | Sort order | `?ordering=-created_at` |
| `department` | string | Filter by department | `?department=Engineering` |
| `active` | boolean | Filter by active status | `?active=true` |
| `start_date` | date | Start date filter | `?start_date=2023-12-01` |
| `end_date` | date | End date filter | `?end_date=2023-12-31` |

---

## 🛠️ Development Tools

### Swagger/OpenAPI Documentation
- **Swagger UI**: `http://localhost:8000/api/schema/swagger/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Example cURL Requests

**Login:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

**Authenticated Request:**
```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer your_access_token"
```

**Create Leave Application:**
```bash
curl -X POST http://localhost:8000/api/leave-management/applications/ \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type": "vacation",
    "start_date": "2023-12-15",
    "end_date": "2023-12-20",
    "reason": "Family vacation"
  }'
```

---

## 🔧 Error Handling

### HTTP Status Codes

| Code | Description | When |
|------|-------------|------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation errors |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server error |

### Common Error Scenarios

1. **Invalid Token**: Ensure access token is valid and not expired
2. **Permission Denied**: Check user role and permissions
3. **Validation Errors**: Review required fields and data formats
4. **Not Found**: Verify resource IDs and availability

---

## 📞 Support

For questions about this API:
1. Check the **Swagger UI** for interactive documentation
2. Review **error messages** for specific guidance
3. Verify **authentication tokens** and **permissions**
4. Ensure **request format** matches documentation

---

*Generated from OpenAPI 3.0.3 specification - Employee Management System API v1.0.0*