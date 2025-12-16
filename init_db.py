"""
Script de inicialización de la base de datos.
Ejecutar: python init_db.py
"""
from app import create_app, db
from app.models import User, Patient, Room, ClinicSettings
from werkzeug.security import generate_password_hash

def init_db():
    """Inicializa la base de datos con tablas y datos por defecto."""
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        print("Creando tablas...")
        db.create_all()
        
        # Verificar si ya existe un admin
        admin = User.query.filter_by(email='admin@clinicadental.com').first()
        if not admin:
            print("Creando usuario administrador por defecto...")
            admin = User(
                nombre='fran',
                email='fran',
                rol='admin',
                activo=True
            )
            admin.set_password('1')  # Cambiar en producción
            db.session.add(admin)
        
        # Crear usuario recepcionista de ejemplo
        recepcionista = User.query.filter_by(email='recepcion@clinicadental.com').first()
        if not recepcionista:
            print("Creando usuario recepcionista de ejemplo...")
            recepcionista = User(
                nombre='Recepcionista',
                email='recepcion@clinicadental.com',
                rol='recepcionista',
                activo=True
            )
            recepcionista.set_password('recepcion123')
            db.session.add(recepcionista)
        
        # Crear dentista de ejemplo
        dentista = User.query.filter_by(email='dentista@clinicadental.com').first()
        if not dentista:
            print("Creando usuario dentista de ejemplo...")
            dentista = User(
                nombre='Dr. Juan Pérez',
                email='dentista@clinicadental.com',
                rol='dentista',
                activo=True
            )
            dentista.set_password('dentista123')
            db.session.add(dentista)
        
        # Crear salas de ejemplo
        salas_ejemplo = ['Sillón 1', 'Sillón 2', 'Sillón 3', 'Sala de Cirugía']
        for nombre_sala in salas_ejemplo:
            sala_existente = Room.query.filter_by(nombre=nombre_sala).first()
            if not sala_existente:
                sala = Room(nombre=nombre_sala, descripcion=f'Sala {nombre_sala}', activo=True)
                db.session.add(sala)
        
        # Crear configuración de clínica por defecto
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
        
        try:
            db.session.commit()
            print("✓ Base de datos inicializada correctamente.")
            print("\nUsuarios creados:")
            print("  Admin: admin@clinicadental.com / admin123")
            print("  Recepcionista: recepcion@clinicadental.com / recepcion123")
            print("  Dentista: dentista@clinicadental.com / dentista123")
            print("\nSalas creadas:")
            for sala in Room.query.all():
                print(f"  - {sala.nombre}")
            print("\n⚠ IMPORTANTE: Cambia las contraseñas en producción.")
        except Exception as e:
            db.session.rollback()
            print(f"Error al inicializar la base de datos: {e}")

if __name__ == '__main__':
    init_db()

