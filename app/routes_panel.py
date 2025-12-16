"""
Rutas del panel interno de gestión (admin, recepcionista, dentistas).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from app import db
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from app.models import (
    User, Patient, Appointment, ClinicalRecord, Odontogram,
    TreatmentPlan, TreatmentItem, Invoice, Payment, Notification,
    Room, ClinicSettings, DoctorSchedule, TimeClock, DayOff, Honorario
)
from app.routes_auth import role_required
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

bp = Blueprint('panel', __name__)


@bp.route('/dashboard')
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def dashboard():
    """Panel principal con calendario semanal."""
    # Obtener semana actual
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    # Estadísticas básicas
    stats = {
        'total_pacientes': Patient.query.filter_by(activo=True).count(),
        'citas_hoy': Appointment.query.filter(
            Appointment.fecha_hora_inicio >= datetime.combine(today, datetime.min.time()),
            Appointment.fecha_hora_inicio < datetime.combine(today + timedelta(days=1), datetime.min.time())
        ).count(),
        'citas_pendientes': Appointment.query.filter_by(estado='programada').count(),
        'facturas_pendientes': Invoice.query.filter_by(estado_pago='pendiente').count()
    }
    
    # Si es dentista, filtrar solo sus citas
    if current_user.is_dentist():
        citas_hoy = Appointment.query.filter(
            Appointment.dentist_id == current_user.id,
            Appointment.fecha_hora_inicio >= datetime.combine(today, datetime.min.time()),
            Appointment.fecha_hora_inicio < datetime.combine(today + timedelta(days=1), datetime.min.time())
        ).all()
        stats['citas_hoy'] = len(citas_hoy)
    else:
        citas_hoy = Appointment.query.filter(
            Appointment.fecha_hora_inicio >= datetime.combine(today, datetime.min.time()),
            Appointment.fecha_hora_inicio < datetime.combine(today + timedelta(days=1), datetime.min.time())
        ).all()
    
    pacientes = Patient.query.filter_by(activo=True).order_by(Patient.apellidos).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    salas = Room.query.filter_by(activo=True).order_by(Room.nombre).all()
    
    # Convertir a diccionarios para JSON (solo si se necesitan en JavaScript)
    pacientes_json = [{'id': p.id, 'nombre': p.nombre_completo()} for p in pacientes]
    dentistas_json = [{'id': d.id, 'nombre': d.nombre} for d in dentistas]
    salas_json = [{'id': s.id, 'nombre': s.nombre} for s in salas]
    
    return render_template('panel/dashboard.html', 
                         stats=stats, 
                         citas_hoy=citas_hoy,
                         pacientes=pacientes,
                         dentistas=dentistas,
                         salas=salas,
                         pacientes_json=pacientes_json,
                         dentistas_json=dentistas_json,
                         salas_json=salas_json,
                         start_of_week=start_of_week)


@bp.route('/calendario/citas-semana')
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def calendario_citas_semana():
    """API para obtener citas de la semana en formato JSON."""
    fecha_str = request.args.get('fecha', None)
    
    if fecha_str:
        fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha_base = datetime.now().date()
    
    # Calcular inicio y fin de semana (lunes a domingo)
    start_of_week = fecha_base - timedelta(days=fecha_base.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    inicio_semana = datetime.combine(start_of_week, datetime.min.time())
    fin_semana = datetime.combine(end_of_week, datetime.max.time())
    
    # Obtener citas de la semana
    query = Appointment.query.filter(
        Appointment.fecha_hora_inicio >= inicio_semana,
        Appointment.fecha_hora_inicio <= fin_semana
    )
    
    # Si es dentista, solo sus citas
    if current_user.is_dentist():
        query = query.filter_by(dentist_id=current_user.id)
    
    citas = query.order_by(Appointment.fecha_hora_inicio).all()
    
    # Formatear citas para el calendario
    citas_json = []
    for cita in citas:
        citas_json.append({
            'id': cita.id,
            'patient_id': cita.patient_id,
            'patient_name': cita.patient.nombre_completo(),
            'dentist_id': cita.dentist_id,
            'dentist_name': cita.dentist.nombre,
            'start': cita.fecha_hora_inicio.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': cita.fecha_hora_fin.strftime('%Y-%m-%dT%H:%M:%S'),
            'sillon': cita.sillon or '',
            'motivo': cita.motivo or '',
            'estado': cita.estado
        })
    
    return jsonify({
        'start_of_week': start_of_week.strftime('%Y-%m-%d'),
        'end_of_week': end_of_week.strftime('%Y-%m-%d'),
        'citas': citas_json
    })


@bp.route('/calendario/crear-cita', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista')
def calendario_crear_cita():
    """Crear cita desde el calendario."""
    data = request.get_json()
    
    try:
        paciente_id = data.get('patient_id')
        dentist_id = data.get('dentist_id')
        
        # Parsear fechas en formato ISO (puede incluir milisegundos y Z)
        start_str = data.get('start')
        end_str = data.get('end')
        
        # Limpiar formato ISO: remover milisegundos y Z si existen
        start_str_clean = start_str.split('.')[0].replace('Z', '')
        end_str_clean = end_str.split('.')[0].replace('Z', '')
        
        # Parsear con formato estándar
        fecha_hora_inicio = datetime.strptime(start_str_clean, '%Y-%m-%dT%H:%M:%S')
        fecha_hora_fin = datetime.strptime(end_str_clean, '%Y-%m-%dT%H:%M:%S')
        
        motivo = data.get('motivo', '')
        sillon = data.get('sillon', '')
        
        # Verificar que el doctor trabaja ese día
        dia_semana = fecha_hora_inicio.weekday()
        horario_dia = DoctorSchedule.query.filter_by(
            doctor_id=dentist_id,
            dia_semana=dia_semana,
            activo=True
        ).first()
        
        if not horario_dia:
            return jsonify({'success': False, 'error': 'El doctor no trabaja ese día'}), 400
        
        # Verificar que la cita está dentro del horario de trabajo
        hora_inicio_cita = fecha_hora_inicio.time()
        hora_fin_cita = fecha_hora_fin.time()
        
        if hora_inicio_cita < horario_dia.hora_inicio or hora_fin_cita > horario_dia.hora_fin:
            return jsonify({'success': False, 'error': f'La cita debe estar entre {horario_dia.hora_inicio.strftime("%H:%M")} y {horario_dia.hora_fin.strftime("%H:%M")}'}), 400
        
        # Verificar que no haya conflicto de horario
        conflicto = Appointment.query.filter(
            Appointment.dentist_id == dentist_id,
            Appointment.estado.in_(['programada', 'confirmada']),
            Appointment.fecha_hora_inicio < fecha_hora_fin,
            Appointment.fecha_hora_fin > fecha_hora_inicio
        ).first()
        
        if conflicto:
            return jsonify({'success': False, 'error': 'El dentista ya tiene una cita en ese horario'}), 400
        
        room_id = data.get('room_id')
        room = Room.query.get(room_id) if room_id else None
        
        cita = Appointment(
            patient_id=paciente_id,
            dentist_id=dentist_id,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
            room_id=room_id,
            sillon=sillon or (room.nombre if room else None),
            motivo=motivo,
            estado='programada'
        )
        
        db.session.add(cita)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'cita': {
                'id': cita.id,
                'patient_name': cita.patient.nombre_completo(),
                'dentist_name': cita.dentist.nombre
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


# ==================== GESTIÓN DE PACIENTES ====================

@bp.route('/pacientes')
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def pacientes_list():
    """Listado de pacientes."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Patient.query.filter_by(activo=True)
    
    if search:
        query = query.filter(
            db.or_(
                Patient.nombre.ilike(f'%{search}%'),
                Patient.apellidos.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%'),
                Patient.dni.ilike(f'%{search}%')
            )
        )
    
    pacientes = query.order_by(Patient.apellidos, Patient.nombre).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('panel/pacientes/list.html', pacientes=pacientes, search=search)


