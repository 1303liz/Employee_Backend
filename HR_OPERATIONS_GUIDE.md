# HR Operations Guide - Employee Management System

## 🔐 HR Login & Access

### How HR Logs In
1. **Navigate to Login Page**: `http://localhost:5173/login`
2. **Enter HR Credentials**:
   - Username: Your HR username
   - Password: Your HR password
3. **System Automatically Identifies HR Role**: The backend checks `user.role === 'HR'` or `user.is_hr === True`
4. **Redirects to Dashboard**: After successful login, you're redirected to `/dashboard`

### HR Role Verification
The system uses JWT tokens and role-based permissions:
- **Backend**: `IsHRPermission` class checks `request.user.is_authenticated` and `request.user.is_hr`
- **Frontend**: Routes check `user?.role === 'HR'` to show/hide HR-only features

---

## 📋 CRUD Operations for HR

### 1️⃣ **CREATE - Add New Employee**

#### Frontend Access:
- **Dashboard**: Click "➕ Add Employee" quick action button
- **Employees Page**: Click "Add Employee" button in header
- **Direct URL**: `http://localhost:5173/employees/add`

#### Steps:
1. Navigate to Add Employee page
2. Fill in the form:
   - **Basic Info**: First Name, Last Name, Username, Email
   - **Employment**: Employee ID, Department, Position, Hire Date
   - **Contact**: Phone Number, Address
   - **Authentication**: Password (required for new employee login)
3. Click "Add Employee" button
4. System creates user account and sends success notification

#### Backend API:
```http
POST /api/employees/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user": {
    "username": "john_doe",
    "email": "john@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepass123",
    "role": "EMPLOYEE",
    "employee_id": "EMP001",
    "department": "Engineering",
    "phone_number": "+1234567890",
    "hire_date": "2024-01-15"
  }
}
```

**Response**: Returns created employee data with auto-generated profile

---

### 2️⃣ **READ - View Employees**

#### Frontend Access:
- **Dashboard**: View stats showing total employees
- **Employees List**: `http://localhost:5173/employees`
- **Employee Details**: Click on any employee card

#### Features:
- **Search**: Search by name, email, department, username
- **Filter**: Filter by department, position, status, employment type
- **Employee Cards**: Display profile photo, name, role, department, contact info

#### Backend APIs:

**List All Employees:**
```http
GET /api/employees/?search=john&department=Engineering
Authorization: Bearer {jwt_token}
```

**Get Single Employee:**
```http
GET /api/employees/{employee_id}/
Authorization: Bearer {jwt_token}
```

**Response**: Returns employee profile with user details, documents, notes

---

### 3️⃣ **UPDATE - Edit Employee Information**

#### Frontend Access:
- **Employees List**: Click employee card → Click "Edit" button
- **Profile Page**: Click "Edit Profile" button
- **Direct URL**: `http://localhost:5173/employees/edit/{id}`

#### What HR Can Update:
- ✅ First Name, Last Name
- ✅ Email Address
- ✅ Employee ID
- ✅ Department
- ✅ Position
- ✅ Phone Number
- ✅ Hire Date
- ✅ Employment Status (Active, On Leave, Terminated)
- ✅ Employment Type (Full-time, Part-time, Contract)
- ✅ Address
- ✅ Emergency Contacts
- ✅ Salary (if implemented)

#### Steps:
1. Navigate to employee's edit page
2. Modify the desired fields
3. Click "Save Changes" or "Update Employee"
4. System validates and updates the record

#### Backend API:
```http
PUT /api/employees/{employee_id}/
or
PATCH /api/employees/{employee_id}/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user": {
    "first_name": "John",
    "last_name": "Smith",
    "department": "Sales",
    "phone_number": "+1234567891"
  }
}
```

**PATCH** allows partial updates (only modified fields)

---

### 4️⃣ **DELETE - Remove/Terminate Employee**

#### Frontend Access:
- **Employees List**: Click employee card → Click "Delete" button
- **Edit Employee Page**: "Delete Employee" button at bottom

#### Important Notes:
⚠️ **Soft Delete Implementation**:
- System does NOT permanently delete employee records
- Instead, it marks employee as TERMINATED
- Sets `user.is_active = False`
- Preserves all historical data for compliance

#### Steps:
1. Navigate to employee's details/edit page
2. Click "Delete" or "Terminate Employee" button
3. **Confirmation Dialog** appears (prevents accidental deletion)
4. Confirm the action
5. Employee status changes to "Terminated" and account is deactivated

#### Backend API:
```http
DELETE /api/employees/{employee_id}/
Authorization: Bearer {jwt_token}
```

**Response**: Soft deletes by updating status:
```json
{
  "message": "Employee deactivated successfully",
  "employee_id": 123,
  "status": "TERMINATED"
}
```

---

## 📝 Leave Management (Approve/Reject)

