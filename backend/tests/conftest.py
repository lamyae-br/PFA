"""
Configuration pytest — fixtures partagées.

Les tests s'exécutent SANS serveur MySQL : le driver mysql.connector est
remplacé par un mock, et la couche base de données par une fausse base
en mémoire (fixture fake_db, vidée à chaque test). L'authentification
JWT/bcrypt reste testée pour de vrai.
"""

import os
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# Ajouter le dossier backend au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-ci-only")


# ──────────────────────────────────────────────
# Mock du driver MySQL (non installé / pas de serveur en CI)
# ──────────────────────────────────────────────
_mysql = ModuleType("mysql")
_connector = ModuleType("mysql.connector")
_connector.connect = MagicMock()
_pooling = ModuleType("mysql.connector.pooling")
_pooling.MySQLConnectionPool = MagicMock()
_connector.pooling = _pooling
_mysql.connector = _connector
sys.modules.setdefault("mysql", _mysql)
sys.modules.setdefault("mysql.connector", _connector)
sys.modules.setdefault("mysql.connector.pooling", _pooling)


# ──────────────────────────────────────────────
# Fausse base de données en mémoire
# ──────────────────────────────────────────────
class _FakeCursor:
    """Interprète les quelques requêtes SQL utilisées par auth.py."""

    def __init__(self, store):
        self.store = store
        self._result = None
        self.rowcount = 0

    def execute(self, sql, params=()):
        s = " ".join(sql.split()).upper()
        if s.startswith("INSERT INTO USERS"):
            id_, username, email, pwd, created = params
            exists = any(
                r["email"] == email or r["username"].lower() == username.lower()
                for r in self.store
            )
            if exists:
                self.rowcount = 0           # contrainte UNIQUE / INSERT IGNORE
            else:
                self.store.append({
                    "id": id_, "username": username, "email": email,
                    "hashed_password": pwd, "created_at": created,
                })
                self.rowcount = 1
            self._result = None
        elif "WHERE EMAIL" in s:
            email = params[0]
            self._result = next((r for r in self.store if r["email"] == email), None)
        elif "LOWER(USERNAME)" in s:
            uname = params[0].lower()
            self._result = next(
                (r for r in self.store if r["username"].lower() == uname), None
            )
        else:
            self._result = None

    def fetchone(self):
        r = self._result
        if not r:
            return None
        return (r["id"], r["username"], r["email"],
                r["hashed_password"], r["created_at"])

    def close(self):
        pass


class _FakeConnection:
    def __init__(self, store):
        self.store = store

    def cursor(self):
        return _FakeCursor(self.store)

    def commit(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    """Remplace la connexion MySQL par une base en mémoire vidée à chaque test."""
    store = []
    import auth
    import database

    monkeypatch.setattr(auth, "get_connection", lambda: _FakeConnection(store))
    monkeypatch.setattr(database, "get_connection",
                        lambda: _FakeConnection(store), raising=False)
    monkeypatch.setattr(database, "init_db", lambda: None, raising=False)
    return store
