"""Prueba conexion Supabase: venv\\Scripts\\python scripts\\test_connection.py"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(override=True)


def main():
    from urllib.parse import quote_plus
    from sqlalchemy import create_engine, text

    base = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    print("SUPABASE_URL:", base)
    print("ANON_KEY:", "ok" if key else "falta")

    ref = base.replace("https://", "").split(".")[0] if "supabase.co" in base else "ckzkznyaajmqwrjdlcld"
    pwd = os.getenv("DB_PASSWORD", "").strip()
    if not pwd:
        print("ERROR: Define DB_PASSWORD en .env")
        return 1

    host = os.getenv("DB_POOLER_HOST", "aws-1-us-west-2.pooler.supabase.com")
    port = os.getenv("DB_POOLER_PORT", "6543")
    user = os.getenv("DB_POOLER_USER", f"postgres.{ref}")
    url = f"postgresql://{user}:{quote_plus(pwd)}@{host}:{port}/postgres"
    print("Pooler:", host)

    try:
        engine = create_engine(url, connect_args={"sslmode": "require", "connect_timeout": 15})
        with engine.connect() as conn:
            print("PostgreSQL OK:", conn.execute(text("SELECT 1")).scalar())
            tables = [
                r[0]
                for r in conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' ORDER BY tablename"
                    )
                ).fetchall()
            ]
            print("Tablas:", ", ".join(tables) if tables else "(ninguna - ejecuta supabase_schema.sql)")
        return 0
    except Exception as e:
        print("ERROR:", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
