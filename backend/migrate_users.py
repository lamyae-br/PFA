"""
migrate_users.py — Migration users.json -> MySQL (à lancer une fois)

Lit l'ancien fichier backend/users.json et insère chaque compte dans
la table MySQL `users`. Les mots de passe sont déjà hachés (bcrypt) :
ils sont copiés tels quels, donc les utilisateurs gardent leur mot
de passe actuel.

Usage :
    cd backend
    python migrate_users.py
"""

import json
import os
from datetime import datetime

from database import get_connection, init_db

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.utcnow()


def migrate():
    init_db()  # s'assure que la base et la table existent

    if not os.path.exists(USERS_FILE):
        print("Aucun users.json trouvé — rien à migrer.")
        return

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f).get("users", [])

    if not users:
        print("users.json vide — rien à migrer.")
        return

    conn = get_connection()
    inserted, skipped = 0, 0
    try:
        cur = conn.cursor()
        for u in users:
            # INSERT IGNORE : ne réinsère pas un email/username déjà présent
            cur.execute(
                "INSERT IGNORE INTO users "
                "(id, username, email, hashed_password, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (
                    u["id"],
                    u["username"],
                    u["email"].lower(),
                    u["hashed_password"],
                    _parse_dt(u.get("created_at")),
                ),
            )
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        conn.commit()
        cur.close()
    finally:
        conn.close()

    print(f"Migration terminée : {inserted} insérés, {skipped} déjà présents.")


if __name__ == "__main__":
    migrate()
