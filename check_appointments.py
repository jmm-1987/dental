"""
Script para verificar las citas creadas.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import Appointment
from datetime import datetime, date, timedelta

app = create_app()

with app.app_context():
    # Contar todas las citas
    total_citas = Appointment.query.count()
    print(f"\nTotal de citas en la base de datos: {total_citas}")
    
    # Citas de enero 2025
    inicio_enero = datetime(2025, 1, 1)
    fin_enero = datetime(2025, 1, 31, 23, 59, 59)
    
    citas_enero = Appointment.query.filter(
        Appointment.fecha_hora_inicio >= inicio_enero,
        Appointment.fecha_hora_inicio <= fin_enero
    ).all()
    
    print(f"\nCitas en enero 2025: {len(citas_enero)}")
    
    if len(citas_enero) > 0:
        print("\nPrimeras 10 citas de enero:")
        for cita in citas_enero[:10]:
            print(f"  - {cita.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')} - {cita.patient.nombre_completo()} con {cita.dentist.nombre} - Estado: {cita.estado}")
    
    # Citas de la semana actual
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    inicio_semana = datetime.combine(start_of_week, datetime.min.time())
    fin_semana = datetime.combine(end_of_week, datetime.max.time())
    
    citas_semana = Appointment.query.filter(
        Appointment.fecha_hora_inicio >= inicio_semana,
        Appointment.fecha_hora_inicio <= fin_semana
    ).all()
    
    print(f"\nCitas de la semana actual ({start_of_week.strftime('%d/%m/%Y')} - {end_of_week.strftime('%d/%m/%Y')}): {len(citas_semana)}")
    
    if len(citas_semana) > 0:
        print("\nCitas de esta semana:")
        for cita in citas_semana:
            print(f"  - {cita.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')} - {cita.patient.nombre_completo()} con {cita.dentist.nombre} - Estado: {cita.estado}")

