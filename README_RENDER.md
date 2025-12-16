# Despliegue en Render

## Configuración para Render

Esta aplicación está preparada para desplegarse en Render.

### Pasos para desplegar:

1. **Crear cuenta en Render** (si no la tienes): https://render.com

2. **Crear una nueva Web Service**:
   - Conecta tu repositorio de GitHub/GitLab
   - Selecciona el branch principal
   - Render detectará automáticamente el `render.yaml` o `Procfile`

3. **Configurar variables de entorno**:
   - `SECRET_KEY`: Genera una clave secreta aleatoria (Render puede generarla automáticamente)
   - `DATABASE_URL`: Se configurará automáticamente si creas la base de datos desde Render

4. **Crear base de datos PostgreSQL**:
   - En Render, crea una nueva PostgreSQL Database
   - Render conectará automáticamente la base de datos al servicio web

5. **Inicializar la base de datos**:
   - Una vez desplegado, ejecuta las migraciones desde el shell de Render:
     ```bash
     python init_db.py
     ```

### Archivos de configuración:

- `render.yaml`: Configuración del servicio y base de datos
- `Procfile`: Comando para iniciar la aplicación con Gunicorn
- `requirements.txt`: Dependencias de Python (incluye gunicorn y psycopg2-binary)

### Notas importantes:

- La aplicación ahora redirige directamente al login (no hay página pública)
- Solo los usuarios internos pueden iniciar sesión (no pacientes)
- La base de datos se inicializa con usuarios por defecto:
  - Admin: admin@clinicadental.com / admin123
  - Recepcionista: recepcionista@clinicadental.com / recepcionista123
  - Dentista: dentista@clinicadental.com / dentista123

### Comandos útiles en Render:

- Ver logs: `render logs`
- Shell: `render shell`
- Ejecutar migraciones: `python migrate_db.py` (si es necesario)

