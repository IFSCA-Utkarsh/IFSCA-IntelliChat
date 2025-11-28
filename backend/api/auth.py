from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Dict
from backend.core.config import settings
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

EMPLOYEES_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "employees.csv"))
SECRET_KEY = settings.JWT_SECRET

# === Cache employees ===
_employees_df = None
_df_lock = asyncio.Lock()

class LoginRequest(BaseModel):
    user_id: str
    password: str

async def get_employees() -> pd.DataFrame:
    global _employees_df
    async with _df_lock:
        if _employees_df is not None:
            return _employees_df
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(None, pd.read_csv, EMPLOYEES_FILE)
        required = ["user_id", "password", "department"]
        if not all(col in df.columns for col in required):
            raise ValueError("CSV missing columns")
        _employees_df = df
        return df

@router.post("/login")
async def login(data: LoginRequest):
    df = await get_employees()
    user = df[df["user_id"] == data.user_id]
    if user.empty or user.iloc[0]["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_data = user.iloc[0]
    token = jwt.encode(
        {
            "user_id": data.user_id,
            "department": user_data["department"],
            "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MIN)
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    logger.info(f"Login: {data.user_id} | {user_data['department']}")
    return {
        "message": "Login successful",
        "user": {"user_id": data.user_id, "department": user_data["department"]},
        "access_token": token,
        "token_type": "bearer"
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
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
        logger.error(f"Token error: {e}")
        raise HTTPException(status_code=500, detail="Verification error")