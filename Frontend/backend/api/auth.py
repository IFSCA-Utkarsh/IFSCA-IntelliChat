# -*- coding: utf-8 -*-
"""Authentication module using CSV-based auth with JWT."""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Dict
from backend.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Load employees.csv from data/
EMPLOYEES_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "employees.csv"))
SECRET_KEY = "your-secret-key"  # Move to .env in production

class LoginRequest(BaseModel):
    user_id: str
    password: str

def load_employees() -> pd.DataFrame:
    """Load employee data from CSV."""
    try:
        df = pd.read_csv(EMPLOYEES_FILE)
        required_columns = ["user_id", "password", "department"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError("CSV missing required columns: user_id, password, department")
        return df
    except Exception as e:
        logger.error(f"Failed to load employees.csv: {e}")
        raise HTTPException(status_code=500, detail="Authentication setup error")

@router.post("/login")
async def login(data: LoginRequest):
    """Authenticate user and return JWT."""
    try:
        employees = load_employees()
        user = employees[employees["user_id"] == data.user_id]
        if user.empty or user.iloc[0]["password"] != data.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_data = user.iloc[0]
        token = jwt.encode(
            {
                "user_id": data.user_id,
                "department": user_data["department"],
                "exp": datetime.utcnow() + timedelta(minutes=60)  # Changed to 60 minutes
            },
            SECRET_KEY,
            algorithm="HS256"
        )
        logger.info(f"User {data.user_id} logged in successfully")
        return {
            "message": "Login successful",
            "user": {"user_id": data.user_id, "department": user_data["department"]},
            "access_token": token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login failed for {data.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify JWT and return user data."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return {"user_id": payload["user_id"], "department": payload["department"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=500, detail="Verification error")