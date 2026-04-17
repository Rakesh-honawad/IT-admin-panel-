from sqlmodel import Session, select
from app.database import engine, create_db
from app.models import User, License, SecurityRecord
from datetime import date

def seed():
    create_db()
    with Session(engine) as s:
        if s.exec(select(User)).first():
            print("Already seeded.")
            return

        # Create users one by one so we can get their IDs
        u1 = User(name="Alice Chen",   email="alice.chen@company.com",   role="Engineer", status="Active")
        u2 = User(name="Bob Martinez", email="bob.martinez@company.com",  role="Manager",  status="Active")
        u3 = User(name="Carol White",  email="carol.white@company.com",   role="Designer", status="Active")

        s.add(u1); s.add(u2); s.add(u3)
        s.commit()

        # Refresh to get auto-assigned IDs
        s.refresh(u1); s.refresh(u2); s.refresh(u3)

        licenses = [
            License(user_id=u1.id, user_name=u1.name, user_email=u1.email, product="GitHub Enterprise", assigned_on=str(date.today())),
            License(user_id=u2.id, user_name=u2.name, user_email=u2.email, product="Slack Pro",         assigned_on=str(date.today())),
        ]
        for l in licenses:
            s.add(l)
        s.commit()

        records = [
            SecurityRecord(user_id=u1.id, name=u1.name, sessions=2, mfa_enabled=True,  status="secured"),
            SecurityRecord(user_id=u2.id, name=u2.name, sessions=4, mfa_enabled=False, status="needs_review"),
            SecurityRecord(user_id=u3.id, name=u3.name, sessions=1, mfa_enabled=False, status="needs_review"),
        ]
        for r in records:
            s.add(r)
        s.commit()
        print("Seeded successfully.")

if __name__ == "__main__":
    seed()