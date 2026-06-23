"""
Configuration pytest — fixtures partagées
"""

import os
import sys

# Ajouter le dossier backend au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Variable d'environnement pour les tests
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-ci-only")
