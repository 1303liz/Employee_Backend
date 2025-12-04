# Reports and Analytics API Documentation

This document describes the comprehensive reporting and analytics endpoints for attendance and leave management, designed for employee performance tracking and HR appraisals.

## Table of Contents
1. [Attendance Reports](#attendance-reports)
2. [Leave Reports](#leave-reports)
3. [Performance Reports](#performance-reports)
4. [Usage Examples](#usage-examples)

---

## Attendance Reports

### 1. Employee Attendance Report
**Endpoint:** `GET /api/attendance-management/reports/employee/`

**Access:** Authenticated users (employees can view only their own, HR can view any)

**Parameters:**
- `employee_id` (optional): Employee ID (if not provided, returns current user's report)
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to 30 days ago
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today

**Response:**
```json
{
  "employee": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "EMPLOYEE"
  },
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-12-03",
    "total_days": 33
  },
  "attendance_summary": {
    "present_days": 28,
    "absent_days": 2,
    "late_days": 3,
    "half_days": 1,
    "on_time_days": 25,
    "attendance_rate": 84.85,
    "punctuality_rate": 89.29
  },
  "hours_summary": {
    "total_hours_worked": 224.0,
    "total_overtime": 12.5,
    "average_daily_hours": 8.0
  },
  "break_summary": {
    "total_breaks_taken": 42,
    "total_break_duration": 21.0,
    "average_break_duration": 0.5
  },
  "performance_metrics": {
    "consistency_score": 84.85,
    "reliability_score": 75.76
  },
  "detailed_records": [...]
}
```

### 2. Team Attendance Report
**Endpoint:** `GET /api/attendance-management/reports/team/`

**Access:** HR only

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to 30 days ago
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today
- `department` (optional): Filter by department name

**Response:**
```json
{
  "period": {
    "start_date": "2025-11-01",
    "end_date": "2025-12-03",
    "total_days": 33
  },
  "team_summary": {
    "total_employees": 25,
    "average_attendance_rate": 87.5,
    "average_hours_worked": 220.5,
    "total_overtime_hours": 145.0
  },
  "employee_details": [
    {
      "employee_id": 1,
      "employee_name": "John Doe",
      "email": "john@example.com",
      "department": "Engineering",
      "present_days": 28,
      "absent_days": 2,
      "late_days": 3,
      "attendance_rate": 84.85,
      "total_hours": 224.0,
      "overtime_hours": 12.5,
      "performance_score": 81.85
    }
  ]
}
```

### 3. Attendance Analytics
**Endpoint:** `GET /api/attendance-management/reports/analytics/`

**Access:** HR only

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to 90 days ago
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today

**Response:**
```json
{
  "period": {
    "start_date": "2025-09-01",
    "end_date": "2025-12-03"
  },
  "overview": {
    "total_records": 750,
    "unique_employees": 25
  },
  "status_distribution": [
    {"status": "PRESENT", "count": 625},
    {"status": "LATE", "count": 75},
    {"status": "ABSENT", "count": 40},
    {"status": "HALF_DAY", "count": 10}
  ],
  "daily_trends": [...],
  "department_analysis": [
    {
      "department": "Engineering",
      "total_records": 300,
      "present_count": 265,
      "attendance_rate": 88.33
    }
  ],
  "top_performers": [
    {
      "employee_name": "Alice Johnson",
      "attendance_rate": 98.5,
      "present_days": 88
    }
  ]
}
```

---

## Leave Reports

### 4. Employee Leave Report
**Endpoint:** `GET /api/leave-management/reports/employee/`

**Access:** Authenticated users (employees can view only their own, HR can view any)

**Parameters:**
- `employee_id` (optional): Employee ID (if not provided, returns current user's report)
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `year` (optional): Year (YYYY), overrides start_date and end_date

**Response:**
```json
{
  "employee": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "EMPLOYEE"
  },
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  },
  "summary": {
    "total_applications": 8,
    "approved_applications": 7,
    "pending_applications": 1,
    "rejected_applications": 0,
    "total_days_taken": 15,
    "average_leave_duration": 2.14
  },
  "status_breakdown": {
    "pending": 1,
    "approved": 7,
    "rejected": 0,
    "cancelled": 0,
    "total": 8
  },
  "leave_type_breakdown": [
    {
      "leave_type": "Annual Leave",
      "total_allocated": 20,
      "days_used": 10,
      "days_remaining": 10,
      "applications_count": 4,
      "pending_count": 0,
      "utilization_rate": 50.0
    },
    {
      "leave_type": "Sick Leave",
      "total_allocated": 15,
      "days_used": 5,
      "days_remaining": 10,
      "applications_count": 3,
      "pending_count": 1,
      "utilization_rate": 33.33
    }
  ],
  "monthly_distribution": {
    "January": {"count": 1, "days": 3},
    "February": {"count": 0, "days": 0},
    ...
  },
  "recent_applications": [...],
  "performance_metrics": {
    "leave_utilization": 41.67,
    "planning_score": 87.5
  }
}
```

### 5. Team Leave Report
**Endpoint:** `GET /api/leave-management/reports/team/`

**Access:** HR only

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `year` (optional): Year (YYYY), overrides start_date and end_date
- `department` (optional): Filter by department name

**Response:**
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  },
  "team_summary": {
    "total_employees": 25,
    "total_leave_applications": 200,
    "total_days_taken": 425,
    "average_utilization": 68.5,
    "pending_applications": 12
  },
  "leave_type_distribution": [
    {
      "leave_type__name": "Annual Leave",
      "count": 95,
      "total_days": 230
    },
    {
      "leave_type__name": "Sick Leave",
      "count": 75,
      "total_days": 150
    }
  ],
  "employee_details": [
    {
      "employee_id": 1,
      "employee_name": "John Doe",
      "email": "john@example.com",
      "department": "Engineering",
      "total_applications": 8,
      "approved_applications": 7,
      "pending_applications": 1,
      "days_taken": 15,
      "days_allocated": 35,
      "days_remaining": 20,
      "utilization_rate": 42.86
    }
  ]
}
```

### 6. Leave Analytics
**Endpoint:** `GET /api/leave-management/reports/analytics/`

**Access:** HR only

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD), defaults to start of current year
- `end_date` (optional): End date (YYYY-MM-DD), defaults to today

**Response:**
```json
{
  "period": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-03"
  },
  "overview": {
    "total_applications": 200,
    "approved_applications": 175,
    "pending_applications": 15,
    "rejection_rate": 5.0,
    "average_approval_time_days": 2.5
  },
  "status_distribution": [...],
  "leave_type_analysis": [
    {
      "leave_type__name": "Annual Leave",
      "count": 95,
      "total_days": 230,
      "avg_duration": 2.42
    }
  ],
  "monthly_trends": {
    "January": {
      "applications": 15,
      "approved": 14,
      "days_taken": 35
    },
    ...
  },
  "department_analysis": [
    {
      "department": "Engineering",
      "total_applications": 80,
      "approved_applications": 72,
      "total_days_taken": 180,
      "approval_rate": 90.0
    }
  ],
  "top_leave_takers": [
    {
      "employee_name": "John Doe",
      "leave_applications": 12,
      "total_days_taken": 25
    }
  ]
}
```

---

## Performance Reports

### 7. Combined Performance Report
**Endpoint:** `GET /api/leave-management/reports/performance/`

**Access:** HR only (designed for employee appraisals)

**Parameters:**
- `employee_id` (required): Employee ID
- `year` (optional): Year (YYYY), defaults to current year

**Response:**
```json
{
  "employee": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "department": "Engineering"
  },
  "period": {
    "year": 2025,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31"
  },
  "attendance_metrics": {
    "total_working_days": 365,
    "present_days": 310,
    "absent_days": 8,
    "late_days": 15,
    "attendance_rate": 84.93,
    "punctuality_rate": 95.16,
    "total_hours_worked": 2480.0,
    "overtime_hours": 120.5,
    "average_daily_hours": 8.0
  },
  "leave_metrics": {
    "total_leave_applications": 8,
    "approved_leaves": 7,
    "rejected_leaves": 0,
    "total_leave_days_taken": 15,
    "leave_planning_score": 87.5
  },
  "performance_summary": {
    "attendance_score": 84.93,
    "punctuality_score": 95.16,
    "leave_planning_score": 87.5,
    "overall_performance_score": 88.37,
    "performance_rating": "Very Good"
  },
  "recommendations": [
    {
      "category": "Punctuality",
      "severity": "medium",
      "message": "Work on improving punctuality (95.16%). Reduce late arrivals."
    }
  ]
}
```

**Performance Ratings:**
- **Excellent**: Score ≥ 90
- **Very Good**: Score ≥ 80
- **Good**: Score ≥ 70
- **Satisfactory**: Score ≥ 60
- **Needs Improvement**: Score < 60

**Scoring Breakdown:**
- Attendance Score: 40% weight
- Punctuality Score: 30% weight
- Leave Planning Score: 20% weight
- Overtime Contribution: 10% weight

---

## Usage Examples

### Example 1: Get Your Own Attendance Report
```bash
curl -X GET "http://127.0.0.1:8000/api/attendance-management/reports/employee/?start_date=2025-11-01&end_date=2025-12-03" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example 2: HR Views Employee Attendance
```bash
curl -X GET "http://127.0.0.1:8000/api/attendance-management/reports/employee/?employee_id=5&start_date=2025-11-01" \
  -H "Authorization: Bearer HR_ACCESS_TOKEN"
```

### Example 3: Get Team Leave Report for Current Year
```bash
curl -X GET "http://127.0.0.1:8000/api/leave-management/reports/team/?year=2025" \
  -H "Authorization: Bearer HR_ACCESS_TOKEN"
```

### Example 4: Generate Performance Report for Appraisal
```bash
curl -X GET "http://127.0.0.1:8000/api/leave-management/reports/performance/?employee_id=5&year=2025" \
  -H "Authorization: Bearer HR_ACCESS_TOKEN"
```

### Example 5: Get Department-wise Analytics
```bash
curl -X GET "http://127.0.0.1:8000/api/attendance-management/reports/analytics/?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer HR_ACCESS_TOKEN"
```

---

## Frontend Integration Guide

### React Example - Fetch Employee Report
```javascript
import api from './services/api';

const fetchEmployeeReport = async (employeeId, startDate, endDate) => {
  try {
    const response = await api.get('/attendance-management/reports/employee/', {
      params: { employee_id: employeeId, start_date: startDate, end_date: endDate }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching report:', error);
    throw error;
  }
};

// Usage
const report = await fetchEmployeeReport(null, '2025-11-01', '2025-12-03');
console.log('Attendance Rate:', report.attendance_summary.attendance_rate);
```

### React Example - Generate Performance Report
```javascript
const generatePerformanceReport = async (employeeId, year) => {
  try {
    const response = await api.get('/leave-management/reports/performance/', {
      params: { employee_id: employeeId, year: year }
    });
    return response.data;
  } catch (error) {
    console.error('Error generating performance report:', error);
    throw error;
  }
};

// Usage for appraisal
const performanceData = await generatePerformanceReport(5, 2025);
console.log('Overall Score:', performanceData.performance_summary.overall_performance_score);
console.log('Rating:', performanceData.performance_summary.performance_rating);
console.log('Recommendations:', performanceData.recommendations);
```

---

## Notes

1. **Access Control:**
   - Employees can view their own reports
   - HR can view all reports and analytics
   - Team reports and analytics are HR-only

2. **Date Formats:**
   - All dates should be in `YYYY-MM-DD` format
   - Times are in ISO 8601 format

3. **Performance Metrics:**
   - Scores are calculated on a 0-100 scale
   - All rates are percentages rounded to 2 decimal places
   - Hours are rounded to 2 decimal places

4. **Best Practices:**
   - Use year parameter for annual reviews
   - Use date ranges for custom period analysis
   - Cache reports for frequently accessed data
   - Export to CSV/PDF in frontend for offline viewing

5. **Rate Limiting:**
   - Consider implementing rate limiting for analytics endpoints
   - Cache results for heavy queries

---

## Future Enhancements

- Export to PDF/CSV
- Scheduled report generation
- Email report delivery
- Comparative analysis (year-over-year)
- Predictive analytics
- Custom report builder
