"""Punto de entrada serverless para Vercel."""
import os
import sys

# Vercel ejecuta este archivo desde api/; el proyecto está un nivel arriba.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from app import app  # noqa: E402
