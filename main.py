# main.py (in root directory)
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (client)
app.mount("/", StaticFiles(directory="app/client", html=True), name="client")

# Serve data files
@app.get("/{layer_name}/{file_name}")
async def get_data_file(layer_name: str, file_name: str):
    file_path = os.path.join("app/server/data", layer_name, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
    return FileResponse(file_path)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)