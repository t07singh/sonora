from fastapi import FastAPI
import uvicorn
import os

app = FastAPI(title="Sonora Minimal API")

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "minimal"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