@bp.route('/pacientes/<int:patient_id>')
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def paciente_detail(patient_id):
    """Detalle completo de un paciente."""
    paciente = Patient.query.get_or_404(patient_id)
    
    # Si es dentista, verificar que tenga relación con el paciente
    if current_user.is_dentist():
        tiene_relacion = Appointment.query.filter_by(
            patient_id=patient_id, dentist_id=current_user.id
        ).first() is not None or TreatmentPlan.query.filter_by(
            patient_id=patient_id, dentist_id=current_user.id
        ).first() is not None
        
        if not tiene_relacion:
            flash('No tienes acceso a este paciente.', 'error')
            return redirect(url_for('panel.pacientes_list'))
    
    # Obtener datos relacionados
    citas = paciente.appointments.order_by(Appointment.fecha_hora_inicio.desc()).limit(10).all()
    clinical_record = paciente.clinical_records.first()
    odontogram = paciente.odontograms.order_by(Odontogram.fecha.desc()).first()
    treatment_plans = paciente.treatment_plans.order_by(TreatmentPlan.fecha_creacion.desc()).all()
    invoices = paciente.invoices.order_by(Invoice.fecha_emision.desc()).limit(10).all()
    
    return render_template('panel/pacientes/detail.html',
                         paciente=paciente,
                         citas=citas,
                         clinical_record=clinical_record,
                         odontogram=odontogram,
                         treatment_plans=treatment_plans,
                         invoices=invoices)


@bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def paciente_new():
    """Crear nuevo paciente."""
    if request.method == 'POST':
        paciente = Patient(
            nombre=request.form.get('nombre'),
            apellidos=request.form.get('apellidos'),
            email=request.form.get('email'),
            telefono=request.form.get('telefono'),
            dni=request.form.get('dni') or None,
            direccion=request.form.get('direccion'),
            fecha_nacimiento=datetime.strptime(request.form.get('fecha_nacimiento'), '%Y-%m-%d').date() if request.form.get('fecha_nacimiento') else None,
            notas_generales=request.form.get('notas_generales')
        )
        
        try:
            db.session.add(paciente)
            db.session.commit()
            flash('Paciente creado correctamente.', 'success')
            return redirect(url_for('panel.paciente_detail', patient_id=paciente.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el paciente.', 'error')
    
    return render_template('panel/pacientes/new.html')


# ==================== GESTIÓN DE CITAS ====================

@bp.route('/citas')
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def citas_list():
    """Listado de citas con filtros."""
    fecha = request.args.get('fecha')
    estado = request.args.get('estado')
    dentist_id = request.args.get('dentist_id', type=int)
    
    query = Appointment.query
    
    # Si es dentista, solo sus citas
    if current_user.is_dentist():
        query = query.filter_by(dentist_id=current_user.id)
    elif dentist_id:
        query = query.filter_by(dentist_id=dentist_id)
    
    if fecha:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        inicio_dia = datetime.combine(fecha_obj, datetime.min.time())
        fin_dia = datetime.combine(fecha_obj, datetime.max.time())
        query = query.filter(
            Appointment.fecha_hora_inicio >= inicio_dia,
            Appointment.fecha_hora_inicio <= fin_dia
        )
    else:
        # Por defecto, mostrar citas de hoy en adelante
        query = query.filter(Appointment.fecha_hora_inicio >= datetime.now())
    
    if estado:
        query = query.filter_by(estado=estado)
    
    citas = query.order_by(Appointment.fecha_hora_inicio).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    
    return render_template('panel/citas/list.html', citas=citas, dentistas=dentistas,
                         fecha=fecha, estado=estado, dentist_id=dentist_id)


@bp.route('/citas/nueva', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def cita_new():
    """Crear nueva cita."""
    if request.method == 'POST':
        paciente_id = request.form.get('patient_id', type=int)
        dentist_id = request.form.get('dentist_id', type=int)
        fecha_hora_inicio = datetime.strptime(
            f"{request.form.get('fecha')} {request.form.get('hora_inicio')}",
            '%Y-%m-%d %H:%M'
        )
        fecha_hora_fin = datetime.strptime(
            f"{request.form.get('fecha')} {request.form.get('hora_fin')}",
            '%Y-%m-%d %H:%M'
        )
        
        # Verificar que el doctor trabaja ese día
        dia_semana = fecha_hora_inicio.weekday()
        horario_dia = DoctorSchedule.query.filter_by(
            doctor_id=dentist_id,
            dia_semana=dia_semana,
            activo=True
        ).first()
        
        if not horario_dia:
            flash('El doctor no trabaja ese día. Por favor, selecciona otro día.', 'error')
        else:
            # Verificar que la cita está dentro del horario de trabajo
            hora_inicio_cita = fecha_hora_inicio.time()
            hora_fin_cita = fecha_hora_fin.time()
            
            if hora_inicio_cita < horario_dia.hora_inicio or hora_fin_cita > horario_dia.hora_fin:
                flash(f'La cita debe estar entre {horario_dia.hora_inicio.strftime("%H:%M")} y {horario_dia.hora_fin.strftime("%H:%M")}', 'error')
            else:
                room_id = request.form.get('room_id', type=int)
                cita = Appointment(
                    patient_id=paciente_id,
                    dentist_id=dentist_id,
                    fecha_hora_inicio=fecha_hora_inicio,
                    fecha_hora_fin=fecha_hora_fin,
                    room_id=room_id if room_id else None,
                    sillon=request.form.get('sillon') or (Room.query.get(room_id).nombre if room_id else None),
                    motivo=request.form.get('motivo'),
                    estado=request.form.get('estado', 'programada')
                )
                
                try:
                    db.session.add(cita)
                    db.session.commit()
                    flash('Cita creada correctamente.', 'success')
                    return redirect(url_for('panel.citas_list'))
                except Exception as e:
                    db.session.rollback()
                    flash('Error al crear la cita.', 'error')
    
    pacientes = Patient.query.filter_by(activo=True).order_by(Patient.apellidos).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    salas = Room.query.filter_by(activo=True).order_by(Room.nombre).all()
    
    return render_template('panel/citas/new.html', pacientes=pacientes, dentistas=dentistas, salas=salas)


@bp.route('/api/pacientes/buscar', methods=['GET'])
@login_required
@role_required('admin', 'recepcionista')
def api_pacientes_buscar():
    """API para buscar pacientes por nombre, apellidos, email o DNI."""
    search = request.args.get('q', '')
    pacientes = []
    
    if search:
        query = Patient.query.filter_by(activo=True).filter(
            db.or_(
                Patient.nombre.ilike(f'%{search}%'),
                Patient.apellidos.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%'),
                Patient.dni.ilike(f'%{search}%')
            )
        ).limit(20).all()
        
        pacientes = [{
            'id': p.id,
            'nombre_completo': p.nombre_completo(),
            'email': p.email,
            'telefono': p.telefono or ''
        } for p in query]
    
    return jsonify({'pacientes': pacientes})


@bp.route('/api/pacientes/crear-rapido', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista')
def api_paciente_crear_rapido():
    """API para crear un paciente rápidamente desde el modal."""
    data = request.get_json()
    
    try:
        # Validar campos requeridos
        if not data.get('nombre') or not data.get('apellidos') or not data.get('email'):
            return jsonify({'success': False, 'error': 'Nombre, apellidos y email son obligatorios'}), 400
        
        # Verificar que el email no exista
        if Patient.query.filter_by(email=data.get('email')).first():
            return jsonify({'success': False, 'error': 'Este email ya está registrado'}), 400
        
        paciente = Patient(
            nombre=data.get('nombre'),
            apellidos=data.get('apellidos'),
            email=data.get('email'),
            telefono=data.get('telefono') or None,
            dni=data.get('dni') or None,
            direccion=data.get('direccion') or None
        )
        
        db.session.add(paciente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'paciente': {
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo(),
                'email': paciente.email
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/citas/<int:cita_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def cita_edit(cita_id):
    """Editar cita existente."""
    cita = Appointment.query.get_or_404(cita_id)
    
    # Detectar si viene del dashboard
    from_dashboard = request.args.get('from') == 'dashboard' or request.form.get('from') == 'dashboard'
    
    if request.method == 'POST':
        cita.patient_id = request.form.get('patient_id', type=int)
        cita.dentist_id = request.form.get('dentist_id', type=int)
        cita.fecha_hora_inicio = datetime.strptime(
            f"{request.form.get('fecha')} {request.form.get('hora_inicio')}",
            '%Y-%m-%d %H:%M'
        )
        cita.fecha_hora_fin = datetime.strptime(
            f"{request.form.get('fecha')} {request.form.get('hora_fin')}",
            '%Y-%m-%d %H:%M'
        )
        # Verificar que el doctor trabaja ese día
        dia_semana = cita.fecha_hora_inicio.weekday()
        horario_dia = DoctorSchedule.query.filter_by(
            doctor_id=cita.dentist_id,
            dia_semana=dia_semana,
            activo=True
        ).first()
        
        if not horario_dia:
            flash('El doctor no trabaja ese día. Por favor, selecciona otro día.', 'error')
        else:
            # Verificar que la cita está dentro del horario de trabajo
            hora_inicio_cita = cita.fecha_hora_inicio.time()
            hora_fin_cita = cita.fecha_hora_fin.time()
            
            if hora_inicio_cita < horario_dia.hora_inicio or hora_fin_cita > horario_dia.hora_fin:
                flash(f'La cita debe estar entre {horario_dia.hora_inicio.strftime("%H:%M")} y {horario_dia.hora_fin.strftime("%H:%M")}', 'error')
            else:
                room_id = request.form.get('room_id', type=int)
                cita.room_id = room_id if room_id else None
                cita.sillon = request.form.get('sillon') or (Room.query.get(room_id).nombre if room_id else None)
                cita.motivo = request.form.get('motivo')
                cita.estado = request.form.get('estado')
                cita.notas = request.form.get('notas')
                
                try:
                    db.session.commit()
                    flash('Cita actualizada correctamente.', 'success')
                    # Redirigir al dashboard si viene de ahí, sino a la lista de citas
                    if from_dashboard:
                        return redirect(url_for('panel.dashboard'))
                    return redirect(url_for('panel.citas_list'))
                except Exception as e:
                    db.session.rollback()
                    flash('Error al actualizar la cita.', 'error')
    
    pacientes = Patient.query.filter_by(activo=True).order_by(Patient.apellidos).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    salas = Room.query.filter_by(activo=True).order_by(Room.nombre).all()
    
    return render_template('panel/citas/edit.html', cita=cita, pacientes=pacientes, dentistas=dentistas, salas=salas, from_dashboard=from_dashboard)


@bp.route('/citas/<int:cita_id>/cambiar-estado', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def cita_change_status(cita_id):
    """Cambiar estado de una cita."""
    cita = Appointment.query.get_or_404(cita_id)
    
    # Si es dentista, solo puede cambiar sus propias citas
    if current_user.is_dentist() and cita.dentist_id != current_user.id:
        flash('No tienes permisos para modificar esta cita.', 'error')
        return redirect(url_for('panel.citas_list'))
    
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in ['programada', 'confirmada', 'cancelada', 'realizada']:
        cita.estado = nuevo_estado
        try:
            db.session.commit()
            flash('Estado de la cita actualizado.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el estado.', 'error')
    
    return redirect(url_for('panel.citas_list'))


# ==================== HISTORIA CLÍNICA Y ODONTOGRAMA ====================

@bp.route('/pacientes/<int:patient_id>/historia-clinica', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def clinical_record_edit(patient_id):
    """Editar historia clínica del paciente."""
    paciente = Patient.query.get_or_404(patient_id)
    clinical_record = paciente.clinical_records.first()
    
    if not clinical_record:
        clinical_record = ClinicalRecord(patient_id=patient_id)
        db.session.add(clinical_record)
        db.session.commit()
    
    if request.method == 'POST':
        clinical_record.antecedentes_medicos = request.form.get('antecedentes_medicos')
        clinical_record.alergias = request.form.get('alergias')
        clinical_record.medicacion = request.form.get('medicacion')
        clinical_record.observaciones_generales = request.form.get('observaciones_generales')
        
        try:
            db.session.commit()
            flash('Historia clínica actualizada.', 'success')
            return redirect(url_for('panel.paciente_detail', patient_id=patient_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la historia clínica.', 'error')
    
    return render_template('panel/pacientes/clinical_record.html', paciente=paciente, clinical_record=clinical_record)


@bp.route('/pacientes/<int:patient_id>/odontograma', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def odontogram_edit(patient_id):
    """Editar odontograma del paciente."""
    paciente = Patient.query.get_or_404(patient_id)
    odontogram = paciente.odontograms.order_by(Odontogram.fecha.desc()).first()
    
    if request.method == 'POST':
        datos = request.get_json()
        
        if not odontogram:
            odontogram = Odontogram(patient_id=patient_id)
            db.session.add(odontogram)
        
        odontogram.set_datos(datos.get('piezas', {}))
        odontogram.notas = datos.get('notas', '')
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Obtener datos del odontograma
    datos_piezas = odontogram.get_datos() if odontogram else {}
    
    return render_template('panel/pacientes/odontogram.html', paciente=paciente, odontogram=odontogram, datos_piezas=datos_piezas)


# ==================== PLANES DE TRATAMIENTO ====================

@bp.route('/tratamientos', methods=['GET'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def treatments_list():
    """Listado general de tratamientos con filtros."""
    # Obtener parámetros de filtro
    estado = request.args.get('estado', '')
    patient_id = request.args.get('patient_id', type=int)
    dentist_id = request.args.get('dentist_id', type=int)
    
    # Construir query base
    query = TreatmentPlan.query
    
    # Si es dentista, solo sus tratamientos
    if current_user.is_dentist():
        query = query.filter_by(dentist_id=current_user.id)
    
    # Aplicar filtros
    if estado:
        query = query.filter_by(estado=estado)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if dentist_id:
        query = query.filter_by(dentist_id=dentist_id)
    
    # Ordenar por fecha de creación descendente
    tratamientos = query.order_by(TreatmentPlan.fecha_creacion.desc()).all()
    
    # Obtener listas para filtros
    pacientes = Patient.query.filter_by(activo=True).order_by(Patient.apellidos).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    
    # Estadísticas rápidas
    stats = {
        'total': TreatmentPlan.query.count() if not current_user.is_dentist() else TreatmentPlan.query.filter_by(dentist_id=current_user.id).count(),
        'propuestos': TreatmentPlan.query.filter_by(estado='propuesto').count() if not current_user.is_dentist() else TreatmentPlan.query.filter_by(estado='propuesto', dentist_id=current_user.id).count(),
        'en_curso': TreatmentPlan.query.filter_by(estado='en_curso').count() if not current_user.is_dentist() else TreatmentPlan.query.filter_by(estado='en_curso', dentist_id=current_user.id).count(),
        'finalizados': TreatmentPlan.query.filter_by(estado='finalizado').count() if not current_user.is_dentist() else TreatmentPlan.query.filter_by(estado='finalizado', dentist_id=current_user.id).count(),
    }
    
    return render_template('panel/tratamientos/all.html', 
                         tratamientos=tratamientos,
                         pacientes=pacientes,
                         dentistas=dentistas,
                         estado=estado,
                         patient_id=patient_id,
                         dentist_id=dentist_id,
                         stats=stats)


@bp.route('/pacientes/<int:patient_id>/tratamientos', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def treatment_plans_list(patient_id):
    """Listar planes de tratamiento de un paciente."""
    paciente = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Crear nuevo plan
        plan = TreatmentPlan(
            patient_id=patient_id,
            dentist_id=request.form.get('dentist_id', type=int),
            descripcion_general=request.form.get('descripcion_general'),
            coste_estimado=float(request.form.get('coste_estimado', 0))
        )
        
        try:
            db.session.add(plan)
            db.session.commit()
            flash('Plan de tratamiento creado.', 'success')
            return redirect(url_for('panel.treatment_plan_detail', plan_id=plan.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el plan.', 'error')
    
    planes = paciente.treatment_plans.order_by(TreatmentPlan.fecha_creacion.desc()).all()
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    
    return render_template('panel/tratamientos/list.html', paciente=paciente, planes=planes, dentistas=dentistas)


@bp.route('/tratamientos/<int:plan_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def treatment_plan_detail(plan_id):
    """Detalle de un plan de tratamiento."""
    plan = TreatmentPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        if nuevo_estado in ['propuesto', 'en_curso', 'finalizado', 'cancelado']:
            plan.estado = nuevo_estado
            try:
                db.session.commit()
                flash('Estado del plan actualizado.', 'success')
                # Si se marca como finalizado, redirigir a facturar
                if nuevo_estado == 'finalizado':
                    return redirect(url_for('panel.treatment_invoice', plan_id=plan_id))
            except Exception as e:
                db.session.rollback()
                flash('Error al actualizar el estado.', 'error')
        return redirect(url_for('panel.treatment_plan_detail', plan_id=plan_id))
    
    items = plan.treatment_items.order_by(TreatmentItem.fecha_prevista).all()
    
    return render_template('panel/tratamientos/detail.html', plan=plan, items=items)


@bp.route('/tratamientos/<int:plan_id>/item/nuevo', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def treatment_item_new(plan_id):
    """Añadir item a un plan de tratamiento."""
    plan = TreatmentPlan.query.get_or_404(plan_id)
    
    item = TreatmentItem(
        treatment_plan_id=plan_id,
        nombre_tratamiento=request.form.get('nombre_tratamiento'),
        pieza_dental=request.form.get('pieza_dental'),
        fecha_prevista=datetime.strptime(request.form.get('fecha_prevista'), '%Y-%m-%d').date() if request.form.get('fecha_prevista') else None,
        precio=float(request.form.get('precio', 0))
    )
    
    try:
        db.session.add(item)
        db.session.commit()
        flash('Acto añadido al plan.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al añadir el acto.', 'error')
    
    return redirect(url_for('panel.treatment_plan_detail', plan_id=plan_id))


@bp.route('/tratamientos/item/<int:item_id>/marcar-realizado', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista', 'dentista')
def treatment_item_mark_done(item_id):
    """Marcar un acto como realizado."""
    item = TreatmentItem.query.get_or_404(item_id)
    
    item.estado = 'realizado'
    item.fecha_realizacion = date.today()
    
    try:
        db.session.commit()
        flash('Acto marcado como realizado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el acto.', 'error')
    
    return redirect(url_for('panel.treatment_plan_detail', plan_id=item.treatment_plan_id))


# ==================== FACTURACIÓN ====================

@bp.route('/facturas')
@login_required
@role_required('admin', 'recepcionista')
def invoices_list():
    """Listado de facturas."""
    estado = request.args.get('estado')
    patient_id = request.args.get('patient_id', type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Invoice.query
    
    if estado:
        query = query.filter_by(estado_pago=estado)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if fecha_desde:
        fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
        query = query.filter(Invoice.fecha_emision >= fecha_desde_obj)
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
        query = query.filter(Invoice.fecha_emision <= fecha_hasta_obj)
    
    facturas = query.order_by(Invoice.fecha_emision.desc()).all()
    pacientes = Patient.query.filter_by(activo=True).order_by(Patient.apellidos).all()
    
    return render_template('panel/facturas/list.html', facturas=facturas, pacientes=pacientes,
                         estado=estado, patient_id=patient_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@bp.route('/tratamientos/<int:plan_id>/facturar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def treatment_invoice(plan_id):
    """Facturar un tratamiento finalizado."""
    plan = TreatmentPlan.query.get_or_404(plan_id)
    
    if plan.estado != 'finalizado':
        flash('Solo se pueden facturar tratamientos finalizados.', 'warning')
        return redirect(url_for('panel.treatment_plan_detail', plan_id=plan_id))
    
    if request.method == 'POST':
        total = float(request.form.get('total', 0))
        metodo_pago = request.form.get('metodo_pago', 'pendiente')
        
        # Calcular total si no se especificó (suma de items realizados)
        if total == 0:
            items_realizados = plan.treatment_items.filter_by(estado='realizado').all()
            total = sum(float(item.precio) for item in items_realizados if item.precio)
            if total == 0:
                total = float(plan.coste_estimado) if plan.coste_estimado else 0
        
        factura = Invoice(
            patient_id=plan.patient_id,
            fecha_emision=date.today(),
            total=total,
            estado_pago='pendiente' if metodo_pago == 'pendiente' else 'parcial',
            metodo_pago=metodo_pago if metodo_pago != 'pendiente' else None
        )
        
        try:
            db.session.add(factura)
            db.session.commit()
            flash('Factura creada correctamente.', 'success')
            return redirect(url_for('panel.invoice_detail', invoice_id=factura.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la factura.', 'error')
    
    # Calcular total sugerido
    items_realizados = plan.treatment_items.filter_by(estado='realizado').all()
    total_sugerido = sum(float(item.precio) for item in items_realizados if item.precio)
    if total_sugerido == 0:
        total_sugerido = float(plan.coste_estimado) if plan.coste_estimado else 0
    
    return render_template('panel/facturas/treatment_invoice.html', 
                         plan=plan, 
                         paciente=plan.patient,
                         total_sugerido=total_sugerido,
                         items_realizados=items_realizados)


@bp.route('/pacientes/<int:patient_id>/factura/nueva', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def invoice_new(patient_id):
    """Crear nueva factura."""
    paciente = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        factura = Invoice(
            patient_id=patient_id,
            total=float(request.form.get('total')),
            metodo_pago=request.form.get('metodo_pago')
        )
        
        try:
            db.session.add(factura)
            db.session.commit()
            flash('Factura creada.', 'success')
            return redirect(url_for('panel.invoice_detail', invoice_id=factura.id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la factura.', 'error')
    
    return render_template('panel/facturas/new.html', paciente=paciente)


@bp.route('/facturas/<int:invoice_id>')
@login_required
@role_required('admin', 'recepcionista')
def invoice_detail(invoice_id):
    """Detalle de factura con pagos."""
    factura = Invoice.query.get_or_404(invoice_id)
    pagos = factura.payments.order_by(Payment.fecha_pago.desc()).all()
    
    return render_template('panel/facturas/detail.html', factura=factura, pagos=pagos)


@bp.route('/facturas/<int:invoice_id>/pago/nuevo', methods=['POST'])
@login_required
@role_required('admin', 'recepcionista')
def payment_new(invoice_id):
    """Registrar un pago."""
    factura = Invoice.query.get_or_404(invoice_id)
    
    pago = Payment(
        invoice_id=invoice_id,
        cantidad=float(request.form.get('cantidad')),
        metodo_pago=request.form.get('metodo_pago'),
        referencia=request.form.get('referencia')
    )
    
    try:
        db.session.add(pago)
        factura.actualizar_estado_pago()
        flash('Pago registrado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al registrar el pago.', 'error')
    
    return redirect(url_for('panel.invoice_detail', invoice_id=invoice_id))


# ==================== NOTIFICACIONES ====================

@bp.route('/pacientes/<int:patient_id>/notificacion/nueva', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def notification_new(patient_id):
    """Enviar notificación a un paciente."""
    paciente = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        notificacion = Notification(
            patient_id=patient_id,
            tipo=request.form.get('tipo'),
            asunto=request.form.get('asunto'),
            contenido_resumen=request.form.get('contenido'),
            estado_envio='exitoso'  # Simulado
        )
        
        try:
            db.session.add(notificacion)
            db.session.commit()
            flash('Notificación registrada (simulada).', 'success')
            return redirect(url_for('panel.paciente_detail', patient_id=patient_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar la notificación.', 'error')
    
    return render_template('panel/notificaciones/new.html', paciente=paciente)


# ==================== GESTIÓN DE SALAS ====================

@bp.route('/salas')
@login_required
@role_required('admin', 'recepcionista')
def rooms_list():
    """Listado de salas/sillones."""
    salas = Room.query.order_by(Room.nombre).all()
    return render_template('panel/salas/list.html', salas=salas)


@bp.route('/salas/nueva', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def room_new():
    """Crear nueva sala."""
    if request.method == 'POST':
        sala = Room(
            nombre=request.form.get('nombre'),
            descripcion=request.form.get('descripcion'),
            activo=request.form.get('activo') == 'on'
        )
        try:
            db.session.add(sala)
            db.session.commit()
            flash('Sala creada correctamente.', 'success')
            return redirect(url_for('panel.rooms_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la sala. El nombre puede estar duplicado.', 'error')
    
    return render_template('panel/salas/new.html')


@bp.route('/salas/<int:room_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def room_edit(room_id):
    """Editar sala."""
    sala = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        sala.nombre = request.form.get('nombre')
        sala.descripcion = request.form.get('descripcion')
        sala.activo = request.form.get('activo') == 'on'
        
        try:
            db.session.commit()
            flash('Sala actualizada correctamente.', 'success')
            return redirect(url_for('panel.rooms_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la sala.', 'error')
    
    return render_template('panel/salas/edit.html', sala=sala)


@bp.route('/salas/<int:room_id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def room_delete(room_id):
    """Eliminar sala."""
    sala = Room.query.get_or_404(room_id)
    
    # Verificar que no tenga citas asociadas
    if sala.appointments.count() > 0:
        flash('No se puede eliminar la sala porque tiene citas asociadas.', 'error')
        return redirect(url_for('panel.rooms_list'))
    
    try:
        db.session.delete(sala)
        db.session.commit()
        flash('Sala eliminada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la sala.', 'error')
    
    return redirect(url_for('panel.rooms_list'))


# ==================== GESTIÓN DE DOCTORES ====================

@bp.route('/usuarios')
@login_required
@role_required('admin')
def users_list():
    """Listado de usuarios."""
    rol_filtro = request.args.get('rol', '')
    
    query = User.query.filter(User.rol != 'paciente')
    
    if rol_filtro:
        query = query.filter_by(rol=rol_filtro)
    
    usuarios = query.order_by(User.nombre).all()
    
    return render_template('panel/usuarios/list.html', usuarios=usuarios, rol_filtro=rol_filtro)


@bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def user_new():
    """Crear nuevo usuario."""
    if request.method == 'POST':
        usuario = User(
            nombre=request.form.get('nombre'),
            email=request.form.get('email'),
            rol=request.form.get('rol'),
            activo=request.form.get('activo') == 'on'
        )
        usuario.set_password(request.form.get('password'))
        
        try:
            db.session.add(usuario)
            db.session.commit()
            flash('Usuario creado correctamente.', 'success')
            return redirect(url_for('panel.users_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el usuario. El email puede estar duplicado.', 'error')
    
    return render_template('panel/usuarios/new.html')


@bp.route('/usuarios/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def user_edit(user_id):
    """Editar usuario."""
    usuario = User.query.get_or_404(user_id)
    
    # No permitir editar pacientes desde aquí
    if usuario.rol == 'paciente':
        flash('Los pacientes se gestionan desde el apartado de pacientes.', 'error')
        return redirect(url_for('panel.users_list'))
    
    if request.method == 'POST':
        usuario.nombre = request.form.get('nombre')
        usuario.email = request.form.get('email')
        usuario.rol = request.form.get('rol')
        usuario.activo = request.form.get('activo') == 'on'
        
        # Cambiar contraseña si se proporciona
        nueva_password = request.form.get('password')
        if nueva_password:
            usuario.set_password(nueva_password)
        
        try:
            db.session.commit()
            flash('Usuario actualizado correctamente.', 'success')
            return redirect(url_for('panel.users_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el usuario.', 'error')
    
    return render_template('panel/usuarios/edit.html', usuario=usuario)


@bp.route('/usuarios/<int:user_id>/horario', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def user_schedule(user_id):
    """Gestionar horario de trabajo del usuario (solo para dentistas)."""
    usuario = User.query.get_or_404(user_id)
    
    if usuario.rol != 'dentista':
        flash('Solo los dentistas pueden tener horario de trabajo.', 'error')
        return redirect(url_for('panel.users_list'))
    
    if request.method == 'POST':
        # Eliminar horarios existentes
        DoctorSchedule.query.filter_by(doctor_id=user_id).delete()
        
        # Obtener días seleccionados
        dias_seleccionados = request.form.getlist('dias')
        
        # Crear nuevos horarios
        for dia_str in dias_seleccionados:
            dia = int(dia_str)
            hora_inicio_str = request.form.get(f'hora_inicio_{dia}', '09:00')
            hora_fin_str = request.form.get(f'hora_fin_{dia}', '20:00')
            
            try:
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
                hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
                
                schedule = DoctorSchedule(
                    doctor_id=user_id,
                    dia_semana=dia,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    activo=True
                )
                db.session.add(schedule)
            except Exception as e:
                flash(f'Error al procesar el día {dia}: {str(e)}', 'error')
        
        try:
            db.session.commit()
            flash('Horario actualizado correctamente.', 'success')
            return redirect(url_for('panel.user_schedule', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el horario.', 'error')
    
    # Obtener horarios actuales
    horarios = DoctorSchedule.query.filter_by(doctor_id=user_id, activo=True).all()
    horarios_dict = {h.dia_semana: h for h in horarios}
    
    dias_semana = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo')
    ]
    
    return render_template('panel/usuarios/schedule.html', 
                         usuario=usuario, 
                         horarios_dict=horarios_dict,
                         dias_semana=dias_semana)


# ==================== REDIRECCIONES (COMPATIBILIDAD) ====================

@bp.route('/doctores')
@login_required
@role_required('admin')
def doctors_list_redirect():
    """Redirección desde la ruta antigua de doctores."""
    return redirect(url_for('panel.users_list', rol='dentista'))


@bp.route('/doctores/nuevo')
@login_required
@role_required('admin')
def doctor_new_redirect():
    """Redirección desde la ruta antigua de nuevo doctor."""
    return redirect(url_for('panel.user_new'))


@bp.route('/doctores/<int:doctor_id>/editar')
@login_required
@role_required('admin')
def doctor_edit_redirect(doctor_id):
    """Redirección desde la ruta antigua de editar doctor."""
    return redirect(url_for('panel.user_edit', user_id=doctor_id))


@bp.route('/doctores/<int:doctor_id>/horario')
@login_required
@role_required('admin')
def doctor_schedule_redirect(doctor_id):
    """Redirección desde la ruta antigua de horario de doctor."""
    return redirect(url_for('panel.user_schedule', user_id=doctor_id))


# ==================== CONFIGURACIÓN DE CLÍNICA ====================

@bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def clinic_settings():
    """Configuración de la clínica."""
    settings = ClinicSettings.get_settings()
    
    if request.method == 'POST':
        settings.nombre_clinica = request.form.get('nombre_clinica')
        settings.nif_cif = request.form.get('nif_cif')
        settings.direccion = request.form.get('direccion')
        settings.codigo_postal = request.form.get('codigo_postal')
        settings.ciudad = request.form.get('ciudad')
        settings.provincia = request.form.get('provincia')
        settings.telefono = request.form.get('telefono')
        settings.email = request.form.get('email')
        settings.web = request.form.get('web')
        logo_url = request.form.get('logo_url')
        if logo_url:
            # Si es una ruta relativa sin /static/, añadirla
            if not logo_url.startswith('http') and not logo_url.startswith('/'):
                settings.logo_url = f'/static/{logo_url}'
            else:
                settings.logo_url = logo_url
        else:
            settings.logo_url = None
        settings.numero_colegio = request.form.get('numero_colegio')
        settings.iban = request.form.get('iban')
        settings.notas_pie_factura = request.form.get('notas_pie_factura')
        
        try:
            db.session.commit()
            flash('Configuración guardada correctamente.', 'success')
            return redirect(url_for('panel.clinic_settings'))
        except Exception as e:
            db.session.rollback()
            flash('Error al guardar la configuración.', 'error')
    
    return render_template('panel/configuracion/settings.html', settings=settings)


# ==================== FICHAJE DE EMPLEADOS ====================

@bp.route('/fichaje')
@login_required
@role_required('admin', 'recepcionista')
def fichaje_dashboard():
    """Panel de control de fichaje de empleados - Vista semanal."""
    # Filtros
    fecha_str = request.args.get('fecha', None)
    user_id = request.args.get('user_id', type=int)
    
    # Por defecto, semana actual
    if fecha_str:
        fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha_base = date.today()
    
    # Calcular inicio y fin de semana (lunes a domingo)
    start_of_week = fecha_base - timedelta(days=fecha_base.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Obtener empleados (todos los usuarios activos excepto pacientes)
    empleados = User.query.filter(
        User.activo == True,
        User.rol.in_(['admin', 'recepcionista', 'dentista', 'auxiliar', 'comercial'])
    )
    
    if user_id:
        empleados = empleados.filter(User.id == user_id)
    
    empleados = empleados.order_by(User.nombre).all()
    
    return render_template('panel/fichaje/dashboard.html',
                         empleados=empleados,
                         start_of_week=start_of_week,
                         end_of_week=end_of_week,
                         user_id=user_id)


@bp.route('/fichaje/semana')
@login_required
@role_required('admin', 'recepcionista')
def fichaje_semana():
    """API para obtener fichajes de la semana en formato JSON."""
    fecha_str = request.args.get('fecha', None)
    user_id = request.args.get('user_id', type=int)
    
    if fecha_str:
        fecha_base = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    else:
        fecha_base = date.today()
    
    # Calcular inicio y fin de semana (lunes a domingo)
    start_of_week = fecha_base - timedelta(days=fecha_base.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Obtener fichajes de la semana
    query = TimeClock.query.filter(
        TimeClock.fecha >= start_of_week,
        TimeClock.fecha <= end_of_week
    )
    
    if user_id:
        query = query.filter(TimeClock.user_id == user_id)
    
    fichajes = query.order_by(TimeClock.fecha, TimeClock.user_id).all()
    
    # Formatear fichajes para el calendario
    fichajes_json = []
    for fichaje in fichajes:
        fichajes_json.append({
            'id': fichaje.id,
            'user_id': fichaje.user_id,
            'user_name': fichaje.user.nombre,
            'fecha': fichaje.fecha.strftime('%Y-%m-%d'),
            'hora_entrada': fichaje.hora_entrada.strftime('%H:%M') if fichaje.hora_entrada else None,
            'hora_salida': fichaje.hora_salida.strftime('%H:%M') if fichaje.hora_salida else None,
            'horas_trabajadas': float(fichaje.horas_trabajadas),
            'horas_extras': float(fichaje.horas_extras),
            'notas': fichaje.notas or ''
        })
    
    return jsonify({
        'start_of_week': start_of_week.strftime('%Y-%m-%d'),
        'end_of_week': end_of_week.strftime('%Y-%m-%d'),
        'fichajes': fichajes_json
    })


@bp.route('/fichaje/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def fichaje_new():
    """Registrar nuevo fichaje."""
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        fecha_str = request.form.get('fecha')
        hora_entrada_str = request.form.get('hora_entrada')
        hora_salida_str = request.form.get('hora_salida')
        notas = request.form.get('notas', '')
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M').time() if hora_entrada_str else None
        hora_salida = datetime.strptime(hora_salida_str, '%H:%M').time() if hora_salida_str else None
        
        # Verificar si ya existe un fichaje para ese día
        fichaje_existente = TimeClock.query.filter_by(
            user_id=user_id,
            fecha=fecha
        ).first()
        
        if fichaje_existente:
            # Actualizar fichaje existente
            fichaje_existente.hora_entrada = hora_entrada
            fichaje_existente.hora_salida = hora_salida
            fichaje_existente.notas = notas
            fichaje_existente.calcular_horas()
            fichaje = fichaje_existente
        else:
            # Crear nuevo fichaje
            fichaje = TimeClock(
                user_id=user_id,
                fecha=fecha,
                hora_entrada=hora_entrada,
                hora_salida=hora_salida,
                notas=notas
            )
            fichaje.calcular_horas()
            db.session.add(fichaje)
        
        try:
            db.session.commit()
            flash('Fichaje registrado correctamente.', 'success')
            return redirect(url_for('panel.fichaje_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el fichaje.', 'error')
    
    empleados = User.query.filter(
        User.activo == True,
        User.rol.in_(['admin', 'recepcionista', 'dentista', 'auxiliar', 'comercial'])
    ).order_by(User.nombre).all()
    
    fecha_hoy = date.today()
    
    return render_template('panel/fichaje/new.html', empleados=empleados, fecha_hoy=fecha_hoy)


@bp.route('/fichaje/<int:fichaje_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def fichaje_edit(fichaje_id):
    """Editar fichaje existente."""
    fichaje = TimeClock.query.get_or_404(fichaje_id)
    
    if request.method == 'POST':
        fecha_str = request.form.get('fecha')
        hora_entrada_str = request.form.get('hora_entrada')
        hora_salida_str = request.form.get('hora_salida')
        notas = request.form.get('notas', '')
        
        fichaje.fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        fichaje.hora_entrada = datetime.strptime(hora_entrada_str, '%H:%M').time() if hora_entrada_str else None
        fichaje.hora_salida = datetime.strptime(hora_salida_str, '%H:%M').time() if hora_salida_str else None
        fichaje.notas = notas
        fichaje.calcular_horas()
        
        try:
            db.session.commit()
            flash('Fichaje actualizado correctamente.', 'success')
            return redirect(url_for('panel.fichaje_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el fichaje.', 'error')
    
    return render_template('panel/fichaje/edit.html', fichaje=fichaje)


@bp.route('/fichaje/<int:fichaje_id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def fichaje_delete(fichaje_id):
    """Eliminar fichaje."""
    fichaje = TimeClock.query.get_or_404(fichaje_id)
    
    try:
        db.session.delete(fichaje)
        db.session.commit()
        flash('Fichaje eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el fichaje.', 'error')
    
    return redirect(url_for('panel.fichaje_dashboard'))


# ==================== DÍAS LIBRES ====================

@bp.route('/dias-libres')
@login_required
@role_required('admin', 'recepcionista')
def dias_libres_list():
    """Listado de días libres."""
    estado = request.args.get('estado', 'todos')  # todos, aprobados, pendientes
    
    query = DayOff.query
    
    if estado == 'aprobados':
        query = query.filter_by(aprobado=True)
    elif estado == 'pendientes':
        query = query.filter_by(aprobado=False)
    
    dias_libres = query.order_by(DayOff.fecha_inicio.desc()).all()
    empleados = User.query.filter(
        User.activo == True,
        User.rol.in_(['admin', 'recepcionista', 'dentista', 'auxiliar', 'comercial'])
    ).order_by(User.nombre).all()
    
    return render_template('panel/fichaje/dias_libres.html',
                         dias_libres=dias_libres,
                         empleados=empleados,
                         estado=estado)


@bp.route('/dias-libres/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'recepcionista')
def dias_libres_new():
    """Solicitar día libre."""
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str = request.form.get('fecha_fin')
        tipo = request.form.get('tipo')
        motivo = request.form.get('motivo', '')
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        
        # Si es admin, aprobar automáticamente
        aprobado = current_user.is_admin()
        aprobado_por = current_user.id if aprobado else None
        fecha_aprobacion = datetime.utcnow() if aprobado else None
        
        dia_libre = DayOff(
            user_id=user_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            motivo=motivo,
            aprobado=aprobado,
            aprobado_por=aprobado_por,
            fecha_aprobacion=fecha_aprobacion
        )
        
        try:
            db.session.add(dia_libre)
            db.session.commit()
            flash('Día libre registrado correctamente.', 'success')
            return redirect(url_for('panel.dias_libres_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar el día libre.', 'error')
    
    empleados = User.query.filter(
        User.activo == True,
        User.rol.in_(['admin', 'recepcionista', 'dentista', 'auxiliar', 'comercial'])
    ).order_by(User.nombre).all()
    
    return render_template('panel/fichaje/dia_libre_new.html', empleados=empleados)


@bp.route('/dias-libres/<int:dia_libre_id>/aprobar', methods=['POST'])
@login_required
@role_required('admin')
def dias_libres_aprobar(dia_libre_id):
    """Aprobar día libre."""
    dia_libre = DayOff.query.get_or_404(dia_libre_id)
    
    dia_libre.aprobado = True
    dia_libre.aprobado_por = current_user.id
    dia_libre.fecha_aprobacion = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Día libre aprobado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al aprobar el día libre.', 'error')
    
    return redirect(url_for('panel.dias_libres_list'))


@bp.route('/dias-libres/<int:dia_libre_id>/rechazar', methods=['POST'])
@login_required
@role_required('admin')
def dias_libres_rechazar(dia_libre_id):
    """Rechazar día libre."""
    dia_libre = DayOff.query.get_or_404(dia_libre_id)
    
    try:
        db.session.delete(dia_libre)
        db.session.commit()
        flash('Día libre rechazado y eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al rechazar el día libre.', 'error')
    
    return redirect(url_for('panel.dias_libres_list'))


# ==================== GESTORÍA ====================

@bp.route('/gestoria')
@login_required
@role_required('admin')
def gestoria_dashboard():
    """Panel de gestoría con resumen financiero."""
    # Filtros
    fecha_inicio_str = request.args.get('fecha_inicio', None)
    fecha_fin_str = request.args.get('fecha_fin', None)
    
    # Por defecto, último mes
    if not fecha_inicio_str:
        fecha_inicio = date.today().replace(day=1)  # Primer día del mes
    else:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    
    if not fecha_fin_str:
        fecha_fin = date.today()
    else:
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    
    # Obtener facturas en el rango
    facturas = Invoice.query.filter(
        Invoice.fecha_emision >= fecha_inicio,
        Invoice.fecha_emision <= fecha_fin
    ).all()
    
    # Calcular totales
    # Si el total incluye IVA, calcular base imponible primero
    # Base = Total / 1.21, IVA = Base * 0.21
    total_facturado = sum(float(f.total) for f in facturas)
    total_base_imponible = sum(float(f.total) / 1.21 for f in facturas)  # Base sin IVA
    total_iva = total_facturado - total_base_imponible  # IVA 21%
    
    # Facturas pagadas
    facturas_pagadas = [f for f in facturas if f.estado_pago == 'pagado']
    total_pagado = sum(float(f.total) for f in facturas_pagadas)
    
    # Facturas pendientes
    facturas_pendientes = [f for f in facturas if f.estado_pago == 'pendiente']
    total_pendiente = sum(float(f.total) for f in facturas_pendientes)
    
    # Facturas parciales
    facturas_parciales = [f for f in facturas if f.estado_pago == 'parcial']
    total_parcial = sum(float(f.total) for f in facturas_parciales)
    
    # Calcular pagos recibidos
    pagos = Payment.query.join(Invoice).filter(
        Invoice.fecha_emision >= fecha_inicio,
        Invoice.fecha_emision <= fecha_fin
    ).all()
    
    total_pagos = sum(float(p.cantidad) for p in pagos)
    
    return render_template('panel/gestoria/dashboard.html',
                         facturas=facturas,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         total_facturado=round(total_facturado, 2),
                         total_iva=round(total_iva, 2),
                         total_base_imponible=round(total_base_imponible, 2),
                         total_pagado=round(total_pagado, 2),
                         total_pendiente=round(total_pendiente, 2),
                         total_parcial=round(total_parcial, 2),
                         total_pagos=round(total_pagos, 2),
                         facturas_pagadas=facturas_pagadas,
                         facturas_pendientes=facturas_pendientes,
                         facturas_parciales=facturas_parciales)


@bp.route('/gestoria/facturas')
@login_required
@role_required('admin')
def gestoria_facturas():
    """Listado detallado de facturas para gestoría."""
    fecha_inicio_str = request.args.get('fecha_inicio', None)
    fecha_fin_str = request.args.get('fecha_fin', None)
    estado = request.args.get('estado', 'todas')
    
    # Por defecto, último mes
    if not fecha_inicio_str:
        fecha_inicio = date.today().replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    
    if not fecha_fin_str:
        fecha_fin = date.today()
    else:
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    
    query = Invoice.query.filter(
        Invoice.fecha_emision >= fecha_inicio,
        Invoice.fecha_emision <= fecha_fin
    )
    
    if estado != 'todas':
        query = query.filter_by(estado_pago=estado)
    
    facturas = query.order_by(Invoice.fecha_emision.desc()).all()
    
    # Calcular totales para evitar errores de Decimal en la plantilla
    total_facturado = sum(float(f.total) for f in facturas)
    total_base_imponible = sum(float(f.total) / 1.21 for f in facturas)
    total_iva = total_facturado - total_base_imponible
    
    return render_template('panel/gestoria/facturas.html',
                         facturas=facturas,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         estado=estado,
                         total_facturado=round(total_facturado, 2),
                         total_base_imponible=round(total_base_imponible, 2),
                         total_iva=round(total_iva, 2))


# ==================== HONORARIOS ====================

@bp.route('/honorarios')
@login_required
@role_required('admin')
def honorarios_list():
    """Listado de honorarios por doctor."""
    doctor_id = request.args.get('doctor_id', type=int)
    
    query = Honorario.query
    
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    
    honorarios = query.order_by(Honorario.doctor_id, Honorario.nombre_tratamiento).all()
    
    # Obtener doctores para el filtro
    doctores = User.query.filter_by(rol='dentista', activo=True).order_by(User.nombre).all()
    
    # Para cada honorario, obtener los tratamientos relacionados con información del paciente
    honorarios_con_info = []
    for honorario in honorarios:
        # Buscar TreatmentItems que coincidan con este honorario (mismo doctor y mismo nombre de tratamiento)
        tratamientos_items = db.session.query(
            TreatmentItem,
            TreatmentPlan,
            Patient
        ).join(
            TreatmentPlan, TreatmentItem.treatment_plan_id == TreatmentPlan.id
        ).join(
            Patient, TreatmentPlan.patient_id == Patient.id
        ).filter(
            TreatmentPlan.dentist_id == honorario.doctor_id,
            TreatmentItem.nombre_tratamiento == honorario.nombre_tratamiento,
            TreatmentItem.estado == 'realizado'  # Solo tratamientos realizados
        ).all()
        
        honorarios_con_info.append({
            'honorario': honorario,
            'tratamientos': tratamientos_items
        })
    
    return render_template('panel/honorarios/list.html', 
                         honorarios_con_info=honorarios_con_info,
                         doctores=doctores,
                         doctor_id=doctor_id)


@bp.route('/honorarios/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def honorario_new():
    """Crear nuevo honorario."""
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        nombre_tratamiento = request.form.get('nombre_tratamiento', '').strip()
        precio = float(request.form.get('precio', 0))
        
        # Verificar que el tratamiento existe en la base de datos
        tratamiento_existe = db.session.query(TreatmentItem.nombre_tratamiento).filter_by(
            nombre_tratamiento=nombre_tratamiento
        ).first()
        
        if not tratamiento_existe:
            flash('El tratamiento seleccionado no existe en la base de datos.', 'error')
            return redirect(url_for('panel.honorario_new', doctor_id=doctor_id))
        
        # Verificar si ya existe
        existente = Honorario.query.filter_by(
            doctor_id=doctor_id,
            nombre_tratamiento=nombre_tratamiento
        ).first()
        
        if existente:
            flash('Este honorario ya existe para este doctor. Edítalo desde el listado.', 'error')
            return redirect(url_for('panel.honorarios_list', doctor_id=doctor_id))
        
        honorario = Honorario(
            doctor_id=doctor_id,
            nombre_tratamiento=nombre_tratamiento,
            precio=precio
        )
        
        try:
            db.session.add(honorario)
            db.session.commit()
            flash('Honorario creado correctamente.', 'success')
            return redirect(url_for('panel.honorarios_list', doctor_id=doctor_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el honorario.', 'error')
    
    # Obtener doctores
    doctores = User.query.filter_by(rol='dentista', activo=True).order_by(User.nombre).all()
    
    # Obtener doctor seleccionado (si viene por parámetro)
    doctor_id = request.args.get('doctor_id', type=int)
    tratamientos_por_doctor = {}
    
    # Para cada doctor, obtener los tratamientos únicos que ha realizado
    for doctor in doctores:
        tratamientos = db.session.query(TreatmentItem.nombre_tratamiento).join(
            TreatmentPlan
        ).filter(
            TreatmentPlan.dentist_id == doctor.id
        ).distinct().all()
        tratamientos_por_doctor[doctor.id] = sorted([t[0] for t in tratamientos])
    
    # Tratamientos del doctor seleccionado (si hay uno)
    tratamientos_lista = []
    if doctor_id and doctor_id in tratamientos_por_doctor:
        tratamientos_lista = tratamientos_por_doctor[doctor_id]
    
    return render_template('panel/honorarios/new.html',
                         doctores=doctores,
                         tratamientos_lista=tratamientos_lista,
                         tratamientos_por_doctor=tratamientos_por_doctor,
                         doctor_id=doctor_id)


@bp.route('/honorarios/<int:honorario_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def honorario_edit(honorario_id):
    """Editar honorario."""
    honorario = Honorario.query.get_or_404(honorario_id)
    
    if request.method == 'POST':
        honorario.nombre_tratamiento = request.form.get('nombre_tratamiento', '').strip()
        honorario.precio = float(request.form.get('precio', 0))
        
        # Verificar si ya existe otro con el mismo doctor y tratamiento
        existente = Honorario.query.filter(
            Honorario.doctor_id == honorario.doctor_id,
            Honorario.nombre_tratamiento == honorario.nombre_tratamiento,
            Honorario.id != honorario_id
        ).first()
        
        if existente:
            flash('Este honorario ya existe para este doctor.', 'error')
            return redirect(url_for('panel.honorario_edit', honorario_id=honorario_id))
        
        try:
            db.session.commit()
            flash('Honorario actualizado correctamente.', 'success')
            return redirect(url_for('panel.honorarios_list', doctor_id=honorario.doctor_id))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el honorario.', 'error')
    
    tratamientos_unicos = db.session.query(TreatmentItem.nombre_tratamiento).distinct().all()
    tratamientos_lista = sorted([t[0] for t in tratamientos_unicos])
    
    return render_template('panel/honorarios/edit.html',
                         honorario=honorario,
                         tratamientos_lista=tratamientos_lista)


@bp.route('/honorarios/<int:honorario_id>/eliminar', methods=['POST'])
@login_required
@role_required('admin')
def honorario_delete(honorario_id):
    """Eliminar honorario."""
    honorario = Honorario.query.get_or_404(honorario_id)
    doctor_id = honorario.doctor_id
    
    try:
        db.session.delete(honorario)
        db.session.commit()
        flash('Honorario eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el honorario.', 'error')
    
    return redirect(url_for('panel.honorarios_list', doctor_id=doctor_id))


@bp.route('/honorarios/pdf/<int:doctor_id>')
@login_required
@role_required('admin')
def honorarios_pdf(doctor_id):
    """Generar PDF con la lista de honorarios de un doctor."""
    doctor = User.query.get_or_404(doctor_id)
    
    if doctor.rol != 'dentista':
        flash('El usuario seleccionado no es un dentista.', 'error')
        return redirect(url_for('panel.honorarios_list'))
    
    # Obtener honorarios del doctor
    honorarios = Honorario.query.filter_by(doctor_id=doctor_id).order_by(Honorario.nombre_tratamiento).all()
    
    # Crear el PDF en memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Contenido del PDF
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#495057'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Título
    story.append(Paragraph("HONORARIOS MÉDICOS", title_style))
    story.append(Paragraph(f"Dr./Dra. {doctor.nombre}", subtitle_style))
    story.append(Paragraph(f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    if not honorarios:
        story.append(Paragraph("No hay honorarios configurados para este doctor.", styles['Normal']))
    else:
        # Preparar datos de la tabla
        table_data = [['Tratamiento', 'Precio Honorario (€)']]
        
        total_honorarios = 0
        for honorario in honorarios:
            table_data.append([
                honorario.nombre_tratamiento,
                f"{honorario.precio:.2f}"
            ])
            total_honorarios += float(honorario.precio)
        
        # Añadir fila de total
        table_data.append([
            '<b>TOTAL</b>',
            f'<b>{total_honorarios:.2f} €</b>'
        ])
        
        # Crear tabla
        table = Table(table_data, colWidths=[12*cm, 4*cm])
        
        # Estilo de la tabla
        table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Filas de datos
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
            
            # Fila de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
        
        # Nota al pie
        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6c757d'),
            alignment=TA_CENTER,
            spaceBefore=20
        )
        story.append(Paragraph("Este documento contiene los honorarios configurados para el doctor.", nota_style))
    
    # Construir PDF
    doc.build(story)
    
    # Obtener el PDF del buffer
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=honorarios_{doctor.nombre.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

