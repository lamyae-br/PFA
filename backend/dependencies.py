"""
dependencies.py — Dépendance FastAPI pour l'authentification JWT
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from auth import decode_token, get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Valide le JWT et retourne l'utilisateur courant."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré. Veuillez vous reconnecter.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise exc
    email: str = payload.get("sub")
    if not email:
        raise exc
    user = get_user_by_email(email)
    if user is None:
        raise exc
    return user
