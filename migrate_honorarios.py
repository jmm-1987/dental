"""
Script para crear la tabla de honorarios.
"""
import sys
import io

# Configurar stdout para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import Honorario

app = create_app()

with app.app_context():
    try:
        # Crear la tabla
        db.create_all()
        print("[OK] Tabla 'honorarios' creada correctamente.")
    except Exception as e:
        print(f"[ERROR] Error al crear la tabla: {e}")

