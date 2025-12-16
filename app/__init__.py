"""
Aplicación Flask para gestión de clínica dental.
Estructura modular con blueprints.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='development'):
    """Factory function para crear la aplicación Flask."""
    # Obtener el directorio base (raíz del proyecto)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Crear Flask app especificando el directorio de templates y static
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    
    # Configuración
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Manejar DATABASE_URL de Render (que usa postgres://) y convertir a postgresql://
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or \
        f'sqlite:///{os.path.join(basedir, "clinic.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configurar LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Registrar blueprints
    from app.routes_auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes_panel import bp as panel_bp
    app.register_blueprint(panel_bp, url_prefix='/panel')
    
    from app.routes_public import bp as public_bp
    app.register_blueprint(public_bp)
    
    from app.routes_patient import bp as patient_bp
    app.register_blueprint(patient_bp, url_prefix='/paciente')
    
    from flask import redirect, url_for
    
    # Context processor para pasar configuración de clínica a todas las plantillas
    @app.context_processor
    def inject_clinic_settings():
        from app.models import ClinicSettings
        try:
            settings = ClinicSettings.get_settings()
            return dict(clinic_settings=settings)
        except:
            return dict(clinic_settings=None)
    
    # Ruta raíz - redirige directamente al login
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    return app

