"""
Script para limpiar los datos de muestra de la base de datos.
Ejecutar: python clean_sample_data.py
⚠️ ADVERTENCIA: Este script eliminará todos los pacientes, citas, tratamientos, facturas y registros clínicos de muestra.
Solo mantendrá los usuarios del sistema y las configuraciones básicas.
"""
from app import create_app, db
from app.models import (
    Patient, Appointment, ClinicalRecord, Odontogram,
    TreatmentPlan, TreatmentItem, Invoice, Payment, Notification
)

def clean_sample_data():
    """Elimina todos los datos de muestra de la base de datos."""
    app = create_app()
    
    with app.app_context():
        print("⚠️  ADVERTENCIA: Este script eliminará todos los datos de muestra.")
        print("Se eliminarán:")
        print("  - Todos los pacientes")
        print("  - Todas las citas")
        print("  - Todos los tratamientos")
        print("  - Todas las facturas")
        print("  - Todos los pagos")
        print("  - Todos los registros clínicos")
        print("  - Todos los odontogramas")
        print("  - Todas las notificaciones")
        print("\nSe mantendrán:")
        print("  - Usuarios del sistema (admin, recepcionista, dentistas)")
        print("  - Salas/sillones")
        print("  - Configuración de la clínica")
        
        confirmacion = input("\n¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
        
        if confirmacion != 'SI':
            print("Operación cancelada.")
            return
        
        try:
            # Eliminar en orden para respetar foreign keys
            print("\nEliminando datos...")
            
            # Notificaciones
            count = Notification.query.delete()
            print(f"  ✓ Eliminadas {count} notificaciones")
            
            # Pagos
            count = Payment.query.delete()
            print(f"  ✓ Eliminados {count} pagos")
            
            # Facturas
            count = Invoice.query.delete()
            print(f"  ✓ Eliminadas {count} facturas")
            
            # Items de tratamiento
            count = TreatmentItem.query.delete()
            print(f"  ✓ Eliminados {count} items de tratamiento")
            
            # Planes de tratamiento
            count = TreatmentPlan.query.delete()
            print(f"  ✓ Eliminados {count} planes de tratamiento")
            
            # Odontogramas
            count = Odontogram.query.delete()
            print(f"  ✓ Eliminados {count} odontogramas")
            
            # Registros clínicos
            count = ClinicalRecord.query.delete()
            print(f"  ✓ Eliminados {count} registros clínicos")
            
            # Citas
            count = Appointment.query.delete()
            print(f"  ✓ Eliminadas {count} citas")
            
            # Pacientes
            count = Patient.query.delete()
            print(f"  ✓ Eliminados {count} pacientes")
            
            db.session.commit()
            
            print("\n✓ Limpieza completada correctamente.")
            print("\nLa base de datos ahora está limpia y lista para uso en producción.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error durante la limpieza: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    clean_sample_data()


