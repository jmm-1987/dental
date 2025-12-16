// Generador de SVG realistas para dientes

function createToothSVG(type, estado = '') {
    // Colores base según estado
    const colors = {
        'sano': { fill: '#f8f9fa', stroke: '#28a745', highlight: '#d4edda' },
        'caries': { fill: '#f8d7da', stroke: '#dc3545', highlight: '#f5c6cb' },
        'empaste': { fill: '#fff3cd', stroke: '#ffc107', highlight: '#ffeaa7' },
        'corona': { fill: '#e7f3ff', stroke: '#0d6efd', highlight: '#cfe2ff' },
        'endodoncia': { fill: '#d1ecf1', stroke: '#17a2b8', highlight: '#bee5eb' },
        'implante': { fill: '#f0e6ff', stroke: '#6f42c1', highlight: '#e0ccff' },
        'extraccion': { fill: '#e9ecef', stroke: '#6c757d', highlight: '#dee2e6' },
        'ausente': { fill: '#e9ecef', stroke: '#6c757d', highlight: '#dee2e6' },
        'default': { fill: '#ffffff', stroke: '#ced4da', highlight: '#f0f0f0' }
    };
    
    const color = colors[estado] || colors['default'];
    
    let svg = '';
    
    switch(type) {
        case 'incisivo':
            // Incisivos - forma rectangular con bordes redondeados
            svg = `
                <svg viewBox="0 0 40 60" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="grad-${estado || 'default'}" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:${color.fill};stop-opacity:1" />
                            <stop offset="50%" style="stop-color:${color.highlight};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:${color.fill};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <!-- Sombra interna -->
                    <ellipse cx="20" cy="10" rx="12" ry="4" fill="rgba(0,0,0,0.05)"/>
                    <!-- Diente principal -->
                    <rect x="8" y="5" width="24" height="50" rx="4" ry="8" 
                          fill="url(#grad-${estado || 'default'})" 
                          stroke="${color.stroke}" 
                          stroke-width="1.5"/>
                    <!-- Brillo superior -->
                    <ellipse cx="20" cy="12" rx="8" ry="3" fill="rgba(255,255,255,0.6)"/>
                    ${estado === 'caries' ? '<circle cx="20" cy="30" r="6" fill="#dc3545" opacity="0.7"/>' : ''}
                    ${estado === 'empaste' ? '<rect x="14" y="25" width="12" height="8" rx="2" fill="#ffc107" opacity="0.8"/>' : ''}
                    ${estado === 'corona' ? '<rect x="8" y="5" width="24" height="15" rx="4" fill="#0d6efd" opacity="0.6"/>' : ''}
                    ${estado === 'endodoncia' ? '<text x="20" y="35" font-size="14" fill="#17a2b8" text-anchor="middle" font-weight="bold">E</text>' : ''}
                    ${estado === 'implante' ? '<text x="20" y="35" font-size="14" fill="#6f42c1" text-anchor="middle" font-weight="bold">I</text>' : ''}
                    ${estado === 'extraccion' || estado === 'ausente' ? '<line x1="10" y1="10" x2="30" y2="50" stroke="#dc3545" stroke-width="2"/>' : ''}
                </svg>
            `;
            break;
            
        case 'canino':
            // Caninos - forma puntiaguda
            svg = `
                <svg viewBox="0 0 40 65" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="grad-canino-${estado || 'default'}" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:${color.fill};stop-opacity:1" />
                            <stop offset="50%" style="stop-color:${color.highlight};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:${color.fill};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <ellipse cx="20" cy="10" rx="10" ry="3" fill="rgba(0,0,0,0.05)"/>
                    <path d="M 12 5 Q 20 0 28 5 L 26 55 Q 20 60 14 55 Z" 
                          fill="url(#grad-canino-${estado || 'default'})" 
                          stroke="${color.stroke}" 
                          stroke-width="1.5"/>
                    <ellipse cx="20" cy="12" rx="6" ry="2" fill="rgba(255,255,255,0.6)"/>
                    ${estado === 'caries' ? '<circle cx="20" cy="30" r="5" fill="#dc3545" opacity="0.7"/>' : ''}
                    ${estado === 'empaste' ? '<rect x="15" y="25" width="10" height="8" rx="2" fill="#ffc107" opacity="0.8"/>' : ''}
                    ${estado === 'corona' ? '<path d="M 12 5 Q 20 0 28 5 L 26 20 Q 20 25 14 20 Z" fill="#0d6efd" opacity="0.6"/>' : ''}
                    ${estado === 'endodoncia' ? '<text x="20" y="35" font-size="12" fill="#17a2b8" text-anchor="middle" font-weight="bold">E</text>' : ''}
                    ${estado === 'implante' ? '<text x="20" y="35" font-size="12" fill="#6f42c1" text-anchor="middle" font-weight="bold">I</text>' : ''}
                    ${estado === 'extraccion' || estado === 'ausente' ? '<line x1="12" y1="8" x2="28" y2="52" stroke="#dc3545" stroke-width="2"/>' : ''}
                </svg>
            `;
            break;
            
        case 'premolar':
            // Premolares - forma intermedia
            svg = `
                <svg viewBox="0 0 45 60" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="grad-premolar-${estado || 'default'}" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:${color.fill};stop-opacity:1" />
                            <stop offset="50%" style="stop-color:${color.highlight};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:${color.fill};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <ellipse cx="22.5" cy="10" rx="14" ry="4" fill="rgba(0,0,0,0.05)"/>
                    <path d="M 10 5 Q 15 2 22.5 5 Q 30 2 35 5 L 33 55 Q 22.5 58 12 55 Z" 
                          fill="url(#grad-premolar-${estado || 'default'})" 
                          stroke="${color.stroke}" 
                          stroke-width="1.5"/>
                    <ellipse cx="22.5" cy="12" rx="10" ry="3" fill="rgba(255,255,255,0.6)"/>
                    <!-- Surcos -->
                    <path d="M 18 25 L 18 35 M 22.5 25 L 22.5 35 M 27 25 L 27 35" 
                          stroke="${color.stroke}" 
                          stroke-width="0.8" 
                          opacity="0.5"/>
                    ${estado === 'caries' ? '<circle cx="22.5" cy="30" r="6" fill="#dc3545" opacity="0.7"/>' : ''}
                    ${estado === 'empaste' ? '<rect x="16" y="25" width="13" height="10" rx="2" fill="#ffc107" opacity="0.8"/>' : ''}
                    ${estado === 'corona' ? '<path d="M 10 5 Q 15 2 22.5 5 Q 30 2 35 5 L 33 20 Q 22.5 23 12 20 Z" fill="#0d6efd" opacity="0.6"/>' : ''}
                    ${estado === 'endodoncia' ? '<text x="22.5" y="35" font-size="13" fill="#17a2b8" text-anchor="middle" font-weight="bold">E</text>' : ''}
                    ${estado === 'implante' ? '<text x="22.5" y="35" font-size="13" fill="#6f42c1" text-anchor="middle" font-weight="bold">I</text>' : ''}
                    ${estado === 'extraccion' || estado === 'ausente' ? '<line x1="10" y1="8" x2="35" y2="52" stroke="#dc3545" stroke-width="2"/>' : ''}
                </svg>
            `;
            break;
            
        case 'molar':
            // Molares - forma más cuadrada con surcos
            svg = `
                <svg viewBox="0 0 50 65" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="grad-molar-${estado || 'default'}" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:${color.fill};stop-opacity:1" />
                            <stop offset="50%" style="stop-color:${color.highlight};stop-opacity:1" />
                            <stop offset="100%" style="stop-color:${color.fill};stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <ellipse cx="25" cy="10" rx="18" ry="5" fill="rgba(0,0,0,0.05)"/>
                    <path d="M 8 5 Q 12 3 18 5 Q 25 2 32 5 Q 38 3 42 5 L 40 60 Q 25 63 10 60 Z" 
                          fill="url(#grad-molar-${estado || 'default'})" 
                          stroke="${color.stroke}" 
                          stroke-width="1.5"/>
                    <ellipse cx="25" cy="12" rx="15" ry="4" fill="rgba(255,255,255,0.6)"/>
                    <!-- Surcos molares -->
                    <path d="M 15 25 Q 20 30 25 25 Q 30 30 35 25 M 15 35 Q 20 40 25 35 Q 30 40 35 35" 
                          stroke="${color.stroke}" 
                          stroke-width="1" 
                          fill="none" 
                          opacity="0.4"/>
                    ${estado === 'caries' ? '<circle cx="25" cy="30" r="7" fill="#dc3545" opacity="0.7"/>' : ''}
                    ${estado === 'empaste' ? '<rect x="18" y="25" width="14" height="12" rx="2" fill="#ffc107" opacity="0.8"/>' : ''}
                    ${estado === 'corona' ? '<path d="M 8 5 Q 12 3 18 5 Q 25 2 32 5 Q 38 3 42 5 L 40 22 Q 25 25 10 22 Z" fill="#0d6efd" opacity="0.6"/>' : ''}
                    ${estado === 'endodoncia' ? '<text x="25" y="35" font-size="14" fill="#17a2b8" text-anchor="middle" font-weight="bold">E</text>' : ''}
                    ${estado === 'implante' ? '<text x="25" y="35" font-size="14" fill="#6f42c1" text-anchor="middle" font-weight="bold">I</text>' : ''}
                    ${estado === 'extraccion' || estado === 'ausente' ? '<line x1="8" y1="8" x2="42" y2="57" stroke="#dc3545" stroke-width="2"/>' : ''}
                </svg>
            `;
            break;
    }
    
    return svg;
}

function getToothType(toothNumber) {
    const num = parseInt(toothNumber.split('.')[1]);
    if (num === 1 || num === 2) return 'incisivo';
    if (num === 3) return 'canino';
    if (num === 4 || num === 5) return 'premolar';
    if (num === 6 || num === 7 || num === 8) return 'molar';
    return 'incisivo';
}

// Hacer funciones globales
window.createToothSVG = createToothSVG;
window.getToothType = getToothType;


