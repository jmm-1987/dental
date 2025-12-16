"""
Rutas de autenticación (login, registro, logout).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Patient
from functools import wraps
from datetime import datetime

bp = Blueprint('auth', __name__)


def role_required(*roles):
    """Decorador para requerir roles específicos."""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.rol not in roles:
                flash('No tienes permisos para acceder a esta página.', 'error')
                return redirect(url_for('panel.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login solo para usuarios internos (no pacientes)."""
    if current_user.is_authenticated:
        if isinstance(current_user, User):
            return redirect(url_for('panel.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Buscar por nombre de usuario
        user = User.query.filter_by(nombre=username, activo=True).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('panel.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos pacientes."""
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellidos = request.form.get('apellidos')
        email = request.form.get('email')
        password = request.form.get('password')
        telefono = request.form.get('telefono')
        fecha_nacimiento = request.form.get('fecha_nacimiento')
        dni = request.form.get('dni')
        
        # Validar que el email no exista
        if Patient.query.filter_by(email=email).first():
            flash('Este email ya está registrado.', 'error')
            return render_template('auth/register.html')
        
        # Crear nuevo paciente
        patient = Patient(
            nombre=nombre,
            apellidos=apellidos,
            email=email,
            telefono=telefono,
            dni=dni if dni else None,
            fecha_nacimiento=datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date() if fecha_nacimiento else None
        )
        patient.set_password(password)
        
        try:
            db.session.add(patient)
            db.session.commit()
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar. Intenta nuevamente.', 'error')
    
    return render_template('auth/register.html')


@bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión."""
    logout_user()
    session.pop('patient_logged_in', None)
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))

