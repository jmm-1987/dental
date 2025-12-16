"""
Script para generar 10 registros de prueba en cada apartado del sistema.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app, db
from app.models import (
    User, Patient, Appointment, ClinicalRecord, Odontogram,
    TreatmentPlan, TreatmentItem, Invoice, Payment, Notification,
    Room, ClinicSettings, DoctorSchedule, TimeClock, DayOff, Honorario
)
from datetime import datetime, timedelta, date, time
import random

app = create_app()

# Datos de prueba
NOMBRES = ['María', 'José', 'Ana', 'Carlos', 'Laura', 'Miguel', 'Carmen', 'David', 'Sofía', 'Juan']
APELLIDOS = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín']
TRATAMIENTOS = [
    'Limpieza dental profesional',
    'Empaste pieza',
    'Endodoncia',
    'Corona cerámica',
    'Blanqueamiento dental',
    'Extracción',
    'Ortodoncia brackets metálicos',
    'Implante dental',
    'Carilla dental',
    'Revisión y diagnóstico'
]

def generar_datos_prueba():
    """Genera 10 registros de prueba en cada apartado."""
    with app.app_context():
        try:
            # 1. SALAS (Rooms) - 10 salas
            print("\n[1/10] Creando 10 Salas...")
            salas_existentes = Room.query.count()
            salas_creadas = 0
            if salas_existentes < 10:
                for i in range(1, 11):
                    nombre_sala = f"Sala {i}"
                    sala_existente = Room.query.filter_by(nombre=nombre_sala).first()
                    if not sala_existente:
                        sala = Room(
                            nombre=nombre_sala,
                            descripcion=f"Sala de consulta {i}",
                            activo=True
                        )
                        db.session.add(sala)
                        salas_creadas += 1
                db.session.commit()
                print(f"  ✓ Creadas {salas_creadas} salas nuevas")
            else:
                print(f"  - Ya existen {salas_existentes} salas")
            
            # 2. USUARIOS (Users) - 10 usuarios adicionales (auxiliares y comerciales)
            print("\n[2/10] Creando 10 Usuarios adicionales...")
            usuarios_existentes = User.query.filter(User.rol.in_(['auxiliar', 'comercial'])).count()
            usuarios_creados = 0
            if usuarios_existentes < 10:
                roles_adicionales = ['auxiliar', 'comercial'] * 5
                for i, rol in enumerate(roles_adicionales[:10]):
                    email = f"{rol}{i+1}@clinicadental.com"
                    usuario_existente = User.query.filter_by(email=email).first()
                    if not usuario_existente:
                        usuario = User(
                            nombre=f"{NOMBRES[i]} {APELLIDOS[i]}",
                            email=email,
                            rol=rol,
                            activo=True
                        )
                        usuario.set_password('123456')
                        db.session.add(usuario)
                        usuarios_creados += 1
                db.session.commit()
                print(f"  ✓ Creados {usuarios_creados} usuarios adicionales")
            else:
                print(f"  - Ya existen {usuarios_existentes} usuarios adicionales")
            
            # 3. PACIENTES (Patients) - 10 pacientes adicionales
            print("\n[3/10] Creando 10 Pacientes adicionales...")
            pacientes_existentes = Patient.query.count()
            pacientes_creados = 0
            if pacientes_existentes < 10:
                for i in range(10):
                    email = f"paciente_test{i+1}@email.com"
                    dni = f"{random.randint(10000000, 99999999)}{chr(random.randint(65, 90))}"
                    paciente_existente = Patient.query.filter((Patient.email == email) | (Patient.dni == dni)).first()
                    if not paciente_existente:
                        paciente = Patient(
                            nombre=NOMBRES[i],
                            apellidos=APELLIDOS[i],
                            email=email,
                            telefono=f"6{random.randint(10000000, 99999999)}",
                            fecha_nacimiento=date(1980 + random.randint(0, 40), random.randint(1, 12), random.randint(1, 28)),
                            direccion=f"Calle {NOMBRES[i]} {random.randint(1, 100)}",
                            dni=dni,
                            activo=True
                        )
                        db.session.add(paciente)
                        pacientes_creados += 1
                db.session.commit()
                print(f"  ✓ Creados {pacientes_creados} pacientes adicionales")
            else:
                print(f"  - Ya existen {pacientes_existentes} pacientes")
            
            # 4. CITAS (Appointments) - 50 citas
            print("\n[4/10] Creando 50 Citas...")
            doctores = User.query.filter_by(rol='dentista', activo=True).all()
            pacientes = Patient.query.filter_by(activo=True).all()
            salas = Room.query.filter_by(activo=True).all()
            citas_existentes = Appointment.query.count()
            
            if doctores and pacientes and salas:
                fecha_base = date.today()
                citas_creadas = 0
                objetivo_citas = 50
                
                for i in range(objetivo_citas):
                    # Crear citas distribuidas en un rango de 90 días (pasado y futuro)
                    fecha_cita = fecha_base + timedelta(days=random.randint(-60, 30))
                    hora_base = random.randint(8, 19)
                    minuto = random.choice([0, 30])
                    hora_inicio = datetime.combine(fecha_cita, time(hora_base, minuto))
                    hora_fin = hora_inicio + timedelta(minutes=random.choice([30, 60, 90]))
                    
                    # Evitar solapamientos básicos verificando si ya existe una cita en ese momento
                    cita_existente = Appointment.query.filter(
                        Appointment.dentist_id == random.choice(doctores).id,
                        Appointment.fecha_hora_inicio == hora_inicio
                    ).first()
                    
                    if not cita_existente:
                        cita = Appointment(
                            patient_id=random.choice(pacientes).id,
                            dentist_id=random.choice(doctores).id,
                            fecha_hora_inicio=hora_inicio,
                            fecha_hora_fin=hora_fin,
                            room_id=random.choice(salas).id if salas else None,
                            motivo=random.choice([
                                'Revisión rutinaria', 'Dolor de muelas', 'Limpieza dental',
                                'Consulta por caries', 'Consulta estética', 'Ortodoncia',
                                'Endodoncia', 'Extracción', 'Implante', 'Seguimiento tratamiento',
                                'Urgencia dental', 'Blanqueamiento'
                            ]),
                            estado=random.choice(['programada', 'confirmada', 'realizada', 'cancelada'])
                        )
                        db.session.add(cita)
                        citas_creadas += 1
                        
                        # Hacer commit cada 10 citas para evitar problemas
                        if citas_creadas % 10 == 0:
                            db.session.commit()
                
                db.session.commit()
                print(f"  ✓ Creadas {citas_creadas} citas nuevas (total: {citas_existentes + citas_creadas})")
            else:
                print(f"  - Ya existen {citas_existentes} citas o faltan datos base")
            
            # 5. HISTORIAS CLÍNICAS (ClinicalRecord) - 10 historias
            print("\n[5/10] Creando 10 Historias Clínicas...")
            pacientes = Patient.query.filter_by(activo=True).limit(10).all()
            historias_existentes = ClinicalRecord.query.count()
            historias_creadas = 0
            
            if pacientes and historias_existentes < 10:
                for paciente in pacientes[:10]:
                    historia_existente = ClinicalRecord.query.filter_by(patient_id=paciente.id).first()
                    if not historia_existente:
                        historia = ClinicalRecord(
                            patient_id=paciente.id,
                            antecedentes_medicos=f"Antecedentes del paciente {paciente.nombre}",
                            alergias=random.choice(['Ninguna', 'Penicilina', 'Anestesia local', 'Latex']),
                            medicacion=f"Medicación {random.randint(1, 5)}",
                            observaciones_generales=f"Observaciones para {paciente.nombre}"
                        )
                        db.session.add(historia)
                        historias_creadas += 1
                db.session.commit()
                print(f"  ✓ Creadas {historias_creadas} historias clínicas")
            else:
                print(f"  - Ya existen {historias_existentes} historias clínicas")
            
            # 6. ODONTOGRAMAS (Odontogram) - Rellenar odontogramas existentes y crear nuevos
            print("\n[6/10] Rellenando Odontogramas con datos...")
            pacientes = Patient.query.filter_by(activo=True).all()
            odontogramas_actualizados = 0
            odontogramas_creados = 0
            
            import json
            
            # Estados posibles para las piezas dentales
            estados_posibles = ['sano', 'caries', 'empaste', 'extraccion', 'corona', 'endodoncia', 'implante']
            
            for paciente in pacientes[:20]:  # Procesar hasta 20 pacientes
                odontogram = Odontogram.query.filter_by(patient_id=paciente.id).first()
                
                # Crear datos realistas del odontograma
                datos_piezas = {}
                # Piezas superiores (1.1 a 1.8 y 2.1 a 2.8)
                for cuadrante in [1, 2]:
                    for pieza in [1, 2, 3, 4, 5, 6, 7, 8]:
                        pieza_key = f"{cuadrante}.{pieza}"
                        # Algunas piezas sanas, otras con problemas
                        if random.random() < 0.3:  # 30% tienen algún problema
                            datos_piezas[pieza_key] = {
                                'estado': random.choice(['caries', 'empaste', 'corona', 'endodoncia']),
                                'notas': random.choice(['', 'Requiere atención', 'Seguimiento']) if random.choice([True, False]) else ''
                            }
                        else:
                            datos_piezas[pieza_key] = {'estado': 'sano'}
                
                # Piezas inferiores (3.1 a 3.8 y 4.1 a 4.8)
                for cuadrante in [3, 4]:
                    for pieza in [1, 2, 3, 4, 5, 6, 7, 8]:
                        pieza_key = f"{cuadrante}.{pieza}"
                        if random.random() < 0.3:  # 30% tienen algún problema
                            datos_piezas[pieza_key] = {
                                'estado': random.choice(['caries', 'empaste', 'corona', 'endodoncia', 'extraccion']),
                                'notas': random.choice(['', 'Requiere atención', 'Seguimiento']) if random.choice([True, False]) else ''
                            }
                        else:
                            datos_piezas[pieza_key] = {'estado': 'sano'}
                
                # Convertir a JSON
                datos_json = json.dumps(datos_piezas, ensure_ascii=False)
                
                if odontogram:
                    # Actualizar odontograma existente
                    odontogram.datos_json = datos_json
                    odontogram.notas = f"Odontograma actualizado de {paciente.nombre_completo()}"
                    odontogramas_actualizados += 1
                else:
                    # Crear nuevo odontograma
                    odontogram = Odontogram(
                        patient_id=paciente.id,
                        datos_json=datos_json,
                        notas=f"Odontograma completo de {paciente.nombre_completo()}"
                    )
                    db.session.add(odontogram)
                    odontogramas_creados += 1
            
            db.session.commit()
            print(f"  ✓ Actualizados {odontogramas_actualizados} odontogramas y creados {odontogramas_creados} nuevos")
            
            # 7. PLANES DE TRATAMIENTO (TreatmentPlan) - 10 planes
            print("\n[7/10] Creando 10 Planes de Tratamiento...")
            doctores = User.query.filter_by(rol='dentista', activo=True).all()
            pacientes = Patient.query.filter_by(activo=True).limit(10).all()
            planes_existentes = TreatmentPlan.query.count()
            
            if doctores and pacientes and planes_existentes < 10:
                planes_creados = 0
                for i in range(10):
                    plan = TreatmentPlan(
                        patient_id=random.choice(pacientes).id,
                        dentist_id=random.choice(doctores).id,
                        descripcion_general=f"Plan de tratamiento prueba {i+1}",
                        estado=random.choice(['propuesto', 'en_curso', 'finalizado']),
                        coste_estimado=random.uniform(100, 2000)
                    )
                    db.session.add(plan)
                    db.session.flush()  # Para obtener el ID
                    
                    # Añadir 2-3 items por plan
                    num_items = random.randint(2, 3)
                    tratamiento_nombres = random.sample(TRATAMIENTOS, min(num_items, len(TRATAMIENTOS)))
                    for j, nombre_trat in enumerate(tratamiento_nombres):
                        item = TreatmentItem(
                            treatment_plan_id=plan.id,
                            nombre_tratamiento=nombre_trat,
                            pieza_dental=f"{random.randint(1, 4)}.{random.randint(1, 8)}" if random.choice([True, False]) else None,
                            fecha_prevista=date.today() + timedelta(days=random.randint(1, 60)),
                            estado=random.choice(['pendiente', 'realizado', 'cancelado']),
                            precio=random.uniform(50, 500)
                        )
                        if item.estado == 'realizado':
                            item.fecha_realizacion = date.today() - timedelta(days=random.randint(1, 30))
                        db.session.add(item)
                    planes_creados += 1
                db.session.commit()
                print(f"  ✓ Creados {planes_creados} planes de tratamiento con items")
            else:
                print(f"  - Ya existen {planes_existentes} planes o faltan datos base")
            
            # 8. FACTURAS (Invoice) - 10 facturas
            print("\n[8/10] Creando 10 Facturas...")
            pacientes = Patient.query.filter_by(activo=True).limit(10).all()
            facturas_existentes = Invoice.query.count()
            
            if pacientes and facturas_existentes < 10:
                facturas_creadas = 0
                for i in range(10):
                    factura = Invoice(
                        patient_id=random.choice(pacientes).id,
                        fecha_emision=datetime.now() - timedelta(days=random.randint(0, 90)),
                        total=random.uniform(100, 1500),
                        estado_pago=random.choice(['pendiente', 'pagado', 'parcial']),
                        metodo_pago=random.choice(['efectivo', 'tarjeta', 'transferencia']) if random.choice([True, False]) else None
                    )
                    db.session.add(factura)
                    db.session.flush()
                    
                    # Añadir pagos si está pagado o parcial
                    if factura.estado_pago in ['pagado', 'parcial']:
                        cantidad_pago = float(factura.total) if factura.estado_pago == 'pagado' else float(factura.total) * 0.5
                        pago = Payment(
                            invoice_id=factura.id,
                            fecha_pago=factura.fecha_emision + timedelta(days=random.randint(1, 30)),
                            cantidad=cantidad_pago,
                            metodo_pago=factura.metodo_pago or 'efectivo',
                            referencia=f"REF{random.randint(1000, 9999)}"
                        )
                        db.session.add(pago)
                    facturas_creadas += 1
                db.session.commit()
                print(f"  ✓ Creadas {facturas_creadas} facturas con pagos")
            else:
                print(f"  - Ya existen {facturas_existentes} facturas o faltan pacientes")
            
            # 9. HONORARIOS (Honorario) - 10 honorarios
            print("\n[9/10] Creando 10 Honorarios...")
            doctores = User.query.filter_by(rol='dentista', activo=True).all()
            tratamientos_items = db.session.query(TreatmentItem.nombre_tratamiento).distinct().limit(10).all()
            
            if doctores and tratamientos_items:
                tratamientos_nombres = [t[0] for t in tratamientos_items]
                honorarios_existentes = Honorario.query.count()
                honorarios_creados = 0
                
                if honorarios_existentes < 10:
                    for i, tratamiento_nombre in enumerate(tratamientos_nombres[:10]):
                        doctor = random.choice(doctores)
                        # Verificar si ya existe
                        existe = Honorario.query.filter_by(
                            doctor_id=doctor.id,
                            nombre_tratamiento=tratamiento_nombre
                        ).first()
                        
                        if not existe:
                            honorario = Honorario(
                                doctor_id=doctor.id,
                                nombre_tratamiento=tratamiento_nombre,
                                precio=random.uniform(20, 300)
                            )
                            db.session.add(honorario)
                            honorarios_creados += 1
                    db.session.commit()
                    print(f"  ✓ Creados {honorarios_creados} honorarios adicionales")
                else:
                    print(f"  - Ya existen {honorarios_existentes} honorarios")
            else:
                print("  - Faltan doctores o tratamientos para crear honorarios")
            
            # 10. FICHAJES (TimeClock) - 50 fichajes
            print("\n[10/10] Creando 50 Fichajes...")
            empleados = User.query.filter(
                User.activo == True,
                User.rol.in_(['admin', 'recepcionista', 'dentista', 'auxiliar', 'comercial'])
            ).all()
            fichajes_existentes = TimeClock.query.count()
            
            if empleados:
                fecha_base = date.today()
                fichajes_creados = 0
                objetivo_fichajes = 50
                
                for i in range(objetivo_fichajes):
                    # Crear fichajes distribuidos en los últimos 60 días
                    fecha_fichaje = fecha_base - timedelta(days=random.randint(0, 60))
                    empleado = random.choice(empleados)
                    
                    # Verificar si ya existe un fichaje para este usuario y fecha
                    existe = TimeClock.query.filter_by(
                        user_id=empleado.id,
                        fecha=fecha_fichaje
                    ).first()
                    
                    if not existe:
                        # Horarios variados
                        hora_entrada_base = random.randint(7, 9)
                        hora_entrada = time(hora_entrada_base, random.choice([0, 15, 30, 45]))
                        
                        # Hora de salida entre 6 y 9 horas después
                        horas_trabajo = random.randint(6, 9)
                        hora_salida_h = hora_entrada_base + horas_trabajo
                        hora_salida_m = random.choice([0, 15, 30, 45])
                        if hora_salida_h >= 24:
                            hora_salida_h = 23
                            hora_salida_m = 0
                        hora_salida = time(hora_salida_h, hora_salida_m)
                        
                        fichaje = TimeClock(
                            user_id=empleado.id,
                            fecha=fecha_fichaje,
                            hora_entrada=hora_entrada,
                            hora_salida=hora_salida,
                            notas=random.choice([None, 'Jornada normal', 'Horas extras', 'Permiso médico']) if random.choice([True, False]) else None
                        )
                        fichaje.calcular_horas()
                        db.session.add(fichaje)
                        fichajes_creados += 1
                        
                        # Hacer commit cada 10 fichajes para evitar problemas
                        if fichajes_creados % 10 == 0:
                            db.session.commit()
                
                db.session.commit()
                print(f"  ✓ Creados {fichajes_creados} fichajes nuevos (total: {fichajes_existentes + fichajes_creados})")
            else:
                print(f"  - Ya existen {fichajes_existentes} fichajes o faltan empleados")
            
            # Guardar todos los cambios
            db.session.commit()
            print("\n" + "="*50)
            print("[OK] Todos los datos de prueba han sido creados correctamente.")
            print("="*50)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error al crear datos de prueba: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    generar_datos_prueba()