### Frontend Access:
- **Dashboard**: Click "✅ Manage Leaves" quick action
- **Direct URL**: `http://localhost:5173/leaves/manage`

### Operations:

#### View All Leave Requests:
1. Navigate to Manage Leaves page
2. See table with columns:
   - Employee Name
   - Leave Type (Sick, Casual, Annual)
   - Start Date & End Date
   - Reason
   - Status (Pending/Approved/Rejected)
   - Action Buttons

#### Approve Leave:
1. Find leave request with "PENDING" status
2. Click **"Approve"** button (green)
3. Status changes to "APPROVED"
4. Employee receives notification

#### Reject Leave:
1. Find leave request with "PENDING" status
2. Click **"Reject"** button (red)
3. Status changes to "REJECTED"
4. Employee receives notification

### Backend API:
```http
GET /api/leave/
Authorization: Bearer {jwt_token}
```

**Update Leave Status:**
```http
PATCH /api/leave/{leave_id}/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "status": "APPROVED"  // or "REJECTED"
}
```

---

## 🔍 Search & Filter Capabilities

### Employee Search:
```javascript
// Frontend searches by:
- Full Name (first + last)
- Email
- Department
- Username
- Employee ID
```

### Backend Query Parameters:
```http
GET /api/employees/?search=john
GET /api/employees/?department=Engineering
GET /api/employees/?position=Developer
GET /api/employees/?status=ACTIVE
GET /api/employees/?employment_type=FULL_TIME
```

---

## 🛡️ Security & Permissions

### HR-Only Features Protected:
✅ Add Employee  
✅ Edit Any Employee  
✅ Delete/Terminate Employee  
✅ View All Employees  
✅ Approve/Reject Leaves  
✅ View Dashboard Statistics  

### Backend Permission Class:
```python
class IsHRPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_hr
```

### Frontend Route Protection:
```javascript
// Only HR can access these routes
<Route path="/employees" element={<ProtectedRoute><EmployeeList /></ProtectedRoute>} />
<Route path="/employees/add" element={<ProtectedRoute><AddEmployee /></ProtectedRoute>} />
<Route path="/employees/edit/:id" element={<ProtectedRoute><EditEmployee /></ProtectedRoute>} />
<Route path="/leaves/manage" element={<ProtectedRoute><ManageLeave /></ProtectedRoute>} />
```

---

## 📊 Dashboard Statistics (HR View)

HR users see additional dashboard stats:
- **Total Employees**: Count of all active employees
- **Pending Leaves**: Leaves awaiting approval
- **Today's Attendance**: Employees who checked in today
- **Attendance Rate**: Percentage of attendance

---

## 🚀 Quick Reference - HR Daily Workflow

### Morning Routine:
1. **Login** to system
2. **Check Dashboard** for pending actions
3. **Review Attendance** - see who's checked in
4. **Approve/Reject Leaves** - process pending requests

### Adding New Employee:
1. Dashboard → "Add Employee"
2. Fill form with employee details
3. Set initial password (employee should change on first login)
4. Save and notify employee

### Managing Employee Data:
1. Go to "Employees" page
2. Search/filter to find employee
3. Click employee card
4. Click "Edit" button
5. Update information
6. Save changes

### Handling Terminations:
1. Find employee in list
2. Click "Edit" → "Delete Employee"
3. Confirm termination
4. Employee account deactivated (soft delete)
5. Historical data preserved

---

## 📞 Support & Troubleshooting

### Common Issues:

**Can't see HR features?**
- Verify user role is set to "HR" in database
- Check `is_hr` field is `True`
- Re-login to refresh JWT token

**Permission Denied Errors?**
- Ensure JWT token is valid
- Check Authorization header is set
- Verify HR role in user profile

**Employee not showing in list?**
- Check employee's `is_active` status
- Verify role is "EMPLOYEE" not "HR"
- Check search/filter parameters

---

## 🔗 API Endpoints Summary

| Operation | Method | Endpoint | Permission |
|-----------|--------|----------|------------|
| List Employees | GET | `/api/employees/` | HR Only |
| Add Employee | POST | `/api/employees/` | HR Only |
| View Employee | GET | `/api/employees/{id}/` | HR Only |
| Update Employee | PATCH/PUT | `/api/employees/{id}/` | HR Only |
| Delete Employee | DELETE | `/api/employees/{id}/` | HR Only |
| List Leaves | GET | `/api/leave/` | HR Only |
| Update Leave | PATCH | `/api/leave/{id}/` | HR Only |
| Dashboard Stats | GET | `/api/accounts/dashboard-stats/` | HR Only |

---

## 📝 Notes

- All CRUD operations require authentication (JWT token)
- HR role is verified on both frontend and backend
- Employee deletion is SOFT DELETE (preserves data)
- Leave status can only be changed by HR
- Profile photos and documents can be uploaded via multipart form data
- All dates should be in ISO format: `YYYY-MM-DD`
