"""
Script para añadir 60 citas ficticias entre el 1 y el 31 de enero.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import User, Patient, Appointment, Room
from datetime import datetime, timedelta, date, time
import random

app = create_app()

MOTIVOS = [
    'Revisión rutinaria', 'Dolor de muelas', 'Limpieza dental',
    'Consulta por caries', 'Consulta estética', 'Ortodoncia',
    'Endodoncia', 'Extracción', 'Implante', 'Seguimiento tratamiento',
    'Urgencia dental', 'Blanqueamiento', 'Radiografía', 'Curetaje',
    'Consulta preventiva', 'Revisión post-tratamiento', 'Consulta de seguimiento'
]

def añadir_citas_enero():
    """Añade 60 citas para enero (1-31 de enero)."""
    with app.app_context():
        try:
            # Obtener datos necesarios
            doctores = User.query.filter_by(rol='dentista', activo=True).all()
            pacientes = Patient.query.filter_by(activo=True).all()
            salas = Room.query.filter_by(activo=True).all()
            
            if not doctores:
                print("[ERROR] No hay doctores activos en la base de datos.")
                return
            
            if not pacientes:
                print("[ERROR] No hay pacientes activos en la base de datos.")
                return
            
            if not salas:
                print("[ADVERTENCIA] No hay salas activas. Las citas se crearán sin sala.")
            
            # Definir rango de fechas: 1 al 31 de enero de 2026
            inicio_enero = date(2026, 1, 1)
            fin_enero = date(2026, 1, 31)
            
            print(f"\nAñadiendo 60 citas para enero de 2026")
            print(f"Rango: {inicio_enero.strftime('%d/%m/%Y')} al {fin_enero.strftime('%d/%m/%Y')}")
            
            citas_creadas = 0
            horas_disponibles = []
            
            # Generar horas disponibles (9:00 a 20:00 en tramos de 30 minutos)
            for hora in range(9, 20):
                horas_disponibles.append(time(hora, 0))
                horas_disponibles.append(time(hora, 30))
            
            # Crear 60 citas distribuidas aleatoriamente
            intentos = 0
            max_intentos = 1000  # Evitar bucle infinito
            
            while citas_creadas < 60 and intentos < max_intentos:
                intentos += 1
                
                # Seleccionar fecha aleatoria en enero
                dias_desde_inicio = random.randint(0, 30)
                fecha_cita = inicio_enero + timedelta(days=dias_desde_inicio)
                
                # No crear citas en domingos (día 6)
                if fecha_cita.weekday() == 6:  # Domingo
                    continue
                
                # Seleccionar hora aleatoria
                hora_disponible = random.choice(horas_disponibles)
                hora_inicio = datetime.combine(fecha_cita, hora_disponible)
                
                # Duración aleatoria: 30, 60 o 90 minutos
                duracion = random.choice([30, 60, 90])
                hora_fin = hora_inicio + timedelta(minutes=duracion)
                
                # Seleccionar doctor, paciente y sala aleatorios
                doctor = random.choice(doctores)
                paciente = random.choice(pacientes)
                sala = random.choice(salas) if salas else None
                
                # Verificar que no haya conflicto de horario con el mismo doctor
                conflicto = Appointment.query.filter(
                    Appointment.dentist_id == doctor.id,
                    Appointment.estado.in_(['programada', 'confirmada']),
                    Appointment.fecha_hora_inicio < hora_fin,
                    Appointment.fecha_hora_fin > hora_inicio
                ).first()
                
                if conflicto:
                    continue  # Intentar con otra fecha/hora
                
                # Crear la cita
                cita = Appointment(
                    patient_id=paciente.id,
                    dentist_id=doctor.id,
                    fecha_hora_inicio=hora_inicio,
                    fecha_hora_fin=hora_fin,
                    room_id=sala.id if sala else None,
                    sillon=sala.nombre if sala else None,
                    motivo=random.choice(MOTIVOS),
                    estado=random.choice(['programada', 'confirmada'])
                )
                
                db.session.add(cita)
                citas_creadas += 1
                
                # Commit cada 10 citas
                if citas_creadas % 10 == 0:
                    db.session.commit()
                    print(f"  Creadas {citas_creadas} citas...")
            
            db.session.commit()
            
            if citas_creadas < 60:
                print(f"\n[ADVERTENCIA] Solo se pudieron crear {citas_creadas} citas (de 60 solicitadas)")
                print(f"             Posiblemente debido a conflictos de horario.")
            else:
                print(f"\n[OK] Creadas {citas_creadas} citas para enero de 2026.")
            
            print(f"     Rango: {inicio_enero.strftime('%d/%m/%Y')} - {fin_enero.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al crear citas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    añadir_citas_enero()

