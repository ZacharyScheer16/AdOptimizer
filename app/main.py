from fastapi import FastAPI, UploadFile, File
from .model import run_clustering
import pandas as pd
import io

app = FastAPI()
@app.get("/")
async def home():
    return {"message": "Welcome to the AdOptimizer API!"}


@app.post("/upload-logistics")
async def upload_data(file: UploadFile = File(...)):
    # 1. Read the raw bytes
    contents = await file.read()
    
    # 2. Turn bytes into a table (DataFrame)
    # We use io.BytesIO(contents) to make the bytes look like a file
    df = pd.read_csv(io.BytesIO(contents))
    
    # 3. Use your model!
    result = run_clustering(df)
    
    return {
        "filename": file.filename,
        "ad_analyzed": len(df),
        "analysis": result
    }