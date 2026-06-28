"""
Tests unitaires — Authentification (sans PyTorch ni MySQL réel)

L'isolation de la base est assurée par la fixture autouse `fake_db`
définie dans conftest.py (base en mémoire vidée à chaque test).
"""

import os
import sys

# Ajouter le backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ──────────────────────────────────────────────
# Tests création d'utilisateur
# ──────────────────────────────────────────────

def test_create_user_returns_user():
    import auth
    user = auth.create_user("testuser", "test@example.com", "password123")
    assert user["username"] == "testuser"
    assert user["email"] == "test@example.com"
    assert "hashed_password" in user
    assert "id" in user
    assert "created_at" in user


def test_create_user_password_is_hashed():
    import auth
    user = auth.create_user("user2", "user2@example.com", "monmotdepasse")
    assert user["hashed_password"] != "monmotdepasse"


def test_get_user_by_email_found():
    import auth
    auth.create_user("alice", "alice@example.com", "pass123")
    found = auth.get_user_by_email("alice@example.com")
    assert found is not None
    assert found["username"] == "alice"


def test_get_user_by_email_not_found():
    import auth
    result = auth.get_user_by_email("inconnu@example.com")
    assert result is None


def test_get_user_by_email_case_insensitive():
    import auth
    auth.create_user("bob", "Bob@Example.com", "pass123")
    found = auth.get_user_by_email("bob@example.com")
    assert found is not None


def test_get_user_by_username_found():
    import auth
    auth.create_user("charlie", "charlie@example.com", "pass")
    found = auth.get_user_by_username("charlie")
    assert found is not None


def test_get_user_by_username_not_found():
    import auth
    result = auth.get_user_by_username("personne")
    assert result is None


# ──────────────────────────────────────────────
# Tests vérification de mot de passe
# ──────────────────────────────────────────────

def test_verify_password_correct():
    import auth
    user = auth.create_user("dave", "dave@example.com", "secret42")
    assert auth.verify_password("secret42", user["hashed_password"]) is True


def test_verify_password_wrong():
    import auth
    user = auth.create_user("eve", "eve@example.com", "correct")
    assert auth.verify_password("mauvais", user["hashed_password"]) is False


# ──────────────────────────────────────────────
# Tests JWT
# ──────────────────────────────────────────────

def test_create_and_decode_token():
    import auth
    token = auth.create_access_token("test@example.com")
    assert isinstance(token, str)
    assert len(token) > 10
    payload = auth.decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"


def test_decode_invalid_token():
    import auth
    payload = auth.decode_token("token.invalide.bidon")
    assert payload is None


def test_decode_tampered_token():
    import auth
    token = auth.create_access_token("user@example.com")
    tampered = token[:-5] + "XXXXX"
    payload = auth.decode_token(tampered)
    assert payload is None
