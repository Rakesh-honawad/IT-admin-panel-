from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    role: str = "Engineer"
    status: str = "active"  # active | inactive | pending

class License(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str
    user_email: str
    product: str
    assigned_on: str  # ISO date string

class SecurityRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    name: str
    sessions: int = 1
    mfa_enabled: bool = True
    status: str = "needs_review"  # secured | needs_review