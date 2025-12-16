"""
Script para generar 50 pacientes de muestra con tratamientos.
Ejecutar: python generate_sample_data.py
"""
from app import create_app, db
from app.models import Patient, User, TreatmentPlan, TreatmentItem, Appointment, ClinicalRecord
from datetime import datetime, timedelta, date
import random

# Nombres y apellidos españoles comunes
NOMBRES = [
    'María', 'Carmen', 'Ana', 'Laura', 'Isabel', 'Patricia', 'Lucía', 'Sandra',
    'José', 'Antonio', 'Manuel', 'Juan', 'Francisco', 'Carlos', 'Miguel', 'Luis',
    'Elena', 'Marta', 'Cristina', 'Paula', 'Sara', 'Andrea', 'Natalia', 'Raquel',
    'Pedro', 'Javier', 'Ángel', 'Pablo', 'David', 'Daniel', 'Alejandro', 'Roberto'
]

APELLIDOS = [
    'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez',
    'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno',
    'Álvarez', 'Muñoz', 'Romero', 'Alonso', 'Gutiérrez', 'Navarro', 'Torres', 'Domínguez',
    'Vázquez', 'Ramos', 'Gil', 'Ramírez', 'Serrano', 'Blanco', 'Suárez', 'Molina'
]

TRATAMIENTOS = [
    ('Limpieza dental profesional', None, 50.00),
    ('Empaste pieza', '2.6', 80.00),
    ('Empaste pieza', '3.6', 80.00),
    ('Empaste pieza', '1.4', 80.00),
    ('Empaste pieza', '4.4', 80.00),
    ('Endodoncia', '2.6', 300.00),
    ('Endodoncia', '3.6', 300.00),
    ('Corona cerámica', '1.1', 450.00),
    ('Corona cerámica', '2.1', 450.00),
    ('Blanqueamiento dental', None, 250.00),
    ('Extracción', '1.8', 60.00),
    ('Extracción', '2.8', 60.00),
    ('Extracción', '3.8', 60.00),
    ('Extracción', '4.8', 60.00),
    ('Ortodoncia brackets metálicos', None, 3000.00),
    ('Ortodoncia brackets estéticos', None, 3500.00),
    ('Invisalign', None, 4000.00),
    ('Implante dental', '1.6', 1200.00),
    ('Implante dental', '2.6', 1200.00),
    ('Carilla dental', '1.1', 300.00),
    ('Carilla dental', '2.1', 300.00),
    ('Revisión y diagnóstico', None, 40.00),
    ('Radiografía panorámica', None, 35.00),
    ('Curetaje', None, 120.00),
    ('Férula de descarga', None, 350.00),
]

MOTIVOS_CITA = [
    'Revisión rutinaria',
    'Dolor de muelas',
    'Limpieza dental',
    'Consulta por caries',
    'Consulta estética',
    'Ortodoncia',
    'Endodoncia',
    'Extracción',
    'Implante',
    'Seguimiento tratamiento',
    'Urgencia dental',
    'Blanqueamiento',
]

def generar_email(nombre, apellido):
    """Genera un email único."""
    base = f"{nombre.lower()}.{apellido.lower()}"
    # Añadir número si ya existe
    contador = 1
    email = f"{base}@email.com"
    while Patient.query.filter_by(email=email).first():
        email = f"{base}{contador}@email.com"
        contador += 1
    return email

def generar_telefono():
    """Genera un número de teléfono español."""
    return f"6{random.randint(10000000, 99999999)}"

def generar_dni():
    """Genera un DNI español."""
    numero = random.randint(10000000, 99999999)
    letras = 'TRWAGMYFPDXBNJZSQVHLCKE'
    letra = letras[numero % 23]
    return f"{numero}{letra}"

