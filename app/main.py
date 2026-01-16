import os
import io
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

# Import our new Modular pieces
from . import models, security
from .database import engine, get_db, Base
from .model import run_clustering # Your AI logic

# --- DATABASE SETUP ---
# This "Master Switch" creates the .db file and tables based on models.py
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def home():
    return {
        "message": "Welcome to the AdOptimizer SQL API!",
        "status": "Running",
        "database": "SQLite (adoptimizer.db)"
    }

# --- ENDPOINT 1: AI ANALYSIS ---
@app.post("/upload-logistics")
async def upload_data(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # Run your clustering model logic
    result = run_clustering(df)
    
    return {
        "filename": file.filename,
        "ad_analyzed": len(df),
        "analysis": result
    }

# --- ENDPOINT 2: SAVE TO HISTORY (SQL Version) ---
@app.post("/save-audit")
async def save_audit(data: dict, db: Session = Depends(get_db)):
    try:
        # Create a new Audit object using the SQL model
        new_audit = models.Audit(
            filename=data["filename"],
            total_spend=data["total_spend"],
            potential_savings=data["potential_savings"],
            # Note: timestamp is handled automatically by the model's default
            user_id=data.get("user_id") 
        )
        
        db.add(new_audit)
        db.commit()
        db.refresh(new_audit)

        return {
            "status": "success", 
            "entry_id": new_audit.id, 
            "message": "Audit saved to SQL database."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 3: RETRIEVE HISTORY (SQL Version) ---
@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    # This replaces db.all()
    audits = db.query(models.Audit).all()
    return audits

# --- ENDPOINT 4: USER SIGNUP (SECURE) ---
@app.post("/signup")
async def signup(data: dict, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == data["username"]).first()
    if existing_user:
        return {"status": "error", "message": "Username already exists."}
    
    # 2. Hash the password
    hashed_password = security.hash_password(data["password"])
    
    # 3. Create and save user
    new_user = models.User(username=data["username"], hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    
    return {"status": "success", "message": "User registered successfully."}
    
# --- ENDPOINT 5: USER LOGIN (SECURE) ---
@app.post("/login")
async def login(data: dict, db: Session = Depends(get_db)):
    # 1. Find user by username
    user = db.query(models.User).filter(models.User.username == data["username"]).first()
    
    # 2. Verify password attempt against stored hash
    if user and security.verify_password(data["password"], user.hashed_password):
        return {
            "status": "success", 
            "message": "Login successful.",
            "user_id": user.id # Send this back so Streamlit can use it for history
        }
    else:
        return {"status": "error", "message": "Invalid username or password."}