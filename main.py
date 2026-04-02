from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./zorvyn_finance.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    role = Column(String)  # Admin, Analyst, Viewer
    status = Column(String, default="active")

class DBTransaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    type = Column(String)  # income / expense
    category = Column(String)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    type: str 
    category: str
    description: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    role: str 

# --- APP & DEPENDENCIES ---
app = FastAPI(title="Zorvyn Finance Backend", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_access(user_id: int, allowed_roles: List[str], db: Session):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="User account is inactive")
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Access denied for role: {user.role}")
    return user

# --- ENDPOINTS ---

@app.post("/users", tags=["Admin"])
def create_user(user: UserCreate, db: Session = Depends(get_db), admin_id: Optional[int] = Query(None)):
    # Check if any users exist in the DB
    user_count = db.query(DBUser).count()
    
    # If users exist, enforce Admin check. If no users exist, let the first one through.
    if user_count > 0:
        if admin_id is None:
             raise HTTPException(status_code=403, detail="admin_id required")
        verify_access(admin_id, ["Admin"], db)
    
    db_user = DBUser(username=user.username, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/transactions", tags=["Finance"])
def add_transaction(data: TransactionCreate, user_id: int, db: Session = Depends(get_db)):
    verify_access(user_id, ["Admin", "Analyst"], db)
    
    new_tx = DBTransaction(
        amount=data.amount,
        type=data.type,
        category=data.category,
        description=data.description
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx

@app.get("/summary", tags=["Dashboard"])
def get_dashboard_summary(user_id: int, db: Session = Depends(get_db)):
    verify_access(user_id, ["Admin", "Analyst", "Viewer"], db)
    
    income = db.query(func.sum(DBTransaction.amount)).filter(DBTransaction.type == "income").scalar() or 0
    expense = db.query(func.sum(DBTransaction.amount)).filter(DBTransaction.type == "expense").scalar() or 0
    cat_totals = db.query(DBTransaction.category, func.sum(DBTransaction.amount)).group_by(DBTransaction.category).all()
    
    return {
        "total_income": income,
        "total_expenses": expense,
        "net_balance": income - expense,
        "category_wise": {cat: amt for cat, amt in cat_totals}
    }
