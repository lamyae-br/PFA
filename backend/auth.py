"""
auth.py — Gestion des utilisateurs (MySQL) et JWT

Les comptes utilisateurs sont stockés dans la table MySQL `users`
(voir database.py). L'authentification reste basée sur JWT (HS256)
et le hachage des mots de passe avec bcrypt — seule la couche de
stockage change par rapport à l'ancienne version users.json.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from database import get_connection

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pfa-gnn-super-secret-key-change-in-prod-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# ─────────────────────────────────────────────
# Mapping ligne SQL -> dict utilisateur
# ─────────────────────────────────────────────

def _row_to_user(row: tuple) -> dict:
    """Convertit une ligne de la table users en dictionnaire."""
    created = row[4]
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "hashed_password": row[3],
        "created_at": created.isoformat() if hasattr(created, "isoformat") else str(created),
    }


# ─────────────────────────────────────────────
# Opérations sur les utilisateurs (MySQL)
# ─────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[dict]:
    """Recherche un utilisateur par email (insensible à la casse)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, hashed_password, created_at "
            "FROM users WHERE email = %s",
            (email.strip().lower(),),
        )
        row = cur.fetchone()
        cur.close()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Recherche un utilisateur par nom d'utilisateur (insensible à la casse)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, hashed_password, created_at "
            "FROM users WHERE LOWER(username) = LOWER(%s)",
            (username.strip(),),
        )
        row = cur.fetchone()
        cur.close()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def create_user(username: str, email: str, password: str) -> dict:
    """Crée un nouvel utilisateur en base et retourne ses informations."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = {
        "id": str(uuid.uuid4()),
        "username": username.strip(),
        "email": email.strip().lower(),
        "hashed_password": hashed,
        "created_at": datetime.now(timezone.utc),
    }

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (id, username, email, hashed_password, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                user["id"],
                user["username"],
                user["email"],
                user["hashed_password"],
                user["created_at"],
            ),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()

    # Renvoie created_at en chaîne ISO (cohérent avec le schéma UserOut)
    user["created_at"] = user["created_at"].isoformat()
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
