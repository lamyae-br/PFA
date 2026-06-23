"""
auth.py — Gestion des utilisateurs (fichier JSON) et JWT
"""

import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pfa-gnn-super-secret-key-change-in-prod-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")


# ─────────────────────────────────────────────
# Lecture / écriture du fichier utilisateurs
# ─────────────────────────────────────────────

def _load_users() -> list:
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("users", [])


def _save_users(users: list):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# Opérations sur les utilisateurs
# ─────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    for user in _load_users():
        if user["email"].lower() == email.lower():
            return user
    return None


def get_user_by_username(username: str) -> Optional[dict]:
    for user in _load_users():
        if user["username"].lower() == username.lower():
            return user
    return None


def create_user(username: str, email: str, password: str) -> dict:
    users = _load_users()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    user = {
        "id": str(uuid.uuid4()),
        "username": username.strip(),
        "email": email.strip().lower(),
        "hashed_password": hashed.decode("utf-8"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    _save_users(users)
    return user


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ─────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────

def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
