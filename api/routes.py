import bcrypt
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Literal

from api.schemas import (
    RegisterRequest, LoginRequest, AuthResponse,
    SpotOut, ReportIn, ReportOut, MessageResponse,
)
from data.database import Database

router = APIRouter()

# Precompute a dummy bcrypt hash to use when a user is not found. This
# avoids bcrypt.checkpw raising on an invalid salt and keeps timing
# behaviour similar for missing users.
DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt(rounds=12))


def get_db():
    db = Database()
    db.connect()
    return db


def _make_token(user_id: int) -> str:
    """
    Simple token for development.
    Replace with JWT (python-jose) for production.
    """
    import hashlib, os
    salt  = os.urandom(8).hex()
    token = hashlib.sha256(f"{user_id}-{salt}".encode()).hexdigest()
    return token


# ------------------------------------------------------------------ #
#  Auth endpoints                                                      #
# ------------------------------------------------------------------ #

@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest):
    db = get_db()

    # Check duplicate email
    existing = db.fetchone(
        "SELECT id FROM users WHERE email = ?",
        (body.email.lower(),),
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    # Hash password
    pw_hash = bcrypt.hashpw(
        body.password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    cursor = db.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (body.name.strip(), body.email.lower(), pw_hash),
    )
    user_id = cursor.lastrowid
    token   = _make_token(user_id)

    return AuthResponse(
        id=user_id,
        name=body.name.strip(),
        email=body.email.lower(),
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    db = get_db()

    row = db.fetchone(
        "SELECT id, name, email, password FROM users WHERE email = ?",
        (body.email.lower(),),
    )

    # Run dummy check even if user not found — prevents timing attacks.
    # Use a real bcrypt hash for the dummy case so checkpw never raises.
    if row:
        stored_hash = row["password"].encode("utf-8")
    else:
        stored_hash = DUMMY_HASH

    match = bcrypt.checkpw(
        body.password.encode("utf-8"),
        stored_hash,
    )

    if not row or not match:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    token = _make_token(row["id"])

    return AuthResponse(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        token=token,
    )


# ------------------------------------------------------------------ #
#  Spots endpoints                                                     #
# ------------------------------------------------------------------ #

@router.get("/spots", response_model=List[SpotOut])
def list_spots(
    lat:       Optional[float] = Query(None, description="Centre latitude"),
    lon:       Optional[float] = Query(None, description="Centre longitude"),
    radius_m:  float           = Query(500,  description="Search radius in metres"),
    spot_type: Optional[str]   = Query(None, description="Filter by type: ramp, elevator, barrier"),
):
    """
    Return accessibility spots near a location.
    If lat/lon not provided, returns all spots (capped at 200).
    """
    db = get_db()

    if lat is not None and lon is not None:
        # Rough bounding box filter — fast, no PostGIS needed
        deg_per_m = 1 / 111_000
        delta     = radius_m * deg_per_m
        sql       = """
            SELECT id, lat, lon, spot_type, description, verified, created_at
            FROM spots
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
        """
        params = [lat - delta, lat + delta, lon - delta, lon + delta]

        if spot_type:
            sql    += " AND spot_type = ?"
            params.append(spot_type)

        sql += " ORDER BY created_at DESC LIMIT 200"
        rows = db.fetchall(sql, params)
    else:
        sql  = "SELECT id, lat, lon, spot_type, description, verified, created_at FROM spots"
        params = []
        if spot_type:
            sql += " WHERE spot_type = ?"
            params.append(spot_type)
        sql += " ORDER BY created_at DESC LIMIT 200"
        rows = db.fetchall(sql, params)

    return [
        SpotOut(
            id=r["id"],
            lat=r["lat"],
            lon=r["lon"],
            spot_type=r["spot_type"],
            description=r["description"] or "",
            verified=bool(r["verified"]),
            created_at=r["created_at"] or "",
        )
        for r in rows
    ]


@router.post("/spots", response_model=SpotOut, status_code=201)
def create_spot(
    lat:         float,
    lon:         float,
    spot_type:   Literal["ramp", "elevator", "barrier"],
    description: str = "",
):
    """Admin endpoint to add a verified accessibility spot."""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO spots (lat, lon, spot_type, description, verified) VALUES (?,?,?,?,1)",
        (lat, lon, spot_type, description),
    )
    row = db.fetchone("SELECT * FROM spots WHERE id = ?", (cursor.lastrowid,))
    return SpotOut(
        id=row["id"], lat=row["lat"], lon=row["lon"],
        spot_type=row["spot_type"], description=row["description"] or "",
        verified=True, created_at=row["created_at"] or "",
    )


# ------------------------------------------------------------------ #
#  Report endpoints                                                    #
# ------------------------------------------------------------------ #

@router.post("/report", response_model=ReportOut, status_code=201)
def submit_report(body: ReportIn):
    """
    Community barrier report submitted from the app.
    Automatically creates an unverified spot from the report.
    """
    db = get_db()

    # Verify user exists
    user = db.fetchone("SELECT id FROM users WHERE id = ?", (body.user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Insert report
    cursor = db.execute(
        """
        INSERT INTO reports (user_id, lat, lon, barrier_type, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (body.user_id, body.lat, body.lon,
         body.barrier_type, body.description),
    )
    report_id = cursor.lastrowid

    # Also add as an unverified spot so it shows on the map immediately
    db.execute(
        """
        INSERT INTO spots (lat, lon, spot_type, description, verified)
        VALUES (?, ?, 'barrier', ?, 0)
        """,
        (body.lat, body.lon, body.description or body.barrier_type),
    )

    row = db.fetchone("SELECT * FROM reports WHERE id = ?", (report_id,))
    return ReportOut(
        id=row["id"],
        lat=row["lat"],
        lon=row["lon"],
        barrier_type=row["barrier_type"],
        description=row["description"] or "",
        user_id=row["user_id"],
        created_at=row["created_at"] or "",
    )


@router.get("/reports", response_model=List[ReportOut])
def list_reports(
    user_id: Optional[int] = Query(None, description="Filter by user"),
):
    """List all community reports, optionally filtered by user."""
    db  = get_db()
    sql = "SELECT * FROM reports"
    params = []
    if user_id:
        sql += " WHERE user_id = ?"
        params.append(user_id)
    sql += " ORDER BY created_at DESC LIMIT 200"
    rows = db.fetchall(sql, params)
    return [
        ReportOut(
            id=r["id"], lat=r["lat"], lon=r["lon"],
            barrier_type=r["barrier_type"],
            description=r["description"] or "",
            user_id=r["user_id"],
            created_at=r["created_at"] or "",
        )
        for r in rows
    ]


# ...existing code...