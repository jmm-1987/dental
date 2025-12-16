"""
Rutas del área privada del paciente.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Patient, Appointment, TreatmentPlan, TreatmentItem, Invoice, Payment, User, DoctorSchedule
from datetime import datetime, date, timedelta

bp = Blueprint('patient', __name__)


@bp.route('/dashboard')
@login_required
def dashboard():
    """Panel principal del paciente."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    paciente = current_user
    
    # Próximas citas
    proximas_citas = paciente.appointments.filter(
        Appointment.fecha_hora_inicio >= datetime.now(),
        Appointment.estado.in_(['programada', 'confirmada'])
    ).order_by(Appointment.fecha_hora_inicio).limit(5).all()
    
    # Citas pasadas
    citas_pasadas = paciente.appointments.filter(
        Appointment.fecha_hora_inicio < datetime.now()
    ).order_by(Appointment.fecha_hora_inicio.desc()).limit(5).all()
    
    # Planes de tratamiento activos
    planes_activos = paciente.treatment_plans.filter(
        TreatmentPlan.estado.in_(['propuesto', 'en_curso'])
    ).order_by(TreatmentPlan.fecha_creacion.desc()).all()
    
    # Facturas pendientes
    facturas_pendientes = paciente.invoices.filter(
        Invoice.estado_pago.in_(['pendiente', 'parcial'])
    ).order_by(Invoice.fecha_emision.desc()).limit(5).all()
    
    return render_template('patient/dashboard.html',
                         paciente=paciente,
                         proximas_citas=proximas_citas,
                         citas_pasadas=citas_pasadas,
                         planes_activos=planes_activos,
                         facturas_pendientes=facturas_pendientes)


@bp.route('/citas')
@login_required
def citas_list():
    """Listado de todas las citas del paciente."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    paciente = current_user
    tipo = request.args.get('tipo', 'proximas')  # proximas o pasadas
    
    if tipo == 'proximas':
        citas = paciente.appointments.filter(
            Appointment.fecha_hora_inicio >= datetime.now()
        ).order_by(Appointment.fecha_hora_inicio).all()
    else:
        citas = paciente.appointments.filter(
            Appointment.fecha_hora_inicio < datetime.now()
        ).order_by(Appointment.fecha_hora_inicio.desc()).all()
    
    return render_template('patient/citas.html', citas=citas, tipo=tipo)


@bp.route('/citas/solicitar')
@login_required
def cita_solicitar():
    """Solicitar nueva cita con calendario."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    paciente = current_user
    dentistas = User.query.filter_by(rol='dentista', activo=True).all()
    
    return render_template('patient/solicitar_cita.html', paciente=paciente, dentistas=dentistas)


@bp.route('/calendario/disponibilidad', methods=['GET'])
@login_required
def calendario_disponibilidad():
    """Obtener disponibilidad de horarios para pacientes."""
    if not isinstance(current_user, Patient):
        return jsonify({'error': 'Acceso denegado'}), 403
    
    fecha_str = request.args.get('fecha', None)
    dentist_id = request.args.get('dentist_id', type=int)
    
    if not fecha_str or not dentist_id:
        return jsonify({'error': 'Fecha y dentista requeridos'}), 400
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
    
    # Verificar si el doctor trabaja ese día
    horario_dia = DoctorSchedule.query.filter_by(
        doctor_id=dentist_id,
        dia_semana=dia_semana,
        activo=True
    ).first()
    
    if not horario_dia:
        # El doctor no trabaja ese día
        return jsonify({'tramos': [], 'message': 'El doctor no trabaja este día'})
    
    # Usar horario del doctor
    hora_inicio = horario_dia.hora_inicio.hour
    minuto_inicio = horario_dia.hora_inicio.minute
    hora_fin = horario_dia.hora_fin.hour
    minuto_fin = horario_dia.hora_fin.minute
    
    # Generar tramos de 30 minutos según el horario del doctor
    tramos_disponibles = []
    hora_actual = hora_inicio
    minuto_actual = minuto_inicio
    
    while hora_actual < hora_fin or (hora_actual == hora_fin and minuto_actual < minuto_fin):
        tramo_inicio = datetime.combine(fecha, datetime.min.time().replace(hour=hora_actual, minute=minuto_actual))
        tramo_fin = tramo_inicio + timedelta(minutes=30)
        
        # Verificar si el tramo está en el pasado
        if tramo_inicio < datetime.now():
            # Avanzar al siguiente tramo
            minuto_actual += 30
            if minuto_actual >= 60:
                hora_actual += 1
                minuto_actual -= 60
            continue
        
        # Verificar si hay conflicto con citas existentes
        conflicto = Appointment.query.filter(
            Appointment.dentist_id == dentist_id,
            Appointment.estado.in_(['programada', 'confirmada']),
            Appointment.fecha_hora_inicio < tramo_fin,
            Appointment.fecha_hora_fin > tramo_inicio
        ).first()
        
        disponible = conflicto is None
        
        tramos_disponibles.append({
            'start': tramo_inicio.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': tramo_fin.strftime('%Y-%m-%dT%H:%M:%S'),
            'disponible': disponible
        })
        
        # Avanzar al siguiente tramo
        minuto_actual += 30
        if minuto_actual >= 60:
            hora_actual += 1
            minuto_actual -= 60
    
    return jsonify({'tramos': tramos_disponibles})


