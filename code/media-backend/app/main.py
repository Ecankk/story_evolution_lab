from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import story, analysis, ws, game

app = FastAPI(title="Media Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(story.router, prefix="/api/story", tags=["story"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(game.router, prefix="/api/game", tags=["game"])
app.include_router(ws.router, tags=["websocket"])

# 方案一：一体化部署 (Frontend Integration)
from fastapi.staticfiles import StaticFiles
import os

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "media-frontend2", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
    print(f"✅ Frontend mounted from: {frontend_dist}")
else:
    print(f"⚠️ Frontend build not found at: {frontend_dist}. Run 'npm run build' in frontend dir.")
