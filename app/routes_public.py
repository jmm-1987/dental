"""
Rutas públicas del portal web.
(Deshabilitado - redirige al login)
"""
from flask import Blueprint, redirect, url_for

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    """Redirige al login."""
    return redirect(url_for('auth.login'))


@bp.route('/servicios')
def servicios():
    """Redirige al login."""
    return redirect(url_for('auth.login'))


@bp.route('/contacto', methods=['GET', 'POST'])
def contacto():
    """Redirige al login."""
    return redirect(url_for('auth.login'))




