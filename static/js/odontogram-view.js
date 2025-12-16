// JavaScript para visualización del odontograma (solo lectura)

function renderOdontogramView(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Limpiar contenedor
    container.innerHTML = '';
    
    // Crear estructura del odontograma
    const odontogramHTML = `
        <div class="odontogram-container">
            <!-- Vista superior (maxilar) -->
            <div class="jaw-section">
                <div class="jaw-label">Maxilar Superior</div>
                <div class="teeth-row">
                    <!-- Cuadrante 1 (derecha superior) -->
                    <div class="quadrant quadrant-1">
                        ${createTooth('1.8', data, 'Muela del juicio superior derecha')}
                        ${createTooth('1.7', data, 'Segundo molar superior derecho')}
                        ${createTooth('1.6', data, 'Primer molar superior derecho')}
                        ${createTooth('1.5', data, 'Segundo premolar superior derecho')}
                        ${createTooth('1.4', data, 'Primer premolar superior derecho')}
                        ${createTooth('1.3', data, 'Canino superior derecho')}
                        ${createTooth('1.2', data, 'Incisivo lateral superior derecho')}
                        ${createTooth('1.1', data, 'Incisivo central superior derecho')}
                    </div>
                    
                    <!-- Cuadrante 2 (izquierda superior) -->
                    <div class="quadrant quadrant-2">
                        ${createTooth('2.1', data, 'Incisivo central superior izquierdo')}
                        ${createTooth('2.2', data, 'Incisivo lateral superior izquierdo')}
                        ${createTooth('2.3', data, 'Canino superior izquierdo')}
                        ${createTooth('2.4', data, 'Primer premolar superior izquierdo')}
                        ${createTooth('2.5', data, 'Segundo premolar superior izquierdo')}
                        ${createTooth('2.6', data, 'Primer molar superior izquierdo')}
                        ${createTooth('2.7', data, 'Segundo molar superior izquierdo')}
                        ${createTooth('2.8', data, 'Muela del juicio superior izquierda')}
                    </div>
                </div>
            </div>
            
            <!-- Vista inferior (mandíbula) -->
            <div class="jaw-section">
                <div class="jaw-label">Mandíbula Inferior</div>
                <div class="teeth-row">
                    <!-- Cuadrante 3 (izquierda inferior) -->
                    <div class="quadrant quadrant-3">
                        ${createTooth('3.8', data, 'Muela del juicio inferior izquierda')}
                        ${createTooth('3.7', data, 'Segundo molar inferior izquierdo')}
                        ${createTooth('3.6', data, 'Primer molar inferior izquierdo')}
                        ${createTooth('3.5', data, 'Segundo premolar inferior izquierdo')}
                        ${createTooth('3.4', data, 'Primer premolar inferior izquierdo')}
                        ${createTooth('3.3', data, 'Canino inferior izquierdo')}
                        ${createTooth('3.2', data, 'Incisivo lateral inferior izquierdo')}
                        ${createTooth('3.1', data, 'Incisivo central inferior izquierdo')}
                    </div>
                    
                    <!-- Cuadrante 4 (derecha inferior) -->
                    <div class="quadrant quadrant-4">
                        ${createTooth('4.1', data, 'Incisivo central inferior derecho')}
                        ${createTooth('4.2', data, 'Incisivo lateral inferior derecho')}
                        ${createTooth('4.3', data, 'Canino inferior derecho')}
                        ${createTooth('4.4', data, 'Primer premolar inferior derecho')}
                        ${createTooth('4.5', data, 'Segundo premolar inferior derecho')}
                        ${createTooth('4.6', data, 'Primer molar inferior derecho')}
                        ${createTooth('4.7', data, 'Segundo molar inferior derecho')}
                        ${createTooth('4.8', data, 'Muela del juicio inferior derecha')}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Leyenda -->
        <div class="mt-3">
            <h6>Leyenda:</h6>
            <div class="legend-container">
                <span class="legend-item"><span class="legend-color sano"></span> Sano</span>
                <span class="legend-item"><span class="legend-color caries"></span> Caries</span>
                <span class="legend-item"><span class="legend-color empaste"></span> Empaste</span>
                <span class="legend-item"><span class="legend-color corona"></span> Corona</span>
                <span class="legend-item"><span class="legend-color endodoncia"></span> Endodoncia</span>
                <span class="legend-item"><span class="legend-color implante"></span> Implante</span>
                <span class="legend-item"><span class="legend-color extraccion"></span> Extracción</span>
                <span class="legend-item"><span class="legend-color ausente"></span> Ausente</span>
            </div>
        </div>
    `;
    
    container.innerHTML = odontogramHTML;
}

function createTooth(toothNumber, data, title) {
    const estado = data[toothNumber]?.estado || '';
    const estadoClass = estado ? ` ${estado}` : '';
    const estadoText = estado || 'Sin estado';
    
    // Extraer número corto (ej: 1.8 -> 18)
    const shortNumber = toothNumber.replace('.', '');
    
    // Determinar tipo de diente
    const toothType = getToothType(toothNumber);
    
    return `
        <div class="tooth${estadoClass}" data-tooth="${toothNumber}" title="${title} - ${estadoText}">
            <div class="tooth-number">${shortNumber}</div>
            <div class="tooth-svg">${createToothSVG(toothType, estado)}</div>
        </div>
    `;
}

// Hacer función global
window.renderOdontogramView = renderOdontogramView;



