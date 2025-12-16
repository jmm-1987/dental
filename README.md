# Sistema de Gestión de Clínica Dental

Aplicación web completa para la gestión de una clínica dental, desarrollada con Flask, SQLAlchemy, SQLite y Jinja2.

## 🎯 Características

### Panel Interno (Administrativos y Dentistas)
- **Calendario Semanal Interactivo**: Vista semanal con tramos de 30 minutos para gestionar citas visualmente
- **Gestión de Pacientes**: CRUD completo de pacientes con historial completo
- **Agenda de Citas**: Visualización y gestión de citas con filtros por fecha, dentista y estado
- **Creación de Citas desde Calendario**: Click en cualquier tramo disponible para crear cita rápidamente
- **Historia Clínica**: Registro de antecedentes médicos, alergias y medicación
- **Odontograma**: Sistema interactivo para registrar el estado de las piezas dentales
- **Planes de Tratamiento**: Creación y seguimiento de tratamientos con actos individuales
- **Facturación**: Gestión de facturas y pagos parciales
- **Notificaciones**: Sistema de registro de comunicaciones con pacientes (simulado)

### Portal Público y Área de Paciente
- **Página Principal**: Información de la clínica y servicios
- **Registro y Login**: Sistema de autenticación para pacientes
- **Área Privada del Paciente**:
  - **Calendario Semanal Interactivo**: Visualización de disponibilidad y solicitud de citas con tramos de 30 minutos
  - Visualización de citas (próximas y pasadas)
  - Solicitud de nuevas citas desde calendario (sincronizado con el panel interno)
  - Consulta de tratamientos (versión amigable)
  - Visualización de facturas y pagos

## 🏗️ Estructura del Proyecto

```
dental/
├── app/
│   ├── __init__.py          # Configuración de la aplicación Flask
│   ├── models.py            # Modelos SQLAlchemy
│   ├── routes_auth.py       # Rutas de autenticación
│   ├── routes_panel.py      # Rutas del panel interno
│   ├── routes_public.py     # Rutas públicas
│   └── routes_patient.py    # Rutas del área de paciente
├── templates/
│   ├── base.html            # Plantilla base
│   ├── auth/                # Plantillas de autenticación
│   ├── public/              # Plantillas públicas
│   ├── panel/               # Plantillas del panel interno
│   └── patient/             # Plantillas del área de paciente
├── static/
│   ├── css/
│   │   └── style.css        # Estilos personalizados
│   └── js/
│       └── main.js          # JavaScript principal
├── init_db.py               # Script de inicialización de BD
├── run.py                   # Script para ejecutar la app
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo
```

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalación

```bash
# Clonar o descargar el proyecto
cd dental

# Crear un entorno virtual (recomendado)
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Inicializar la Base de Datos

```bash
python init_db.py
```

Esto creará:
- Todas las tablas necesarias en `clinic.db`
- Usuario administrador por defecto:
  - Email: `admin@clinicadental.com`
  - Contraseña: `admin123`
- Usuario recepcionista:
  - Email: `recepcion@clinicadental.com`
  - Contraseña: `recepcion123`
- Usuario dentista:
  - Email: `dentista@clinicadental.com`
  - Contraseña: `dentista123`

**⚠️ IMPORTANTE**: Cambia estas contraseñas en producción.

### 3.1. Generar Datos de Muestra (Opcional)

Para cargar 50 pacientes de muestra con tratamientos y citas:

```bash
python generate_sample_data.py
```

Esto creará:
- 50 pacientes con datos realistas (nombres españoles, DNI, teléfonos, etc.)
- Planes de tratamiento con múltiples actos
- Citas pasadas y futuras
- Historias clínicas básicas

**Nota**: Todos los pacientes de muestra tienen la contraseña: `paciente123`

### 4. Ejecutar la Aplicación

```bash
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 👥 Roles y Permisos

### Administrador (`admin`)
- Acceso completo a todas las funcionalidades
- Gestión de usuarios, pacientes, citas, tratamientos y facturación

### Recepcionista (`recepcionista`)
- Gestión de pacientes y citas
- Creación de facturas y registro de pagos
- Envío de notificaciones

### Dentista (`dentista`)
- Visualización de sus propias citas
- Acceso a pacientes asignados
- Gestión de tratamientos de sus pacientes
- Edición de historia clínica y odontograma

### Paciente
- Acceso solo a su área privada
- Visualización de citas, tratamientos y facturas
- Solicitud de nuevas citas

## 📊 Modelos de Datos

- **User**: Usuarios internos (admin, recepcionista, dentista)
- **Patient**: Pacientes de la clínica
- **Appointment**: Citas médicas
- **ClinicalRecord**: Historia clínica general
- **Odontogram**: Odontograma del paciente
- **TreatmentPlan**: Planes de tratamiento
- **TreatmentItem**: Actos concretos dentro de un plan
- **Invoice**: Facturas
- **Payment**: Pagos realizados
- **Notification**: Registro de notificaciones enviadas

## 🎨 Diseño

La aplicación utiliza:
- **Bootstrap 5** para el diseño responsive
- **Bootstrap Icons** para iconos
- CSS personalizado en `static/css/style.css`
- JavaScript ligero en `static/js/main.js` para interactividad

## 🔒 Seguridad

- Autenticación con Flask-Login
- Contraseñas hasheadas con Werkzeug
- Protección de rutas con decoradores `@login_required` y `@role_required`
- Validación de permisos según roles

## 📝 Notas de Desarrollo

### Modularidad
El proyecto está diseñado de forma modular para facilitar la venta por módulos:
- Cada funcionalidad está separada en blueprints
- Las plantillas están organizadas por secciones
- Los modelos están centralizados pero pueden extenderse

### Base de Datos
- SQLite para desarrollo (fácil de migrar a PostgreSQL/MySQL)
- SQLAlchemy ORM para abstracción de base de datos
- Flask-Migrate incluido para futuras migraciones

### Notificaciones
El sistema de notificaciones está simulado. Para producción, integrar:
- Servicio de email (SMTP, SendGrid, etc.)
- API de WhatsApp Business
- Sistema de recordatorios automáticos (Celery + cron)

## 🐛 Solución de Problemas

### Error al crear tablas
```bash
# Eliminar el archivo clinic.db y ejecutar nuevamente
rm clinic.db
python init_db.py
```

### Error de importación
Asegúrate de estar en el directorio raíz del proyecto y que el entorno virtual esté activado.

## 📄 Licencia

Este proyecto es de código abierto y está disponible para uso comercial.

## 👨‍💻 Desarrollo

Para contribuir o personalizar:
1. Revisa la estructura modular del proyecto
2. Cada módulo puede venderse/activarse independientemente
3. Extiende los modelos según necesidades específicas
4. Añade nuevas funcionalidades siguiendo el patrón de blueprints

---

**Desarrollado con Flask + SQLAlchemy + SQLite + Jinja2**

