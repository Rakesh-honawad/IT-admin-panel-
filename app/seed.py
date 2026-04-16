from sqlmodel import Session
from app.database import engine, create_db
from app.models import User, License, SecurityRecord
from datetime import date

def seed():
    create_db()
    with Session(engine) as s:
        # Skip if already seeded
        from sqlmodel import select
        if s.exec(select(User)).first():
            print("Already seeded.")
            return

        users = [
            User(name="Alice Chen",   email="alice.chen@company.com",   role="Engineer", status="active"),
            User(name="Bob Martinez", email="bob.martinez@company.com",  role="Manager",  status="active"),
            User(name="Carol White",  email="carol.white@company.com",   role="Designer", status="inactive"),
        ]
        for u in users:
            s.add(u)
        s.commit()

        licenses = [
            License(user_name="Alice Chen",   user_email="alice.chen@company.com",   product="GitHub Enterprise", assigned_on=str(date.today())),
            License(user_name="Bob Martinez", user_email="bob.martinez@company.com",  product="Slack Pro",         assigned_on=str(date.today())),
        ]
        for l in licenses:
            s.add(l)
        s.commit()

        records = [
            SecurityRecord(user_id=1, name="Alice Chen",   sessions=2, mfa_enabled=True,  status="secured"),
            SecurityRecord(user_id=2, name="Bob Martinez", sessions=4, mfa_enabled=False, status="needs_review"),
            SecurityRecord(user_id=3, name="Carol White",  sessions=1, mfa_enabled=False, status="needs_review"),
        ]
        for r in records:
            s.add(r)
        s.commit()
        print("Seeded successfully.")

if __name__ == "__main__":
    seed()