from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from pathlib import Path
from datetime import date
from fastapi import Query
from collections import defaultdict
from app.models import AuditLog
from app.database import create_db, get_session
from app.models import User, License, SecurityRecord

app = FastAPI(title="IT Admin Agent")
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.on_event("startup")
def on_startup():
    create_db()


# ── USERS ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/users", response_class=HTMLResponse)
async def users(
    request: Request,
    session: Session = Depends(get_session),
    q: str = Query(default=None)
):
    users_query = select(User)

    if q:
        users_query = users_query.where(User.name.contains(q) | User.email.contains(q))

    all_users = session.exec(users_query).all()

    # 🔥 user_licenses mapping
    licenses = session.exec(select(License)).all()
    user_licenses = defaultdict(list)

    for lic in licenses:
       user = session.exec(select(User).where(User.email == lic.user_email)).first()
       if user:
            user_licenses[user.id].append(lic.product)

    return templates.TemplateResponse("users.html", {
       "request": request,
       "users": all_users,
       "user_licenses": user_licenses,   
       "active": "users"
})


@app.post("/users/create")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form("Engineer"),
    session: Session = Depends(get_session)
):
    existing = session.exec(select(User).where(User.email == email)).first()

    if not existing:
        user = User(name=name, email=email, role=role, status="active")
        session.add(user)
        session.commit()
        session.refresh(user)

        rec = SecurityRecord(
            user_id=user.id,
            name=name,
            sessions=0,
            mfa_enabled=False,
            status="needs_review"
        )
        session.add(rec)
        session.commit()
        session.add(AuditLog(
            action="User Created",
            target=name,
            performed_by="Agent",
            details=email
        ))
        session.commit()    

    return RedirectResponse("/users", status_code=303)


@app.post("/users/{user_id}/disable")
async def disable_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user:
        user.status = "inactive"
        session.add(user)
        session.commit()
    session.add(AuditLog(
        action="User Disabled",
        target=user.name if user else "Unknown",
        performed_by="Agent",
        details="Account disabled"
    ))
    session.commit()    
    return RedirectResponse("/users", status_code=303)

@app.post("/users/{user_id}/enable")
async def enable_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if user:
        user.status = "active"
        session.add(user)
        session.commit()
    session.add(AuditLog(
        action="User Enabled",
        target=user.name if user else "Unknown",
        performed_by="Agent",
        details="Account enabled"
    ))
    session.commit()
    return RedirectResponse("/users", status_code=303)


# ── LICENSES ───────────────────────────────────────────
@app.get("/licenses", response_class=HTMLResponse)
async def licenses(request: Request, session: Session = Depends(get_session)):
    all_licenses = session.exec(select(License)).all()
    users = session.exec(select(User)).all()

    user_map = {u.id: u for u in users}

    summary = {}
    for lic in all_licenses:
        summary[lic.product] = summary.get(lic.product, 0) + 1

    products = ["GitHub Enterprise", "Slack Pro", "Figma Org", "AWS IAM", "Jira Cloud"]

    return templates.TemplateResponse("licenses.html", {
        "request": request,
        "all_licenses": all_licenses,
        "user_map": user_map,
        "summary": summary,
        "users": users,
        "products": products,
        "active": "licenses"
    })


@app.post("/licenses/assign")
async def assign_license(
    user_id: int = Form(...),
    product: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.get(User, user_id)

    if not user:
        return RedirectResponse("/licenses", status_code=303)

    lic = License(
        user_id=user.id,   
        user_name=user.name,
        user_email=user.email,
        product=product,
        assigned_on=str(date.today())
    )

    session.add(lic)
    session.commit()
    session.add(AuditLog(
        action="License Assigned",
        target=user.name if user else "Unknown",
        performed_by="Agent",
        details=product
   ))
    session.commit()

    return RedirectResponse("/licenses", status_code=303)

@app.post("/licenses/{lic_id}/revoke")
async def revoke_license(lic_id: int, session: Session = Depends(get_session)):
    lic = session.get(License, lic_id)

    if lic:
        session.delete(lic)
        session.commit()
    session.add(AuditLog(
        action="License Revoked",
        target=lic.user_name if lic else "Unknown",
        performed_by="Agent",
        details=lic.product if lic else ""
    ))
    session.commit()    

    return RedirectResponse("/licenses", status_code=303)


# ── SECURITY ───────────────────────────────────────────
@app.get("/security", response_class=HTMLResponse)
async def security(request: Request, session: Session = Depends(get_session), msg: str = None):
    records = session.exec(select(SecurityRecord)).all()

    return templates.TemplateResponse("security.html", {
        "request": request,
        "security_records": records,
        "msg": msg,
        "active": "security"
    })

@app.post("/security/revoke-sessions/{user_id}")
async def revoke_sessions(user_id: int, session: Session = Depends(get_session)):
    rec = session.exec(
        select(SecurityRecord).where(SecurityRecord.user_id == user_id)
    ).first()

    if rec:
        rec.sessions = 0

        if rec.sessions == 0 and rec.mfa_enabled:
            rec.status = "secured"

        session.add(rec)
        session.commit()

    user = session.get(User, user_id)

    session.add(AuditLog(
        action="Sessions Revoked",
        target=user.name if user else str(user_id),
        performed_by="Agent",
        details="All sessions cleared"
    ))
    session.commit()

    return RedirectResponse(f"/security?msg=Sessions+revoked+for+user+{user_id}", status_code=303)

@app.post("/security/reset-mfa/{user_id}")
async def reset_mfa(user_id: int, session: Session = Depends(get_session)):
    rec = session.exec(
        select(SecurityRecord).where(SecurityRecord.user_id == user_id)
    ).first()

    if rec:
        rec.mfa_enabled = True

        if rec.sessions == 0 and rec.mfa_enabled:
            rec.status = "secured"

        session.add(rec)
        session.commit()
    session.add(AuditLog(
        action="MFA Reset",
        target=str(user_id),
        performed_by="Agent",
        details="Account secured"
    ))
    session.commit()   

    return RedirectResponse("/security?msg=MFA+reset.+Account+Secured.", status_code=303)

@app.get("/audit", response_class=HTMLResponse)
async def audit(request: Request, session: Session = Depends(get_session)):
    logs = session.exec(select(AuditLog).order_by(AuditLog.id.desc())).all()

    return templates.TemplateResponse("audit.html", {
        "request": request,
        "logs": logs
    })

@app.get("/health")
async def health():
    return {"status": "ok"}