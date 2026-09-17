# API Documentation

Base URL (local development): `http://127.0.0.1:5000/api`

All request and response bodies are JSON. All list/detail endpoints end
with a trailing slash.

---

## Students

### List students
`GET /students/`
Query params (optional): `search` (matches name, roll number, or email),
`branch` (exact match)

```
GET /api/students/?search=aarav&branch=Computer%20Science
```

**200 OK**
```json
[
  {
    "id": 1,
    "roll_number": "CS001",
    "name": "Aarav Sharma",
    "email": "aarav.sharma@example.com",
    "phone": "9876543210",
    "branch": "Computer Science",
    "cgpa": 8.7,
    "created_at": "2026-08-01T10:00:00"
  }
]
```

### Get one student
`GET /students/{id}/` → 200 OK with student object, or 404 if not found.

### Create student
`POST /students/`

```json
{
  "roll_number": "CS010",
  "name": "New Student",
  "email": "new.student@example.com",
  "phone": "9876500000",
  "branch": "Computer Science",
  "cgpa": 8.2
}
```
- **201 Created** — returns the created student.
- **400** — missing required field, invalid email format, or CGPA outside 0–10.
- **409** — roll number or email already exists.

### Update student
`PUT /students/{id}/` or `PATCH /students/{id}/` — send any subset of the
create fields. Same validation rules apply. Returns **200 OK** with the
updated student, **404** if not found.

### Delete student
`DELETE /students/{id}/` → **200 OK** `{"message": "Student deleted successfully"}`,
or **404** if not found. Also deletes that student's placement records.

---

## Companies

### List companies
`GET /companies/` — optional `search` query param (matches company name or role).

### Get one company
`GET /companies/{id}/`

### Create company
`POST /companies/`

```json
{
  "name": "Acme Corp",
  "role": "Software Engineer",
  "package_lpa": 10.5,
  "eligibility_cgpa": 7.0,
  "drive_date": "2026-11-15"
}
```
- **201 Created**. `eligibility_cgpa` and `drive_date` are optional.
- **400** — missing required field, non-numeric/negative package.
- **409** — a company with this name already exists.

### Update company
`PUT /companies/{id}/` or `PATCH /companies/{id}/` — partial updates allowed.

### Delete company
`DELETE /companies/{id}/` — also deletes related placement records.

---

## Placements (applications / drive tracking)

### List placements
`GET /placements/` — optional `status` filter
(`Applied` | `Shortlisted` | `Selected` | `Rejected`).

```json
[
  {
    "id": 4,
    "student_id": 1,
    "student_name": "Aarav Sharma",
    "company_id": 1,
    "company_name": "TechNova Solutions",
    "status": "Selected",
    "package_offered": 12.0,
    "placement_date": "2026-08-12",
    "created_at": "2026-08-01T10:00:00"
  }
]
```

### Get one placement
`GET /placements/{id}/`

### Create placement (log an application)
`POST /placements/`

```json
{
  "student_id": 1,
  "company_id": 2,
  "status": "Applied"
}
```
- `student_id` and `company_id` are required and must reference existing
  records (**404** if not).
- `status` defaults to `Applied` if omitted; must be one of the four valid
  values (**400** otherwise).
- `package_offered` and `placement_date` are optional.
- **201 Created** on success.

### Update placement
`PUT /placements/{id}/` or `PATCH /placements/{id}/` — typically used to
move status forward (e.g. `Applied` → `Shortlisted` → `Selected`) and set
`package_offered` / `placement_date` once an offer is made.

### Delete placement
`DELETE /placements/{id}/`

---

## Dashboard

### Summary statistics
`GET /dashboard/`

```json
{
  "total_students": 5,
  "total_companies": 3,
  "total_placements": 4,
  "students_selected": 2,
  "placement_percentage": 40.0,
  "average_package_lpa": 13.5,
  "highest_package_lpa": 15.0
}
```

---

## Error format

All errors return a JSON body with an `error` field:

```json
{ "error": "Invalid email format" }
```

| Status | Meaning |
|--------|---------|
| 400 | Validation failed (missing/invalid field) |
| 404 | Resource not found |
| 409 | Conflict — duplicate unique value (roll number, email, company name) |
| 500 | Unexpected server error |

## Manual test cases run against this API

| # | Test | Method & endpoint | Expected result | Result |
|---|------|--------------------|------------------|--------|
| 1 | Create valid student | POST /students/ | 201, student returned | ✅ |
| 2 | Create student, invalid email | POST /students/ | 400, "Invalid email format" | ✅ |
| 3 | Create student, duplicate roll number | POST /students/ | 409 | ✅ |
| 4 | Read all students (populated) | GET /students/ | 200, array | ✅ |
| 5 | Update student CGPA | PATCH /students/{id}/ | 200, updated value | ✅ |
| 6 | Delete existing student | DELETE /students/{id}/ | 200 | ✅ |
| 7 | Delete non-existent student | DELETE /students/9999/ | 404 | ✅ |
| 8 | Create placement with valid student & company | POST /placements/ | 201 | ✅ |
| 9 | Create placement with invalid student_id | POST /placements/ | 404 | ✅ |
| 10 | Dashboard stats reflect current data | GET /dashboard/ | 200, correct counts | ✅ |
