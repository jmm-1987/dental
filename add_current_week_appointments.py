"""
Script para añadir citas para la semana actual y las próximas semanas.
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

def añadir_citas_semanas_actuales():
    """Añade citas para la semana actual y las próximas 3 semanas."""
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
            
            # Calcular inicio de la semana actual (lunes)
            hoy = date.today()
            inicio_semana_actual = hoy - timedelta(days=hoy.weekday())
            
            print(f"\nAñadiendo citas para las próximas 4 semanas")
            print(f"Desde: {inicio_semana_actual.strftime('%d/%m/%Y')}")
            
            citas_creadas = 0
            horas_disponibles = []
            
            # Generar horas disponibles (9:00 a 20:00 en tramos de 30 minutos)
            for hora in range(9, 20):
                horas_disponibles.append(time(hora, 0))
                horas_disponibles.append(time(hora, 30))
            
            # Crear citas para las próximas 4 semanas
            for semana in range(4):
                inicio_semana = inicio_semana_actual + timedelta(weeks=semana)
                fin_semana = inicio_semana + timedelta(days=6)
                
                print(f"\n  Semana {semana + 1}: {inicio_semana.strftime('%d/%m/%Y')} - {fin_semana.strftime('%d/%m/%Y')}")
                
                # Crear entre 8 y 15 citas por semana
                num_citas_semana = random.randint(8, 15)
                citas_semana = 0
                
                for i in range(num_citas_semana):
                    # Seleccionar día aleatorio de la semana (lunes a sábado, no domingo)
                    dia_semana = random.randint(0, 5)  # 0=lunes, 5=sábado
                    fecha_cita = inicio_semana + timedelta(days=dia_semana)
                    
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
                    citas_semana += 1
                    
                    # Commit cada 10 citas
                    if citas_creadas % 10 == 0:
                        db.session.commit()
                        print(f"    Creadas {citas_creadas} citas en total...")
                
                print(f"    Creadas {citas_semana} citas para esta semana")
            
            db.session.commit()
            
            print(f"\n[OK] Creadas {citas_creadas} citas para las próximas 4 semanas.")
            print(f"     Desde: {inicio_semana_actual.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al crear citas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    añadir_citas_semanas_actuales()

