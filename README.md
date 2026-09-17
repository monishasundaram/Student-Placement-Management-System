# Student Placement Management System

A full-stack CRUD web application for a college placement cell to manage
**students**, **companies**, and **placement drives** (applications and
offers). Built with a Flask + SQLite REST API backend and a vanilla
HTML/CSS/JavaScript frontend.

## 1. Problem statement

Placement cells track three related things every season: who the students
are, which companies are recruiting, and how each student's application
with each company is progressing (applied → shortlisted → selected /
rejected). This app gives a single dashboard to manage all three with full
Create, Read, Update, and Delete operations.

## 2. Technology stack

| Layer            | Technology                          |
|-------------------|--------------------------------------|
| Frontend          | HTML5, CSS3, vanilla JavaScript (fetch API) |
| Backend           | Python, Flask, Flask-SQLAlchemy, Flask-CORS |
| Database          | SQLite (file-based, zero setup)     |
| API style         | REST (JSON over HTTP)               |

No build step, no Node dependency, no framework install for the frontend —
open a file and it runs. The backend needs only Python + pip.

## 3. System architecture

```
Browser (index.html / style.css / script.js)
        │  fetch() — JSON over HTTP
        ▼
Flask REST API  (backend/app.py)
        │  SQLAlchemy ORM
        ▼
SQLite database (backend/placement.db, created automatically)
```

## 4. Data model (ER overview)

```
Student (1) ──< Placement >── (1) Company
```

- **Student**: id, roll_number (unique), name, email (unique), phone, branch, cgpa
- **Company**: id, name (unique), role, package_lpa, eligibility_cgpa, drive_date
- **Placement**: id, student_id (FK), company_id (FK), status
  (Applied / Shortlisted / Selected / Rejected), package_offered, placement_date

Deleting a student or company cascades and removes their related placement
records, so there are never orphaned rows.

## 5. Setup and execution

### Prerequisites
- Python 3.9+
- pip

### Step 1 — Start the backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API starts at **http://127.0.0.1:5000**. On first run it creates
`placement.db` automatically and seeds it with a few sample students,
companies, and placement records so the UI isn't empty. Delete
`placement.db` any time to reset to a blank database (it will reseed the
sample data on the next start — remove the `seed_sample_data()` call in
`app.py` if you don't want that).

### Step 2 — Start the frontend

The frontend is static, so any local web server works. From the
`frontend/` folder:

```bash
cd frontend
python3 -m http.server 8080
```

Then open **http://127.0.0.1:8080** in a browser. (Opening `index.html`
directly by double-clicking also works in most browsers, since the app
only talks to the API over `fetch`.)

> The frontend expects the API at `http://127.0.0.1:5000/api`. If you run
> the backend on a different host/port, update `API_BASE` at the top of
> `frontend/script.js`.

## 6. Using the app

- **Overview** — placement statistics: total students, companies, students
  placed, placement percentage, average and highest package.
- **Students** — add, search, filter by branch, edit, and delete students.
- **Companies** — add, search, edit, and delete recruiting companies.
- **Placement Drives** — log an application (pick a student + company),
  move it through statuses, record the offered package and date, edit or
  delete records.

All forms validate on the client (HTML5 `required`, number ranges) and
again on the server (duplicate roll numbers/emails, invalid email format,
CGPA range, valid status values, foreign key existence) — see
`docs/API_DOCUMENTATION.md` for exact rules and error responses.

## 7. Testing

The API was exercised manually with `curl` for each endpoint, covering:
- Successful create/read/update/delete for all three resources
- Missing required fields
- Invalid email format
- Duplicate roll number / email / company name
- Invalid foreign keys when logging a placement
- Empty vs. populated result sets

See `docs/API_DOCUMENTATION.md` for example requests/responses you can
replay in Postman.

## 8. Project structure

```
student-placement-management-system/
├── backend/
│   ├── app.py              REST API, models, validation, sample data seed
│   └── requirements.txt
├── frontend/
│   ├── index.html           App shell / views
│   ├── style.css            Visual design
│   └── script.js            API calls, rendering, forms
├── docs/
│   └── API_DOCUMENTATION.md
└── README.md
```

## 9. Security notes

- No secrets or credentials are hard-coded; SQLite needs none.
- All user input is validated server-side, independent of the frontend.
- CORS is enabled broadly for local development — restrict
  `CORS(app)` to a specific origin before deploying publicly.
- The Flask dev server (`app.run(debug=True)`) is for development only;
  use a production WSGI server (e.g. gunicorn) for deployment.

## 10. Future enhancements

- Authentication (placement-cell staff login) and role-based access
- Resume upload per student
- Email notifications on status change
- Pagination for large student/company lists
- Export placement report to PDF/Excel
