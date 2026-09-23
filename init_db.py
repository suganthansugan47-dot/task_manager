"""
Creates the SQLite database and tables.
Run this once before starting the app for the first time:

    python init_db.py

Pass --demo to also create a sample login (demo / demo1234) with a few tasks,
handy for trying the app out immediately.
"""
import sys
from datetime import date, timedelta

from app import create_app
from extensions import db
from models import User, Task

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created.")

    if "--demo" in sys.argv:
        if User.query.filter_by(username="demo").first():
            print("Demo user already exists, skipping seed data.")
        else:
            demo_user = User(username="demo", email="demo@example.com")
            demo_user.set_password("demo1234")
            db.session.add(demo_user)
            db.session.flush()  # so demo_user.id is available below

            sample_tasks = [
                Task(
                    title="Set up the project",
                    description="Install dependencies and run the app locally.",
                    status="Completed",
                    priority="High",
                    due_date=date.today() - timedelta(days=1),
                    owner_id=demo_user.id,
                ),
                Task(
                    title="Design the dashboard layout",
                    description="Sketch the stats row and task list.",
                    status="In Progress",
                    priority="Medium",
                    due_date=date.today() + timedelta(days=2),
                    owner_id=demo_user.id,
                ),
                Task(
                    title="Write project README",
                    description="Explain setup and usage for new developers.",
                    status="Pending",
                    priority="Low",
                    due_date=date.today() + timedelta(days=7),
                    owner_id=demo_user.id,
                ),
            ]
            db.session.add_all(sample_tasks)
            db.session.commit()
            print("Demo user created -> username: demo | password: demo1234")
