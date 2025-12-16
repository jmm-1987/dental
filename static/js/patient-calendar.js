// Calendario semanal para pacientes

let currentWeekStart = new Date();
let disponibilidad = [];
let selectedDentist = null;

// Usar variables globales si están disponibles
const diasSemana = window.diasSemana || ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const meses = window.meses || ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const formatDate = window.formatDate || function(date) { return date.toISOString().split('T')[0]; };
const getWeekStart = window.getWeekStart || function(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(d.setDate(diff));
};

function loadAvailability() {
    const dentistId = document.getElementById('select-dentist').value;
    if (!dentistId) {
        document.getElementById('calendar-body').innerHTML = '<div class="col-12 text-center p-4"><p class="text-muted">Selecciona un dentista para ver disponibilidad</p></div>';
        return;
    }
    
    selectedDentist = dentistId;
    const fechaStr = formatDate(currentWeekStart);
    
    // Cargar disponibilidad para cada día de la semana
    const promises = [];
    for (let i = 0; i < 7; i++) {
        const fecha = new Date(currentWeekStart);
        fecha.setDate(fecha.getDate() + i);
        const fechaStr = formatDate(fecha);
        
        promises.push(
            fetch(`/paciente/calendario/disponibilidad?fecha=${fechaStr}&dentist_id=${dentistId}`)
                .then(response => response.json())
        );
    }
    
    Promise.all(promises).then(results => {
        disponibilidad = results.flatMap(r => r.tramos);
        renderPatientCalendar();
    });
}

function renderPatientCalendar() {
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
                    // Buscar disponibilidad en este tramo
                    const tramo = disponibilidad.find(t => {
                        const tramoStart = new Date(t.start);
                        return tramoStart.getTime() === fecha.getTime();
                    });
                    
                    if (tramo && tramo.disponible) {
                        cell.classList.add('disponible');
                        cell.onclick = () => openRequestAppointmentModal(fecha);
                    } else {
                        cell.classList.add('ocupado');
                    }
                }
                
                calendarBody.appendChild(cell);
            }
        }
    }
}

function openRequestAppointmentModal(fecha) {
    if (!selectedDentist) {
        alert('Por favor selecciona un dentista primero');
        return;
    }
    
    const fechaFin = new Date(fecha);
    fechaFin.setMinutes(fechaFin.getMinutes() + 30);
    
    document.getElementById('cita-start-time').value = fecha.toISOString();
    document.getElementById('cita-end-time').value = fechaFin.toISOString();
    document.getElementById('cita-dentist-id').value = selectedDentist;
    document.getElementById('cita-datetime').value = `${fecha.toLocaleDateString('es-ES')} ${fecha.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}`;
    
    const modal = new bootstrap.Modal(document.getElementById('modalSolicitarCita'));
    modal.show();
}

function requestAppointment() {
    const form = document.getElementById('formSolicitarCita');
    const formData = new FormData(form);
    
    const data = {
        dentist_id: parseInt(formData.get('dentist_id')),
        start: formData.get('start'),
        end: formData.get('end'),
        motivo: formData.get('motivo')
    };
    
    fetch('/paciente/calendario/solicitar-cita', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('modalSolicitarCita')).hide();
            alert(data.message || 'Cita solicitada correctamente');
            loadAvailability();
        } else {
            alert('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al solicitar la cita');
    });
}

// Sobrescribir funciones de navegación para recargar disponibilidad
const originalPreviousWeek = previousWeek;
const originalNextWeek = nextWeek;
const originalGoToToday = goToToday;

function previousWeek() {
    currentWeekStart = new Date(currentWeekStart);
    currentWeekStart.setDate(currentWeekStart.getDate() - 7);
    updateCalendarHeaders();
    if (selectedDentist) {
        loadAvailability();
    }
}

function nextWeek() {
    currentWeekStart = new Date(currentWeekStart);
    currentWeekStart.setDate(currentWeekStart.getDate() + 7);
    updateCalendarHeaders();
    if (selectedDentist) {
        loadAvailability();
    }
}

function goToToday() {
    currentWeekStart = getWeekStart(new Date());
    updateCalendarHeaders();
    if (selectedDentist) {
        loadAvailability();
    }
}

function updateCalendarHeaders() {
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
}

// Inicializar
if (document.getElementById('select-dentist')) {
    currentWeekStart = getWeekStart(new Date());
    updateCalendarHeaders();
}

