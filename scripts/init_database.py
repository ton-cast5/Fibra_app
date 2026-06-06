"""Crea todas las tablas según los modelos SQLAlchemy (si no existen)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(override=True)

def main():
    from app import app, db, Archivo, NapModel, Nat, Cliente, Potencia

    with app.app_context():
        db.create_all()
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tablas creadas/verificadas:", ", ".join(sorted(tables)) or "(ninguna)")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("Error:", e)
        raise SystemExit(1)
