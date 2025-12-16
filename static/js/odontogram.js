// JavaScript para el odontograma interactivo

let toothData = {};
let selectedTooth = null;
let saveUrl = '';

function initOdontogram(data, url) {
    toothData = data || {};
    saveUrl = url;
    
    // Reemplazar formas CSS con SVG realistas
    replaceToothShapesWithSVG();
    
    // Aplicar estados visuales a los dientes
    updateToothVisuals();
    
    // Añadir event listeners
    document.querySelectorAll('.tooth').forEach(tooth => {
        tooth.addEventListener('click', function() {
            selectTooth(this.dataset.tooth, this);
        });
    });
    
    // Listener para cambios en el select de estado
    const statusSelect = document.getElementById('toothStatus');
    if (statusSelect) {
        statusSelect.addEventListener('change', function() {
            if (selectedTooth) {
                updateToothStatus(selectedTooth, this.value);
            }
        });
    }
}

function replaceToothShapesWithSVG() {
    document.querySelectorAll('.tooth').forEach(toothElement => {
        const toothNumber = toothElement.dataset.tooth;
        const toothType = getToothType(toothNumber);
        const estado = toothData[toothNumber]?.estado || '';
        
        // Buscar el elemento tooth-shape
        const shapeElement = toothElement.querySelector('.tooth-shape');
        if (shapeElement) {
            // Crear contenedor SVG
            const svgContainer = document.createElement('div');
            svgContainer.className = 'tooth-svg';
            svgContainer.innerHTML = createToothSVG(toothType, estado);
            
            // Reemplazar
            shapeElement.replaceWith(svgContainer);
        }
    });
}

function selectTooth(toothNumber, element) {
    // Deseleccionar anterior
    document.querySelectorAll('.tooth').forEach(t => t.classList.remove('selected'));
    
    // Seleccionar nuevo
    element.classList.add('selected');
    selectedTooth = toothNumber;
    
    // Actualizar información
    updateToothInfo(toothNumber);
    
    // Cargar estado actual en el select
    const currentStatus = toothData[toothNumber]?.estado || '';
    const statusSelect = document.getElementById('toothStatus');
    if (statusSelect) {
        statusSelect.value = currentStatus;
    }
}

function updateToothInfo(toothNumber) {
    const infoDiv = document.getElementById('selectedToothInfo');
    if (!infoDiv) return;
    
    const tooth = document.querySelector(`[data-tooth="${toothNumber}"]`);
    const title = tooth ? tooth.title : `Pieza ${toothNumber}`;
    const estado = toothData[toothNumber]?.estado || 'Sin estado';
    
    infoDiv.innerHTML = `
        <strong>Pieza:</strong> ${toothNumber} - ${title}<br>
        <strong>Estado actual:</strong> ${estado || 'Sin estado'}
    `;
}

function updateToothStatus(toothNumber, status) {
    // Guardar en datos
    if (!toothData[toothNumber]) {
        toothData[toothNumber] = {};
    }
    
    if (status) {
        toothData[toothNumber].estado = status;
    } else {
        delete toothData[toothNumber].estado;
    }
    
    // Actualizar visualización
    updateToothVisual(toothNumber);
    updateToothInfo(toothNumber);
}

function updateToothVisual(toothNumber) {
    const toothElement = document.querySelector(`[data-tooth="${toothNumber}"]`);
    if (!toothElement) return;
    
    // Remover todas las clases de estado
    toothElement.classList.remove('sano', 'caries', 'empaste', 'corona', 
                                   'endodoncia', 'implante', 'extraccion', 'ausente');
    
    // Añadir clase según estado
    const estado = toothData[toothNumber]?.estado;
    if (estado) {
        toothElement.classList.add(estado);
    }
    
    // Actualizar SVG con nuevo estado
    const svgContainer = toothElement.querySelector('.tooth-svg');
    if (svgContainer) {
        const toothType = getToothType(toothNumber);
        svgContainer.innerHTML = createToothSVG(toothType, estado);
    }
}

function updateToothVisuals() {
    // Actualizar visualización de todos los dientes
    Object.keys(toothData).forEach(toothNumber => {
        updateToothVisual(toothNumber);
    });
}

function saveOdontogram() {
    const notas = document.getElementById('notas').value;
    
    // Preparar datos para enviar
    const dataToSend = {
        piezas: {},
        notas: notas
    };
    
    // Limpiar datos vacíos
    Object.keys(toothData).forEach(toothNumber => {
        if (toothData[toothNumber] && toothData[toothNumber].estado) {
            dataToSend.piezas[toothNumber] = {
                estado: toothData[toothNumber].estado
            };
        }
    });
    
    fetch(saveUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mostrar mensaje de éxito
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.innerHTML = `
                <i class="bi bi-check-circle"></i> Odontograma guardado correctamente.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.querySelector('.card-body').insertBefore(alertDiv, document.querySelector('.card-body').firstChild);
            
            // Auto-redirigir después de 2 segundos
            setTimeout(() => {
                const backUrl = window.location.href.split('/odontograma')[0];
                window.location.href = backUrl;
            }, 2000);
        } else {
            alert('Error al guardar el odontograma: ' + (data.error || 'Error desconocido'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al guardar el odontograma. Por favor, intenta nuevamente.');
    });
}

// Hacer función global para que pueda ser llamada desde el HTML
window.saveOdontogram = saveOdontogram;



