"""
Modelos SQLAlchemy para la aplicación de clínica dental.
"""
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, time
import json


class User(UserMixin, db.Model):
    """Usuario interno de la clínica (admin, recepcionista, dentista)."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)  # admin, recepcionista, dentista, auxiliar, comercial
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    appointments_as_dentist = db.relationship('Appointment', foreign_keys='Appointment.dentist_id', backref='dentist', lazy='dynamic')
    treatment_plans = db.relationship('TreatmentPlan', backref='dentist_user', lazy='dynamic')
    
    def set_password(self, password):
        """Genera hash de la contraseña."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Verifica si el usuario es administrador."""
        return self.rol == 'admin'
    
    def is_dentist(self):
        """Verifica si el usuario es dentista."""
        return self.rol == 'dentist'
    
    def is_recepcionista(self):
        """Verifica si el usuario es recepcionista."""
        return self.rol == 'recepcionista'
    
    def __repr__(self):
        return f'<User {self.email}>'


class Patient(db.Model):
    """Paciente de la clínica."""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telefono = db.Column(db.String(20))
    fecha_nacimiento = db.Column(db.Date)
    direccion = db.Column(db.Text)
    dni = db.Column(db.String(20), unique=True, index=True)
    fecha_alta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notas_generales = db.Column(db.Text)
    password_hash = db.Column(db.String(255))  # Para login de pacientes
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relaciones
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    clinical_records = db.relationship('ClinicalRecord', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    odontograms = db.relationship('Odontogram', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    treatment_plans = db.relationship('TreatmentPlan', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Genera hash de la contraseña."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def nombre_completo(self):
        """Retorna el nombre completo del paciente."""
        return f"{self.nombre} {self.apellidos}"
    
    def __repr__(self):
        return f'<Patient {self.nombre_completo()}>'


class Appointment(db.Model):
    """Cita médica."""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    dentist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False, index=True)
    fecha_hora_fin = db.Column(db.DateTime, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True, index=True)  # Relación con Room
    sillon = db.Column(db.String(50))  # Mantener por compatibilidad, pero usar room_id
    motivo = db.Column(db.Text)
    estado = db.Column(db.String(50), default='programada', nullable=False)  # programada, confirmada, cancelada, realizada
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.patient.nombre_completo()}>'


class ClinicalRecord(db.Model):
    """Historia clínica general del paciente."""
    __tablename__ = 'clinical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    antecedentes_medicos = db.Column(db.Text)
    alergias = db.Column(db.Text)
    medicacion = db.Column(db.Text)
    observaciones_generales = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ClinicalRecord {self.id} - Patient {self.patient_id}>'


class Odontogram(db.Model):
    """Odontograma del paciente."""
    __tablename__ = 'odontograms'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    datos_json = db.Column(db.Text)  # JSON con el estado de las piezas dentales
    notas = db.Column(db.Text)
    
    def get_datos(self):
        """Retorna los datos del odontograma como diccionario."""
        if self.datos_json:
            try:
                return json.loads(self.datos_json)
            except:
                return {}
        return {}
    
    def set_datos(self, datos_dict):
        """Guarda los datos del odontograma como JSON."""
        self.datos_json = json.dumps(datos_dict)
    
    def __repr__(self):
        return f'<Odontogram {self.id} - Patient {self.patient_id}>'


class TreatmentPlan(db.Model):
    """Plan de tratamiento."""
    __tablename__ = 'treatment_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    dentist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    descripcion_general = db.Column(db.Text)
    estado = db.Column(db.String(50), default='propuesto', nullable=False)  # propuesto, en_curso, finalizado, cancelado
    coste_estimado = db.Column(db.Numeric(10, 2), default=0)
    
    # Relaciones
    treatment_items = db.relationship('TreatmentItem', backref='treatment_plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TreatmentPlan {self.id} - Patient {self.patient_id}>'


class TreatmentItem(db.Model):
    """Acto concreto dentro de un plan de tratamiento."""
    __tablename__ = 'treatment_items'
    
    id = db.Column(db.Integer, primary_key=True)
    treatment_plan_id = db.Column(db.Integer, db.ForeignKey('treatment_plans.id'), nullable=False, index=True)
    nombre_tratamiento = db.Column(db.String(200), nullable=False)
    pieza_dental = db.Column(db.String(20))  # Ej: "2.6", "1.1", etc.
    fecha_prevista = db.Column(db.Date)
    fecha_realizacion = db.Column(db.Date)
    estado = db.Column(db.String(50), default='pendiente', nullable=False)  # pendiente, realizado, cancelado
    precio = db.Column(db.Numeric(10, 2), default=0)
    
    def __repr__(self):
        return f'<TreatmentItem {self.id} - {self.nombre_tratamiento}>'


class Invoice(db.Model):
    """Factura."""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    estado_pago = db.Column(db.String(50), default='pendiente', nullable=False)  # pendiente, pagado, parcial
    metodo_pago = db.Column(db.String(50))  # efectivo, tarjeta, transferencia, financiación
    
    # Relaciones
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    
    def calcular_total_pagado(self):
        """Calcula el total pagado de esta factura."""
        return sum([p.cantidad for p in self.payments])
    
    def calcular_saldo_pendiente(self):
        """Calcula el saldo pendiente de esta factura."""
        return float(self.total) - float(self.calcular_total_pagado())
    
    def actualizar_estado_pago(self):
        """Actualiza el estado de pago según los pagos realizados."""
        total_pagado = self.calcular_total_pagado()
        if total_pagado == 0:
            self.estado_pago = 'pendiente'
        elif total_pagado >= float(self.total):
            self.estado_pago = 'pagado'
        else:
            self.estado_pago = 'parcial'
        db.session.commit()
    
    def __repr__(self):
        return f'<Invoice {self.id} - Patient {self.patient_id} - Total: {self.total}>'


class Payment(db.Model):
    """Pago realizado."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(50), nullable=False)
    referencia = db.Column(db.String(100))  # Referencia de pago
    
    def __repr__(self):
        return f'<Payment {self.id} - Invoice {self.invoice_id} - Cantidad: {self.cantidad}>'


class Notification(db.Model):
    """Registro de notificaciones enviadas a pacientes."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    tipo = db.Column(db.String(50), nullable=False)  # email, whatsapp
    asunto = db.Column(db.String(200))
    contenido_resumen = db.Column(db.Text)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado_envio = db.Column(db.String(50), default='pendiente', nullable=False)  # exitoso, error, pendiente
    
    def __repr__(self):
        return f'<Notification {self.id} - Patient {self.patient_id} - Tipo: {self.tipo}>'


class Room(db.Model):
    """Sala o sillón de la clínica."""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    appointments = db.relationship('Appointment', backref='room', lazy='dynamic')
    
    def __repr__(self):
        return f'<Room {self.nombre}>'


class ClinicSettings(db.Model):
    """Configuración de la clínica para facturas y presupuestos."""
    __tablename__ = 'clinic_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_clinica = db.Column(db.String(200), nullable=False)
    nif_cif = db.Column(db.String(50))
    direccion = db.Column(db.Text)
    codigo_postal = db.Column(db.String(10))
    ciudad = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    web = db.Column(db.String(200))
    logo_url = db.Column(db.String(500))
    numero_colegio = db.Column(db.String(50))  # Número de colegio profesional
    iban = db.Column(db.String(50))  # IBAN para facturas
    notas_pie_factura = db.Column(db.Text)  # Texto para el pie de página de facturas
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_settings(cls):
        """Obtiene la configuración de la clínica (solo debe haber una)."""
        settings = cls.query.first()
        if not settings:
            # Crear configuración por defecto si no existe
            settings = cls(nombre_clinica='Clínica Dental')
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<ClinicSettings {self.nombre_clinica}>'


class DoctorSchedule(db.Model):
    """Horario de trabajo de un doctor (días de la semana que trabaja)."""
    __tablename__ = 'doctor_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Lunes, 1=Martes, ..., 6=Domingo
    hora_inicio = db.Column(db.Time, nullable=False, default='09:00')
    hora_fin = db.Column(db.Time, nullable=False, default='20:00')
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relación
    doctor = db.relationship('User', backref='work_schedule')
    
    def __repr__(self):
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return f'<DoctorSchedule Doctor {self.doctor_id} - {dias[self.dia_semana]}>'


class TimeClock(db.Model):
    """Registro de fichaje de empleados (entrada/salida)."""
    __tablename__ = 'time_clocks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_entrada = db.Column(db.Time, nullable=True)
    hora_salida = db.Column(db.Time, nullable=True)
    horas_trabajadas = db.Column(db.Float, default=0.0)  # Horas calculadas
    horas_extras = db.Column(db.Float, default=0.0)  # Horas extras si supera la jornada normal
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    user = db.relationship('User', backref='time_records')
    
    def calcular_horas(self, horas_jornada_normal=8.0):
        """Calcula las horas trabajadas y extras."""
        if self.hora_entrada and self.hora_salida:
            # Convertir a datetime para calcular diferencia
            entrada_dt = datetime.combine(self.fecha, self.hora_entrada)
            salida_dt = datetime.combine(self.fecha, self.hora_salida)
            
            # Si la salida es anterior a la entrada, asumir que es del día siguiente
            if salida_dt < entrada_dt:
                salida_dt += timedelta(days=1)
            
            diferencia = salida_dt - entrada_dt
            horas_totales = diferencia.total_seconds() / 3600.0
            
            self.horas_trabajadas = round(horas_totales, 2)
            
            # Calcular horas extras
            if horas_totales > horas_jornada_normal:
                self.horas_extras = round(horas_totales - horas_jornada_normal, 2)
            else:
                self.horas_extras = 0.0
    
    def __repr__(self):
        return f'<TimeClock User {self.user_id} - {self.fecha}>'


class DayOff(db.Model):
    """Días libres/vacaciones de empleados."""
    __tablename__ = 'day_offs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    fecha_inicio = db.Column(db.Date, nullable=False, index=True)
    fecha_fin = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # vacaciones, baja_medica, permiso, etc.
    motivo = db.Column(db.Text)
    aprobado = db.Column(db.Boolean, default=False, nullable=False)
    aprobado_por = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref='days_off')
    aprobador = db.relationship('User', foreign_keys=[aprobado_por])
    
    def dias_totales(self):
        """Calcula el número total de días."""
        return (self.fecha_fin - self.fecha_inicio).days + 1
    
    def __repr__(self):
        return f'<DayOff User {self.user_id} - {self.fecha_inicio} a {self.fecha_fin}>'


class Honorario(db.Model):
    """Honorarios por tratamiento para cada doctor."""
    __tablename__ = 'honorarios'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    nombre_tratamiento = db.Column(db.String(200), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación
    doctor = db.relationship('User', backref='honorarios', lazy=True)
    
    # Índice único para evitar duplicados
    __table_args__ = (db.UniqueConstraint('doctor_id', 'nombre_tratamiento', name='_doctor_tratamiento_uc'),)
    
    def __repr__(self):
        return f'<Honorario {self.id} - Doctor {self.doctor_id} - {self.nombre_tratamiento}: {self.precio}>'



