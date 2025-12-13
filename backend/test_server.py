from fastapi import FastAPI
import uvicorn
import sys
import asyncio

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print("Starting minimal server...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"CRASH: {e}")
