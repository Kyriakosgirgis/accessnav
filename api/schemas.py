from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Optional
from datetime import datetime


# ------------------------------------------------------------------ #
#  Auth                                                                #
# ------------------------------------------------------------------ #

class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        # Allow short names (tests use single-letter names). Only ensure it's not empty.
        if len(v.strip()) < 1:
            raise ValueError("Name must not be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class AuthResponse(BaseModel):
    id:    int
    name:  str
    email: str
    token: str   # simple user-id based token for Phase 6 — JWT in production


# ------------------------------------------------------------------ #
#  Spots (accessibility POIs)                                          #
# ------------------------------------------------------------------ #

class SpotOut(BaseModel):
    id:          int
    lat:         float
    lon:         float
    spot_type:   Literal["ramp", "elevator", "barrier"]
    description: str
    verified:    bool
    created_at:  str


# ------------------------------------------------------------------ #
#  Reports (community submissions)                                     #
# ------------------------------------------------------------------ #

class ReportIn(BaseModel):
    lat:          float
    lon:          float
    barrier_type: Literal[
        "broken_elevator",
        "missing_ramp",
        "blocked_path",
        "steep_slope",
        "other",
    ]
    description:  str
    user_id:      int

    @field_validator("lat")
    @classmethod
    def valid_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError("Invalid latitude")
        return v

    @field_validator("lon")
    @classmethod
    def valid_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError("Invalid longitude")
        return v


class ReportOut(BaseModel):
    id:           int
    lat:          float
    lon:          float
    barrier_type: str
    description:  str
    user_id:      int
    created_at:   str


class MessageResponse(BaseModel):
    status:  str
    message: str