from fastapi import FastAPI
from src.core.reliability import get_device

app = FastAPI(title="Sonora Separator")

@app.get("/health")
def health():
    return {"status": "healthy", "device": get_device()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
