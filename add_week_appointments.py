"""
Script para añadir más citas para la semana actual.
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
    'Urgencia dental', 'Blanqueamiento', 'Radiografía', 'Curetaje'
]

def añadir_citas_semana():
    """Añade citas para la semana actual."""
    with app.app_context():
        try:
            # Obtener datos necesarios
            doctores = User.query.filter_by(rol='dentista', activo=True).all()
            pacientes = Patient.query.filter_by(activo=True).all()
            salas = Room.query.filter_by(activo=True).all()
            
            if not doctores or not pacientes or not salas:
                print("[ERROR] Faltan doctores, pacientes o salas en la base de datos.")
                return
            
            # Calcular inicio y fin de la semana actual (lunes a domingo)
            hoy = date.today()
            inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes
            fin_semana = inicio_semana + timedelta(days=6)  # Domingo
            
            print(f"\nAñadiendo citas para la semana del {inicio_semana.strftime('%d/%m/%Y')} al {fin_semana.strftime('%d/%m/%Y')}")
            
            citas_creadas = 0
            horas_disponibles = []
            
            # Generar horas disponibles (8:00 a 20:00 en tramos de 30 minutos)
            for hora in range(8, 20):
                horas_disponibles.append(time(hora, 0))
                horas_disponibles.append(time(hora, 30))
            
            # Crear citas para cada día de la semana
            for dia_offset in range(7):
                fecha_cita = inicio_semana + timedelta(days=dia_offset)
                dia_nombre = fecha_cita.strftime('%A')
                
                # Crear entre 5 y 10 citas por día
                num_citas_dia = random.randint(5, 10)
                horas_usadas = set()
                
                for i in range(num_citas_dia):
                    # Seleccionar hora aleatoria que no esté ya usada
                    hora_disponible = None
                    intentos = 0
                    while hora_disponible is None and intentos < 50:
                        hora_candidata = random.choice(horas_disponibles)
                        hora_key = f"{fecha_cita}_{hora_candidata}"
                        if hora_key not in horas_usadas:
                            hora_disponible = hora_candidata
                            horas_usadas.add(hora_key)
                        intentos += 1
                    
                    if hora_disponible:
                        hora_inicio = datetime.combine(fecha_cita, hora_disponible)
                        # Duración aleatoria: 30, 60 o 90 minutos
                        duracion = random.choice([30, 60, 90])
                        hora_fin = hora_inicio + timedelta(minutes=duracion)
                        
                        # Verificar que no haya solapamiento con citas existentes del mismo doctor
                        doctor = random.choice(doctores)
                        cita_existente = Appointment.query.filter(
                            Appointment.dentist_id == doctor.id,
                            Appointment.fecha_hora_inicio == hora_inicio
                        ).first()
                        
                        if not cita_existente:
                            cita = Appointment(
                                patient_id=random.choice(pacientes).id,
                                dentist_id=doctor.id,
                                fecha_hora_inicio=hora_inicio,
                                fecha_hora_fin=hora_fin,
                                room_id=random.choice(salas).id if salas else None,
                                motivo=random.choice(MOTIVOS),
                                estado=random.choice(['programada', 'confirmada'])
                            )
                            db.session.add(cita)
                            citas_creadas += 1
                            
                            # Commit cada 10 citas
                            if citas_creadas % 10 == 0:
                                db.session.commit()
            
            db.session.commit()
            print(f"\n[OK] Creadas {citas_creadas} citas para la semana actual.")
            print(f"     Semana: {inicio_semana.strftime('%d/%m/%Y')} - {fin_semana.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al crear citas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    añadir_citas_semana()

