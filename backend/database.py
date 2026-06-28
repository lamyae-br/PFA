"""
=============================================================
database.py — Connexion MySQL (pool) et initialisation
=============================================================
Remplace le stockage des utilisateurs dans users.json par une
vraie base de données MySQL. La configuration est lue depuis
le fichier .env (voir .env.example).
=============================================================
"""

import os
from pathlib import Path

import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Charge le .env situé dans le dossier backend/, quel que soit le cwd
load_dotenv(Path(__file__).resolve().parent / ".env")

DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "localhost"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "pfa_gnn"),
}

_pool = None


def get_pool() -> pooling.MySQLConnectionPool:
    """Crée (une seule fois) et retourne le pool de connexions MySQL."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="pfa_pool",
            pool_size=5,
            pool_reset_session=True,
            charset="utf8mb4",
            **DB_CONFIG,
        )
    return _pool


def get_connection():
    """Retourne une connexion issue du pool (à fermer après usage)."""
    return get_pool().get_connection()


def init_db():
    """
    Initialise la base : crée la base de données et la table `users`
    si elles n'existent pas encore. Appelé au démarrage du backend.
    """
    # 1) S'assurer que la base de données existe
    boot = mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    cur = boot.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    boot.commit()
    cur.close()
    boot.close()

    # 2) Créer la table `users` si nécessaire
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              VARCHAR(36)  NOT NULL PRIMARY KEY,
                username        VARCHAR(30)  NOT NULL UNIQUE,
                email           VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                created_at      DATETIME     NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )
        conn.commit()
        cur.close()
        print(f"        Base MySQL prête : {DB_CONFIG['database']}.users")
    finally:
        conn.close()