def crear_paciente():
    """Crea un paciente con datos aleatorios."""
    nombre = random.choice(NOMBRES)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    
    # Fecha de nacimiento entre 18 y 80 años
    edad = random.randint(18, 80)
    fecha_nacimiento = date.today() - timedelta(days=edad*365 + random.randint(0, 365))
    
    paciente = Patient(
        nombre=nombre,
        apellidos=f"{apellido1} {apellido2}",
        email=generar_email(nombre, apellido1),
        telefono=generar_telefono(),
        dni=generar_dni(),
        fecha_nacimiento=fecha_nacimiento,
        direccion=f"Calle {random.choice(['Mayor', 'Real', 'Nueva', 'San', 'Santa'])} {random.randint(1, 200)}, {random.randint(10000, 99999)}",
        fecha_alta=datetime.now() - timedelta(days=random.randint(1, 365*2)),
        activo=True
    )
    
    # Establecer contraseña por defecto
    paciente.set_password('paciente123')
    
    return paciente

def crear_tratamiento(paciente, dentista):
    """Crea un plan de tratamiento para un paciente."""
    # 70% de probabilidad de tener tratamiento activo
    if random.random() > 0.3:
        estado = random.choice(['propuesto', 'en_curso', 'finalizado'])
        
        descripciones = [
            'Tratamiento de ortodoncia',
            'Plan de restauración dental',
            'Tratamiento de periodoncia',
            'Plan de implantes',
            'Tratamiento estético',
            'Rehabilitación oral',
            'Tratamiento conservador',
        ]
        
        plan = TreatmentPlan(
            patient_id=paciente.id,
            dentist_id=dentista.id,
            descripcion_general=random.choice(descripciones),
            estado=estado,
            coste_estimado=0
        )
        
        db.session.add(plan)
        db.session.flush()
        
        # Añadir 2-5 actos al plan
        num_actos = random.randint(2, 5)
        tratamientos_seleccionados = random.sample(TRATAMIENTOS, min(num_actos, len(TRATAMIENTOS)))
        
        total_coste = 0
        for i, (nombre, pieza, precio) in enumerate(tratamientos_seleccionados):
            fecha_prevista = date.today() + timedelta(days=random.randint(0, 90))
            
            # Si el plan está finalizado o en curso, algunos actos pueden estar realizados
            if estado in ['en_curso', 'finalizado']:
                estado_acto = random.choice(['pendiente', 'realizado', 'realizado'])
                fecha_realizacion = fecha_prevista - timedelta(days=random.randint(0, 30)) if estado_acto == 'realizado' else None
            else:
                estado_acto = 'pendiente'
                fecha_realizacion = None
            
            item = TreatmentItem(
                treatment_plan_id=plan.id,
                nombre_tratamiento=nombre,
                pieza_dental=pieza,
                fecha_prevista=fecha_prevista,
                fecha_realizacion=fecha_realizacion,
                estado=estado_acto,
                precio=precio
            )
            
            total_coste += precio
            db.session.add(item)
        
        plan.coste_estimado = total_coste
        return plan
    
    return None

