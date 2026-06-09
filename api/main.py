from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from data.database import Database

# ------------------------------------------------------------------ #
#  App                                                                 #
# ------------------------------------------------------------------ #

app = FastAPI(
    title="AccessNav API",
    description=(
        "Backend API for the AccessNav wheelchair navigation app. "
        "Provides user auth, accessibility spot data, and community "
        "barrier reports."
    ),
    version="1.0.0",
)

# Allow requests from the Kivy app and any local dev client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(router)


# ------------------------------------------------------------------ #
#  Startup                                                             #
# ------------------------------------------------------------------ #

@app.on_event("startup")
def startup():
    """Ensure the database and all tables exist on startup."""
    db = Database()
    db.connect()
    print("[API] Database ready")
    print("[API] AccessNav API started")


@app.get("/health")
def health():
    """Quick health check — confirms the API is running."""
    return {"status": "ok", "service": "AccessNav API"}