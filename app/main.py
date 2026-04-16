from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from pathlib import Path
from datetime import date

from app.database import create_db, get_session
from app.models import User, License, SecurityRecord

app = FastAPI(title="IT Admin Agent")
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.on_event("startup")
def on_startup():
    create_db()

# ── Users ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/users", response_class=HTMLResponse)
async def users(request: Request, session: Session = Depends(get_session)):
    all_users = session.exec(select(User)).all()
    return templates.TemplateResponse("users.html", {"request": request, "users": all_users})

@app.post("/users/create")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form("Engineer"),
    session: Session = Depends(get_session)
):
    # Idempotent: don't duplicate
    existing = session.exec(select(User).where(User.email == email)).first()
    if not existing:
        user = User(name=name, email=email, role=role, status="active")
        session.add(user)
        session.commit()
        session.refresh(user)
        # Auto-create security record
        rec = SecurityRecord(user_id=user.id, name=name, sessions=0, mfa_enabled=False, status="needs_review")
        session.add(rec)
        session.commit()
    return RedirectResponse("/users", status_code=303)

@app.post("/users/disable/{user_id}")
async def disable_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user:
        user.status = "inactive"
        session.add(user)
        session.commit()
    return RedirectResponse("/users", status_code=303)

# ── Licenses ───────────────────────────────────────────
@app.get("/licenses", response_class=HTMLResponse)
async def licenses(request: Request, session: Session = Depends(get_session)):
    all_lics = session.exec(select(License)).all()
    return templates.TemplateResponse("licenses.html", {"request": request, "licenses": all_lics})

@app.post("/licenses/assign")
async def assign_license(
    email: str = Form(...),
    product: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == email)).first()
    name = user.name if user else email
    lic = License(user_name=name, user_email=email, product=product, assigned_on=str(date.today()))
    session.add(lic)
    session.commit()
    return RedirectResponse("/licenses", status_code=303)

@app.post("/licenses/revoke/{lic_id}")
async def revoke_license(lic_id: int, session: Session = Depends(get_session)):
    lic = session.get(License, lic_id)
    if lic:
        session.delete(lic)
        session.commit()
    return RedirectResponse("/licenses", status_code=303)

# ── Security ───────────────────────────────────────────
@app.get("/security", response_class=HTMLResponse)
async def security(request: Request, session: Session = Depends(get_session), msg: str = None):
    records = session.exec(select(SecurityRecord)).all()
    return templates.TemplateResponse("security.html", {
        "request": request,
        "security_records": records,
        "success_message": msg
    })

@app.post("/security/revoke-sessions/{user_id}")
async def revoke_sessions(user_id: int, session: Session = Depends(get_session)):
    rec = session.exec(select(SecurityRecord).where(SecurityRecord.user_id == user_id)).first()
    if rec:
        rec.sessions = 0
        session.add(rec)
        session.commit()
    return RedirectResponse(f"/security?msg=Sessions+revoked+for+user+{user_id}", status_code=303)

@app.post("/security/reset-mfa/{user_id}")
async def reset_mfa(user_id: int, session: Session = Depends(get_session)):
    rec = session.exec(select(SecurityRecord).where(SecurityRecord.user_id == user_id)).first()
    if rec:
        rec.mfa_enabled = False
        rec.status = "secured"
        session.add(rec)
        session.commit()
    return RedirectResponse(f"/security?msg=MFA+reset.+Account+Secured.", status_code=303)

@app.get("/health")
async def health():
    return {"status": "ok"}