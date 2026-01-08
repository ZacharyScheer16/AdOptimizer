import os
import io
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from tinydb import TinyDB, Query

# Import your AI logic
from .model import run_clustering

# --- DATABASE SETUP ---
# This ensures the database file is always in the same folder as this script
db = TinyDB('database.json')
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'database.json')
audits_table = db.table('audits')
user_table = db.table('users')


app = FastAPI()

@app.get("/")
async def home():
    return {
        "message": "Welcome to the AdOptimizer API!",
        "database_location": db_path
    }

# --- ENDPOINT 1: AI ANALYSIS ---
@app.post("/upload-logistics")
async def upload_data(file: UploadFile = File(...)):
    # 1. Read the raw bytes
    contents = await file.read()
    
    # 2. Turn bytes into a table (DataFrame)
    df = pd.read_csv(io.BytesIO(contents))
    
    # 3. Use your model!
    result = run_clustering(df)
    
    return {
        "filename": file.filename,
        "ad_analyzed": len(df),
        "analysis": result
    }

# --- ENDPOINT 2: SAVE TO HISTORY ---
@app.post("/save-audit")
async def save_audit(data: dict):
    try:
        # Add the timestamp for logistics tracking
        data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert into TinyDB
        entry_id = db.insert(data)

        return {
            "status": "success", 
            "entry_id": entry_id, 
            "saved_data": data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 3: RETRIEVE HISTORY ---
@app.get("/history")
async def get_history():
    # Returns all saved audits for the Streamlit History Tab
    return db.all()

# --- ENDPOINT 4 User signup ---
@app.post("/signup")
async def signup(data: dict):
    try:
        User = Query()
        existing_user = user_table.get(User.username == data["username"])
        if existing_user:
            return {"status": "error", "message": "Username already exists."}
        user_table.insert(data)
        return {"status": "success", "message": "User registered successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# --- ENDPOINT 5 User login ---
@app.post("/login")
async def login(data:dict):
    try:
        User = Query()
        user = user_table.get(User.username == data["username"])
        if user and user['password'] == data['password']:
            return {"status": "success", "message": "Login successful."}
        else:
            return{"status": "error", "message": "Invalid username or password."}
    except Exception as e:
        return {"status": "error", "message": str(e)}