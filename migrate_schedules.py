"""
Script de migración para añadir la tabla doctor_schedules.
Ejecutar: python migrate_schedules.py
"""
from app import create_app, db
from app.models import DoctorSchedule
import sqlite3

def migrate_schedules():
    """Migra la base de datos añadiendo la tabla doctor_schedules."""
    app = create_app()
    
    with app.app_context():
        # Obtener la ruta de la base de datos
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        try:
            # Conectar directamente a SQLite para verificar
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si existe la tabla
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctor_schedules'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("Creando tabla doctor_schedules...")
                db.create_all()
                print("✓ Tabla doctor_schedules creada correctamente.")
            else:
                print("✓ La tabla doctor_schedules ya existe.")
            
            conn.close()
            
            print("\n✓ Migración completada correctamente.")
            
        except Exception as e:
            print(f"\n✗ Error durante la migración: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_schedules()


