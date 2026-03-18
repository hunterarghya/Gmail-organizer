from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from backend.routers import auth, actions
import os

app = FastAPI(title="Gmail AI Organizer")

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("JWT_SECRET", "dev_secret"),
    https_only=False,
    same_site="lax"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.include_router(auth.router)
app.include_router(actions.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")