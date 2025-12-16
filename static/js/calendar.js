// Calendario semanal para el panel interno

// Días de la semana en español (globales para compartir)
window.diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
window.meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

let currentWeekStart = new Date();
let citas = [];

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Ajustar para que lunes sea día 1
    return new Date(d.setDate(diff));
}

// Hacer funciones globales para compartir
window.formatDate = formatDate;
window.getWeekStart = getWeekStart;

function previousWeek() {
    currentWeekStart = new Date(currentWeekStart);
    currentWeekStart.setDate(currentWeekStart.getDate() - 7);
    loadCalendar();
}

function nextWeek() {
    currentWeekStart = new Date(currentWeekStart);
    currentWeekStart.setDate(currentWeekStart.getDate() + 7);
    loadCalendar();
}

function goToToday() {
    currentWeekStart = getWeekStart(new Date());
    loadCalendar();
}

function loadCalendar() {
    const fechaStr = formatDate(currentWeekStart);
    
    // Actualizar encabezados
    for (let i = 0; i < 7; i++) {
        const fecha = new Date(currentWeekStart);
        fecha.setDate(fecha.getDate() + i);
        
        const dayName = document.getElementById(`day-name-${i}`);
        const dayDate = document.getElementById(`day-date-${i}`);
        
        if (dayName) dayName.textContent = diasSemana[i];
        if (dayDate) {
            dayDate.textContent = `${fecha.getDate()} ${meses[fecha.getMonth()]}`;
        }
    }
    
    // Cargar citas de la semana
    fetch(`/panel/calendario/citas-semana?fecha=${fechaStr}`)
        .then(response => response.json())
        .then(data => {
            citas = data.citas;
            renderCalendar();
        })
        .catch(error => {
            console.error('Error al cargar citas:', error);
        });
}

function renderCalendar() {
    const calendarBody = document.getElementById('calendar-body');
    if (!calendarBody) return;
    
    calendarBody.innerHTML = '';
    
    // Generar tramos de 30 minutos de 9:00 a 20:00
    const horaInicio = 9;
    const horaFin = 20;
    
    for (let hora = horaInicio; hora < horaFin; hora++) {
        for (let minuto of [0, 30]) {
            // Columna de tiempo
            const timeSlot = document.createElement('div');
            timeSlot.className = 'calendar-time-slot';
            timeSlot.textContent = `${String(hora).padStart(2, '0')}:${String(minuto).padStart(2, '0')}`;
            calendarBody.appendChild(timeSlot);
            
            // Celdas para cada día
            for (let dia = 0; dia < 7; dia++) {
                const fecha = new Date(currentWeekStart);
                fecha.setDate(fecha.getDate() + dia);
                fecha.setHours(hora, minuto, 0, 0);
                
                const cell = document.createElement('div');
                cell.className = 'calendar-cell';
                cell.dataset.datetime = fecha.toISOString();
                
                // Verificar si es pasado
                if (fecha < new Date()) {
                    cell.classList.add('pasado');
                } else {
                    // Buscar citas en este tramo
                    const citaEnTramo = citas.find(c => {
                        const citaStart = new Date(c.start);
                        const citaEnd = new Date(c.end);
                        return fecha >= citaStart && fecha < citaEnd;
                    });
                    
                    if (citaEnTramo) {
                        cell.classList.add('ocupado');
                        const badge = document.createElement('div');
                        badge.className = `cita-badge ${citaEnTramo.estado}`;
                        badge.textContent = citaEnTramo.patient_name;
                        badge.title = `${citaEnTramo.patient_name} - ${citaEnTramo.dentist_name}\n${citaEnTramo.motivo || 'Sin motivo'}\nClick para ver detalles`;
                        badge.style.cursor = 'pointer';
                        badge.onclick = (e) => {
                            e.stopPropagation();
                            window.location.href = `/panel/citas/${citaEnTramo.id}/editar?from=dashboard`;
                        };
                        cell.appendChild(badge);
                    } else {
                        cell.classList.add('disponible');
                        cell.onclick = () => openNewAppointmentModal(fecha);
                    }
                }
                
                calendarBody.appendChild(cell);
            }
        }
    }
}

function openNewAppointmentModal(fecha) {
    const fechaFin = new Date(fecha);
    fechaFin.setMinutes(fechaFin.getMinutes() + 30);
    
    document.getElementById('cita-start-time').value = fecha.toISOString();
    document.getElementById('cita-end-time').value = fechaFin.toISOString();
    document.getElementById('cita-datetime').value = `${fecha.toLocaleDateString('es-ES')} ${fecha.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}`;
    
    // Limpiar formulario
    document.getElementById('formNuevaCita').reset();
    
    // Restaurar valores de fecha/hora
    document.getElementById('cita-start-time').value = fecha.toISOString();
    document.getElementById('cita-end-time').value = fechaFin.toISOString();
    document.getElementById('cita-datetime').value = `${fecha.toLocaleDateString('es-ES')} ${fecha.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}`;
    
    const modal = new bootstrap.Modal(document.getElementById('modalNuevaCita'));
    modal.show();
}

function saveAppointment() {
    const form = document.getElementById('formNuevaCita');
    const formData = new FormData(form);
    
    const data = {
        patient_id: parseInt(formData.get('patient_id')),
        dentist_id: parseInt(formData.get('dentist_id')),
        start: formData.get('start'),
        end: formData.get('end'),
        motivo: formData.get('motivo'),
        room_id: formData.get('room_id') ? parseInt(formData.get('room_id')) : null,
        sillon: formData.get('sillon') || null
    };
    
    fetch('/panel/calendario/crear-cita', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('modalNuevaCita')).hide();
            loadCalendar();
            // Mostrar mensaje de éxito (puedes usar toast o alert)
            alert('Cita creada correctamente');
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al crear la cita');
    });
}

// Inicializar calendario al cargar la página
if (document.getElementById('calendar-body')) {
    currentWeekStart = getWeekStart(new Date());
    loadCalendar();
}

