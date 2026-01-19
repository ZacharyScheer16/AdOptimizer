import os
import io
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, security
from .database import engine, get_db, Base
from .model import run_clustering, calculate_savings

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- ENDPOINT 1: UPLOAD & AUTO-SAVE ---
@app.post("/upload-logistics")
async def upload_data(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # 1. AI Analysis
        result = run_clustering(df)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        # 2. Calculate Values
        savings_value = calculate_savings(df, result.get("group_insights", {}))
        total_spend_value = float(df['Spend'].sum())

        # 3. Create & Save Record (The "Save" logic is now here!)
        new_audit = models.Audit(
            filename=file.filename,
            total_spend=total_spend_value,
            potential_savings=float(savings_value),
            user_id=current_user.id
        )
        db.add(new_audit)
        db.commit()
        db.refresh(new_audit)

        return {
            "status": "success",
            "database_id": new_audit.id,
            "analysis": result,
            "summary": {"total_spend": total_spend_value, "savings": savings_value}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 2: SECURE HISTORY ---
@app.get("/history")
async def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # This filters the database so users only see their own folders
    return db.query(models.Audit).filter(models.Audit.user_id == current_user.id).all()

# --- ENDPOINT 3: DELETE AUDIT ---
@app.delete("/delete-audit/{audit_id}")
async def delete_audit(
    audit_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    audit = db.query(models.Audit).filter(
        models.Audit.id == audit_id, 
        models.Audit.user_id == current_user.id
    ).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found or unauthorized")
    
    db.delete(audit)
    db.commit()
    return {"message": "Deleted successfully"}

# --- AUTH ENDPOINTS (SIGNUP/LOGIN) ---
@app.post("/signup")
async def signup(data: dict, db: Session = Depends(get_db)):
    hashed_pwd = security.hash_password(data["password"])
    new_user = models.User(username=data["username"], hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/login")
async def login(data: dict, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data["username"]).first()
    if user and security.verify_password(data["password"], user.hashed_password):
        # We return a TOKEN now, not just a success message
        token = security.create_access_token(data={"sub": user.username})
        return {"status": "success", "access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")