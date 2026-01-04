from fastapi import FastAPI
from .model import run_clustering

app = FastAPI()
@app.get("/")
async def home():
    return {"message": "Welcome to the AdOptimizer API!"}