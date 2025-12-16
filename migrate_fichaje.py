"""
Script de migración para añadir las tablas de fichaje.
Ejecutar: python migrate_fichaje.py
"""
from app import create_app, db
from app.models import TimeClock, DayOff
import sqlite3

def migrate_fichaje():
    """Migra la base de datos añadiendo las tablas de fichaje."""
    app = create_app()
    
    with app.app_context():
        # Obtener la ruta de la base de datos
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        try:
            # Conectar directamente a SQLite para verificar
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si existe la tabla time_clocks
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_clocks'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("Creando tablas de fichaje...")
                db.create_all()
                print("OK: Tablas time_clocks y day_offs creadas correctamente.")
            else:
                print("OK: Las tablas de fichaje ya existen.")
            
            conn.close()
            
            print("\nOK: Migracion completada correctamente.")
            
        except Exception as e:
            print(f"\nERROR: Error durante la migracion: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_fichaje()

