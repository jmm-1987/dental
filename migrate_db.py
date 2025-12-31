"""
Script de migración para añadir las nuevas columnas y tablas.
Ejecutar: python migrate_db.py
"""
from app import create_app, db
from app.models import Room, ClinicSettings
import sqlite3

def migrate_db():
    """Migra la base de datos añadiendo nuevas columnas y tablas."""
    app = create_app()
    
    with app.app_context():
        # Obtener la ruta de la base de datos
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        try:
            # Conectar directamente a SQLite para hacer cambios en el esquema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si existe la columna room_id en appointments
            cursor.execute("PRAGMA table_info(appointments)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'room_id' not in columns:
                print("Añadiendo columna room_id a la tabla appointments...")
                cursor.execute("ALTER TABLE appointments ADD COLUMN room_id INTEGER")
                print("✓ Columna room_id añadida correctamente.")
            else:
                print("✓ La columna room_id ya existe.")
            
            # Crear las nuevas tablas si no existen
            print("\nCreando nuevas tablas...")
            db.create_all()
            
            # Verificar si existen las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            if 'rooms' not in tables:
                print("✓ Tabla 'rooms' creada.")
            else:
                print("✓ Tabla 'rooms' ya existe.")
            
            if 'clinic_settings' not in tables:
                print("✓ Tabla 'clinic_settings' creada.")
            else:
                print("✓ Tabla 'clinic_settings' ya existe.")
            
            conn.commit()
            conn.close()
            
            # Crear datos por defecto si no existen
            print("\nVerificando datos por defecto...")
            
            # Crear salas de ejemplo si no existen
            salas_ejemplo = ['Sillón 1', 'Sillón 2', 'Sillón 3', 'Sala de Cirugía']
            for nombre_sala in salas_ejemplo:
                sala_existente = Room.query.filter_by(nombre=nombre_sala).first()
                if not sala_existente:
                    sala = Room(nombre=nombre_sala, descripcion=f'Sala {nombre_sala}', activo=True)
                    db.session.add(sala)
                    print(f"  ✓ Sala '{nombre_sala}' creada.")
            
            # Crear configuración de clínica por defecto si no existe
            if not ClinicSettings.query.first():
                settings = ClinicSettings(
                    nombre_clinica='Clínica Dental',
                    direccion='Calle Principal, 123',
                    ciudad='Madrid',
                    provincia='Madrid',
                    codigo_postal='28001',
                    telefono='912 345 678',
                    email='info@clinicadental.com'
                )
                db.session.add(settings)
                print("  ✓ Configuración de clínica creada.")
            
            db.session.commit()
            
            print("\n✓ Migración completada correctamente.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error durante la migración: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_db()




