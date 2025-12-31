"""
Script para verificar usuarios en la base de datos.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import User

app = create_app()

def check_users():
    """Verifica los usuarios en la base de datos."""
    with app.app_context():
        try:
            usuarios = User.query.all()
            print(f"\nTotal de usuarios en la base de datos: {len(usuarios)}\n")
            
            for user in usuarios:
                print(f"ID: {user.id}")
                print(f"Nombre: {user.nombre}")
                print(f"Email: {user.email}")
                print(f"Rol: {user.rol}")
                print(f"Activo: {user.activo}")
                print(f"Password hash: {user.password_hash[:50]}...")
                print("-" * 50)
            
            # Buscar específicamente "fran"
            fran = User.query.filter_by(nombre='fran').first()
            if fran:
                print(f"\n✓ Usuario 'fran' encontrado:")
                print(f"  - Nombre: {fran.nombre}")
                print(f"  - Email: {fran.email}")
                print(f"  - Activo: {fran.activo}")
                print(f"  - Verificando contraseña '1': {fran.check_password('1')}")
            else:
                print("\n✗ Usuario 'fran' NO encontrado")
                print("\nUsuarios disponibles:")
                for user in usuarios:
                    print(f"  - {user.nombre}")
                    
        except Exception as e:
            print(f"\n[ERROR] Error al verificar usuarios: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    check_users()



