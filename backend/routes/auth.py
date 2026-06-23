"""
routes/auth.py — Endpoints d'authentification
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from auth import (
    get_user_by_email, get_user_by_username,
    create_user, verify_password, create_access_token,
)
from dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentification"])


# ─────────────────────────────────────────────
# Schémas
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str    = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email:    str
    password: str


class UserOut(BaseModel):
    id:         str
    username:   str
    email:      str
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=201)
def register(req: RegisterRequest):
    """Crée un nouveau compte utilisateur."""
    if "@" not in req.email or "." not in req.email:
        raise HTTPException(status_code=400, detail="Adresse email invalide.")
    if get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    if get_user_by_username(req.username):
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris.")

    user = create_user(req.username, req.email, req.password)
    token = create_access_token(user["email"])
    return AuthResponse(
        access_token=token,
        user=UserOut(**{k: user[k] for k in UserOut.model_fields}),
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Connexion — retourne un JWT."""
    user = get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )
    token = create_access_token(user["email"])
    return AuthResponse(
        access_token=token,
        user=UserOut(**{k: user[k] for k in UserOut.model_fields}),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    """Retourne les informations de l'utilisateur connecté."""
    return UserOut(**{k: current_user[k] for k in UserOut.model_fields})


@router.post("/logout")
def logout():
    """JWT stateless — la déconnexion est gérée côté client."""
    return {"message": "Déconnecté avec succès."}
