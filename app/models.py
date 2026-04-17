from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

from sqlmodel import SQLModel, Field
from datetime import datetime

class AuditLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    action: str
    target: str
    performed_by: str
    details: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    role: str = "Engineer"
    status: str = "active"  

class License(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int   # MUST exist
    user_name: str
    user_email: str
    product: str
    assigned_on: str

class SecurityRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    name: str
    sessions: int = 1
    mfa_enabled: bool = True
    status: str = "needs_review"  