@bp.route('/calendario/solicitar-cita', methods=['POST'])
@login_required
def calendario_solicitar_cita():
    """Solicitar cita desde el calendario."""
    if not isinstance(current_user, Patient):
        return jsonify({'error': 'Acceso denegado'}), 403
    
    data = request.get_json()
    
    try:
        paciente_id = current_user.id
        dentist_id = data.get('dentist_id')
        fecha_hora_inicio = datetime.strptime(data.get('start'), '%Y-%m-%dT%H:%M:%S')
        fecha_hora_fin = datetime.strptime(data.get('end'), '%Y-%m-%dT%H:%M:%S')
        motivo = data.get('motivo', '')
        
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
        
        # Verificar que no haya conflicto
        conflicto = Appointment.query.filter(
            Appointment.dentist_id == dentist_id,
            Appointment.estado.in_(['programada', 'confirmada']),
            Appointment.fecha_hora_inicio < fecha_hora_fin,
            Appointment.fecha_hora_fin > fecha_hora_inicio
        ).first()
        
        if conflicto:
            return jsonify({'success': False, 'error': 'Ese horario ya no está disponible'}), 400
        
        cita = Appointment(
            patient_id=paciente_id,
            dentist_id=dentist_id,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
            motivo=motivo,
            estado='programada'
        )
        
        db.session.add(cita)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cita solicitada correctamente. Te contactaremos para confirmarla.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/tratamientos')
@login_required
def tratamientos_list():
    """Listado de tratamientos del paciente (versión amigable)."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    paciente = current_user
    planes = paciente.treatment_plans.order_by(TreatmentPlan.fecha_creacion.desc()).all()
    
    # Preparar datos amigables para el paciente
    planes_data = []
    for plan in planes:
        items_pendientes = plan.treatment_items.filter_by(estado='pendiente').count()
        items_realizados = plan.treatment_items.filter_by(estado='realizado').count()
        total_items = plan.treatment_items.count()
        
        planes_data.append({
            'plan': plan,
            'items_pendientes': items_pendientes,
            'items_realizados': items_realizados,
            'total_items': total_items,
            'progreso': (items_realizados / total_items * 100) if total_items > 0 else 0
        })
    
    return render_template('patient/tratamientos.html', planes_data=planes_data)


@bp.route('/tratamientos/<int:plan_id>')
@login_required
def tratamiento_detail(plan_id):
    """Detalle de un tratamiento (versión paciente)."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    plan = TreatmentPlan.query.get_or_404(plan_id)
    
    # Verificar que el plan pertenece al paciente
    if plan.patient_id != current_user.id:
        flash('No tienes acceso a este tratamiento.', 'error')
        return redirect(url_for('patient.tratamientos_list'))
    
    items = plan.treatment_items.order_by(TreatmentItem.fecha_prevista).all()
    
    return render_template('patient/tratamiento_detail.html', plan=plan, items=items)


@bp.route('/facturas')
@login_required
def facturas_list():
    """Listado de facturas del paciente."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    paciente = current_user
    facturas = paciente.invoices.order_by(Invoice.fecha_emision.desc()).all()
    
    return render_template('patient/facturas.html', facturas=facturas)


@bp.route('/facturas/<int:invoice_id>')
@login_required
def factura_detail(invoice_id):
    """Detalle de una factura."""
    if not isinstance(current_user, Patient):
        flash('Acceso denegado.', 'error')
        return redirect(url_for('public.index'))
    
    factura = Invoice.query.get_or_404(invoice_id)
    
    # Verificar que la factura pertenece al paciente
    if factura.patient_id != current_user.id:
        flash('No tienes acceso a esta factura.', 'error')
        return redirect(url_for('patient.facturas_list'))
    
    pagos = factura.payments.order_by(Payment.fecha_pago.desc()).all()
    
    return render_template('patient/factura_detail.html', factura=factura, pagos=pagos)

