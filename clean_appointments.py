"""
Script para limpiar citas duplicadas o todas las citas.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import Appointment
from datetime import datetime

app = create_app()

def limpiar_citas_duplicadas():
    """Elimina citas duplicadas (mismo paciente, mismo doctor, misma fecha/hora)."""
    with app.app_context():
        try:
            # Contar citas antes
            total_antes = Appointment.query.count()
            print(f"\nTotal de citas antes: {total_antes}")
            
            # Buscar duplicados: mismo paciente, mismo doctor, misma fecha/hora inicio
            citas = Appointment.query.all()
            citas_vistas = set()
            citas_a_eliminar = []
            
            for cita in citas:
                clave = (cita.patient_id, cita.dentist_id, cita.fecha_hora_inicio)
                if clave in citas_vistas:
                    citas_a_eliminar.append(cita)
                else:
                    citas_vistas.add(clave)
            
            # Eliminar duplicados
            for cita in citas_a_eliminar:
                db.session.delete(cita)
            
            db.session.commit()
            
            total_despues = Appointment.query.count()
            eliminadas = total_antes - total_despues
            
            print(f"  ✓ Eliminadas {eliminadas} citas duplicadas")
            print(f"  ✓ Citas restantes: {total_despues}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al limpiar citas: {e}")
            import traceback
            traceback.print_exc()

def limpiar_todas_las_citas():
    """Elimina todas las citas de la base de datos."""
    with app.app_context():
        try:
            total = Appointment.query.count()
            print(f"\nEliminando todas las citas ({total} citas)...")
            
            Appointment.query.delete()
            db.session.commit()
            
            print(f"  ✓ Eliminadas todas las citas")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al eliminar citas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        limpiar_todas_las_citas()
    else:
        limpiar_citas_duplicadas()



