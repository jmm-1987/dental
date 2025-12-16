"""
Script para crear el usuario 'fran' con contraseña '1'.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import User

app = create_app()

def create_fran():
    """Crea el usuario 'fran' con contraseña '1'."""
    with app.app_context():
        try:
            # Verificar si ya existe
            fran = User.query.filter_by(nombre='fran').first()
            
            if fran:
                print(f"\nUsuario 'fran' ya existe. Actualizando contraseña...")
                fran.set_password('1')
                fran.activo = True
                fran.rol = 'admin'
                db.session.commit()
                print(f"✓ Contraseña actualizada para usuario 'fran'")
            else:
                print("\nCreando usuario 'fran'...")
                fran = User(
                    nombre='fran',
                    email='fran@clinicadental.com',
                    rol='admin',
                    activo=True
                )
                fran.set_password('1')
                db.session.add(fran)
                db.session.commit()
                print(f"✓ Usuario 'fran' creado correctamente")
            
            # Verificar que funciona
            fran_check = User.query.filter_by(nombre='fran').first()
            if fran_check and fran_check.check_password('1'):
                print(f"\n✓ Verificación exitosa:")
                print(f"  - Nombre: {fran_check.nombre}")
                print(f"  - Email: {fran_check.email}")
                print(f"  - Rol: {fran_check.rol}")
                print(f"  - Activo: {fran_check.activo}")
                print(f"  - Contraseña '1' verificada: ✓")
            else:
                print("\n✗ Error: La contraseña no se verificó correctamente")
                
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al crear usuario: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_fran()