def crear_citas(paciente, dentistas):
    """Crea citas pasadas y futuras para un paciente."""
    citas = []
    
    # 1-3 citas pasadas
    num_pasadas = random.randint(1, 3)
    for _ in range(num_pasadas):
        fecha = datetime.now() - timedelta(days=random.randint(1, 180))
        hora = random.randint(9, 19)
        minuto = random.choice([0, 30])
        
        cita = Appointment(
            patient_id=paciente.id,
            dentist_id=random.choice(dentistas).id,
            fecha_hora_inicio=datetime.combine(fecha.date(), datetime.min.time().replace(hour=hora, minute=minuto)),
            fecha_hora_fin=datetime.combine(fecha.date(), datetime.min.time().replace(hour=hora, minute=minuto)) + timedelta(minutes=30),
            motivo=random.choice(MOTIVOS_CITA),
            estado=random.choice(['realizada', 'confirmada', 'realizada']),
            sillon=f"Sillón {random.randint(1, 5)}"
        )
        citas.append(cita)
    
    # 0-2 citas futuras
    num_futuras = random.randint(0, 2)
    for _ in range(num_futuras):
        fecha = datetime.now() + timedelta(days=random.randint(1, 60))
        hora = random.randint(9, 19)
        minuto = random.choice([0, 30])
        
        cita = Appointment(
            patient_id=paciente.id,
            dentist_id=random.choice(dentistas).id,
            fecha_hora_inicio=datetime.combine(fecha.date(), datetime.min.time().replace(hour=hora, minute=minuto)),
            fecha_hora_fin=datetime.combine(fecha.date(), datetime.min.time().replace(hour=hora, minute=minuto)) + timedelta(minutes=30),
            motivo=random.choice(MOTIVOS_CITA),
            estado=random.choice(['programada', 'confirmada']),
            sillon=f"Sillón {random.randint(1, 5)}"
        )
        citas.append(cita)
    
    return citas

def crear_historia_clinica(paciente):
    """Crea una historia clínica básica."""
    antecedentes = [
        'Hipertensión controlada',
        'Diabetes tipo 2',
        'Asma',
        'Alergia a penicilina',
        'Ninguno',
        'Hipertensión',
    ]
    
    alergias = [
        'Penicilina',
        'Látex',
        'Ninguna conocida',
        'Anestesia local (lidocaína)',
    ]
    
    medicacion = [
        'Metformina 500mg',
        'Enalapril 10mg',
        'Ventolin inhalador',
        'Ninguna',
        'Aspirina 100mg',
    ]
    
    record = ClinicalRecord(
        patient_id=paciente.id,
        antecedentes_medicos=random.choice(antecedentes),
        alergias=random.choice(alergias),
        medicacion=random.choice(medicacion),
        observaciones_generales=f"Paciente colaborador. Última revisión: {datetime.now().strftime('%d/%m/%Y')}"
    )
    
    return record

def main():
    """Función principal."""
    app = create_app()
    
    with app.app_context():
        print("Generando 50 pacientes de muestra...")
        
        # Obtener dentistas
        dentistas = User.query.filter_by(rol='dentista', activo=True).all()
        if not dentistas:
            print("⚠ Error: No hay dentistas en la base de datos. Ejecuta init_db.py primero.")
            return
        
        pacientes_creados = 0
        
        for i in range(50):
            try:
                # Crear paciente
                paciente = crear_paciente()
                db.session.add(paciente)
                db.session.flush()
                
                # Crear historia clínica (80% probabilidad)
                if random.random() > 0.2:
                    record = crear_historia_clinica(paciente)
                    db.session.add(record)
                
                # Crear tratamiento
                dentista = random.choice(dentistas)
                plan = crear_tratamiento(paciente, dentista)
                
                # Crear citas
                citas = crear_citas(paciente, dentistas)
                for cita in citas:
                    db.session.add(cita)
                
                pacientes_creados += 1
                
                if (i + 1) % 10 == 0:
                    print(f"  Procesados {i + 1}/50 pacientes...")
                    db.session.commit()
            
            except Exception as e:
                db.session.rollback()
                print(f"  Error al crear paciente {i + 1}: {e}")
                continue
        
        # Commit final
        db.session.commit()
        
        print(f"\n✓ Proceso completado. Se crearon {pacientes_creados} pacientes de muestra.")
        print("\nDatos generados:")
        print(f"  - Pacientes: {pacientes_creados}")
        print(f"  - Tratamientos: {TreatmentPlan.query.count()}")
        print(f"  - Actos de tratamiento: {TreatmentItem.query.count()}")
        print(f"  - Citas: {Appointment.query.count()}")
        print(f"  - Historias clínicas: {ClinicalRecord.query.count()}")
        print("\nTodos los pacientes tienen la contraseña: paciente123")

if __name__ == '__main__':
    main()




