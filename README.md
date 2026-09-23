# Tasklog — Task Management Web App

A full-stack task manager: register, log in, and create/edit/delete your own
tasks from a dashboard with search, filters, and live stats.

## Tech stack (and why)

| Layer    | Choice                                   | Why |
|----------|-------------------------------------------|-----|
| Backend  | **Flask** (Python)                        | Small, readable, no heavy conventions to learn first — a few files and you can see exactly how a request flows in. |
| Database | **SQLite** via **Flask-SQLAlchemy** (ORM) | Zero setup (it's just a file), but you still write real relational models and queries through the ORM, which transfers directly to Postgres/MySQL later. |
| Auth     | **JWT** (PyJWT) + Werkzeug password hashing | The frontend is a separate set of static files talking to a JSON API, so a stateless token is simpler to reason about than server-side sessions/cookies — no CORS-with-cookies edge cases to debug. |
| Frontend | **Plain HTML / CSS / vanilla JavaScript** (`fetch`) | No build step, no framework concepts to learn before you can see a task on screen. Every line of markup and JS is something you can open and read top to bottom. |

This mirrors a standard "SPA-ish frontend + JSON API backend" architecture,
just without the frameworks — so the concepts (tokens, REST routes, ORM
models) carry over directly if you later move to React or a bigger backend
framework.

## Project structure

```
task-manager/
├── backend/
│   ├── app.py            # Flask app factory, blueprint registration, static file serving
│   ├── config.py         # Secret key, database URL, token expiry
│   ├── extensions.py     # The shared `db` (SQLAlchemy) instance
│   ├── models.py         # User and Task models
│   ├── auth.py           # /api/auth/* routes + the token_required decorator
│   ├── tasks.py          # /api/tasks/* routes (CRUD, filters, search, stats)
│   ├── init_db.py        # Run once to create the database (optionally with demo data)
│   └── requirements.txt
└── frontend/
    ├── index.html         # Redirects to login or dashboard
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── css/style.css
    └── js/
        ├── api.js         # fetch() wrapper: adds the auth token, handles 401s
        ├── auth.js        # Login / register form logic
        └── dashboard.js   # Stats, task list, filters/search, create/edit/delete modals
```

## Database schema

**users**

| column        | type          |
|---------------|---------------|
| id            | integer, PK   |
| username      | string, unique|
| email         | string, unique|
| password_hash | string        |
| created_at    | datetime      |

**tasks**

| column      | type                                   |
|-------------|-----------------------------------------|
| id          | integer, PK                             |
| title       | string                                  |
| description | text                                    |
| status      | string — `Pending` / `In Progress` / `Completed` |
| priority    | string — `Low` / `Medium` / `High`      |
| due_date    | date, nullable                          |
| created_at  | datetime                                |
| updated_at  | datetime                                |
| owner_id    | integer, FK → users.id                  |

One user has many tasks (`users.tasks`); each task belongs to exactly one
user (`tasks.owner_id`). Deleting a user deletes their tasks too.

## Setup and installation

### 1. Requirements
- Python 3.9+

### 2. Install backend dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create the database

```bash
python init_db.py
```

This creates `backend/taskmanager.db` (a SQLite file) with empty `users` and
`tasks` tables. To also get a ready-to-use login with a few sample tasks:

```bash
python init_db.py --demo
```

This creates a demo account:
- **username:** `demo`
- **password:** `demo1234`

### 4. Run the application

```bash
python app.py
```

The server starts on **http://127.0.0.1:5000**. Flask serves both the API
(under `/api/...`) and the frontend static files, so just open that URL in
your browser — no separate frontend server needed.

To start fresh, stop the server, delete `backend/taskmanager.db`, and re-run
`init_db.py`.

## API reference

All `/api/tasks/*` routes require the header `Authorization: Bearer <token>`,
obtained from `/api/auth/login` or `/api/auth/register`.

| Method | Route                  | Description                                    |
|--------|-------------------------|------------------------------------------------|
| POST   | `/api/auth/register`    | Create an account, returns a token             |
| POST   | `/api/auth/login`       | Log in, returns a token                        |
| POST   | `/api/auth/logout`      | Stateless no-op (see note below)                |
| GET    | `/api/auth/me`          | Current user's info                            |
| GET    | `/api/tasks`            | List your tasks. Query params: `status`, `priority`, `search` |
| GET    | `/api/tasks/stats`      | Counts by status, for the dashboard tiles      |
| POST   | `/api/tasks`            | Create a task                                  |
| GET    | `/api/tasks/<id>`       | Get one task (must be yours)                   |
| PUT    | `/api/tasks/<id>`       | Update a task (partial updates allowed; `PATCH` also works) |
| DELETE | `/api/tasks/<id>`       | Delete a task                                  |

**Status codes used:** `400` invalid input, `401` missing/expired/invalid
token, `403` the task exists but belongs to someone else, `404` the task
doesn't exist, `409` username/email already taken.

**A note on logout:** since auth is a stateless JWT, there's no server-side
session to destroy — "logging out" really just means the frontend deleting
its stored token, which `dashboard.js` does regardless of whether the
`/api/auth/logout` call succeeds. The endpoint exists mainly so the frontend
has a symmetrical call to make; a production app wanting true server-side
token revocation would add a blacklist table, which felt like more
complexity than this project needs.

## Trying it out

1. Run the app and open http://127.0.0.1:5000
2. Register a new account, or log in with the demo account (`demo` /
   `demo1234`) if you ran `init_db.py --demo`
3. Use **+ New task** to create a task, click the pencil icon to edit one,
   or the trash icon to delete one
4. Try the search box and the status/priority dropdowns to filter the list

## Notes on real-time updates

WebSockets weren't added. The dashboard already re-fetches tasks and stats
after every create/edit/delete, which covers the "see your own changes
immediately" case. Real-time sync *across multiple open tabs or devices*
would need a WebSocket (e.g. Flask-SocketIO) broadcasting task changes to
connected clients — a reasonable next step once the core CRUD is solid, but
it wasn't necessary for the app to work correctly, so it was left out per
the brief.
# task-manager
