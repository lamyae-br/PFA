"""
routes/pfa.py — Endpoint pour le vecteur PFA
"""

from fastapi import APIRouter, Depends
from schemas import PFAVectorResponse
from data_loader import get_pfa_vector
from dependencies import get_current_user

router = APIRouter()


@router.get("/pfa-vector", response_model=PFAVectorResponse)
def get_pfa(_user: dict = Depends(get_current_user)):
    """
    Retourne le vecteur PFA (Projet de Football Athlétique).
    18 dimensions tactiques représentant le profil idéal.
    """
    pfa_vector = get_pfa_vector()
    return PFAVectorResponse(
        dimensions=len(pfa_vector),
        vector=pfa_vector,
        description=(
            "Vecteur représentant le profil tactique idéal. "
            "Combine attributs FIFA (pace, passing, defending...) "
            "et statistiques réelles StatsBomb (pressings, carries, duels...)."
        )
    )
