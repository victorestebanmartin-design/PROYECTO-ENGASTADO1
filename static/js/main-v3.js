/**
 * Sistema de Engastado Automático V3.0
 * JavaScript Principal - Modo Avanzado
 */

// Variables globales V3
let bonoActual = null;
let proyectoActual = null;
let datosV3 = {};
let puestoSeleccionado = null;
let maquinaSeleccionada = null;
let terminalesAsignados = [];
let carrosDelBono = []; // Todos los carros del bono
let carroActualIndex = 0; // Índice del carro actual en proceso
let terminalActual = null; // Terminal en el que estamos trabajando
let terminalesCompletados = []; // Lista de terminales ya completados
let paquetesActuales = []; // Paquetes del carro actual
let gruposEtiquetasCache = null; // Cache de grupos de etiquetas

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    const codigoBonoInput = document.getElementById('codigo-bono');
    
    // Event listener para código de bono
    if (codigoBonoInput) {
        codigoBonoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                cargarBono();
            }
        });
    }
});

/**
 * Cargar grupos de etiquetas desde el JSON generado
 */
async function cargarGruposEtiquetas() {
    // Si ya está en cache, retornar
    if (gruposEtiquetasCache) {
        return gruposEtiquetasCache;
    }
    
    try {
        // Si hay un bono activo, cargar etiquetas de todos los archivos del bono
        if (window.bonoActual && window.bonoActual.nombre) {
            const response = await fetch(`/api/etiquetas/grupos_bono/${encodeURIComponent(window.bonoActual.nombre)}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    gruposEtiquetasCache = data.grupos || [];
                    console.log(`✅ Etiquetas cargadas del bono (${data.archivos_procesados} archivos):`, gruposEtiquetasCache.length);
                    return gruposEtiquetasCache;
                }
            }
        } else {
            // Fallback: cargar desde el JSON único (para compatibilidad)
            const response = await fetch('/api/etiquetas/grupos_json');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    gruposEtiquetasCache = data.grupos || [];
                    console.log('✅ Etiquetas cargadas:', gruposEtiquetasCache.length);
                    return gruposEtiquetasCache;
                }
            } else {
                console.log('⚠️ No se encontró archivo de etiquetas');
            }
        }
    } catch (error) {
        console.log('⚠️ Error al cargar etiquetas:', error);
    }
    return [];
}

/**
 * Obtener número de etiqueta para un elemento específico
 */
function obtenerNumeroEtiqueta(codCable, elemento, gruposEtiquetas) {
    if (!gruposEtiquetas || gruposEtiquetas.length === 0) {
        return null;
    }
    
    // Buscar en los grupos de etiquetas
    const grupo = gruposEtiquetas.find(g => 
        g.cod_cable === codCable && g.elemento === elemento
    );
    
    return grupo ? grupo.numero_etiqueta : null;
}

/**
 * Mostrar bonos disponibles
 */
async function mostrarBonosDisponibles() {
    try {
        const response = await fetch('/api/bonos');
        const data = await response.json();
        
        if (data.success) {
            const bonosDisponibles = document.getElementById('bonos-disponibles');
            const bonosLista = document.getElementById('bonos-lista');
            
            const bonosActivos = Object.values(data.bonos).filter(b => b.estado === 'activo');
            
            if (bonosActivos.length === 0) {
                bonosLista.innerHTML = '<p style="color: #6c757d;">No hay bonos activos disponibles.</p>';
            } else {
                bonosLista.innerHTML = bonosActivos.map(bono => `
                    <div style="background: white; padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 4px solid #0d6efd; cursor: pointer; transition: all 0.2s;" 
                         onclick="document.getElementById('codigo-bono').value='${bono.nombre}'; cargarBono();"
                         onmouseover="this.style.background='#e7f1ff'"
                         onmouseout="this.style.background='white'">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 1.1em; color: #0d6efd;">${bono.nombre}</strong>
                                <div style="color: #6c757d; font-size: 0.9em; margin-top: 4px;">
                                    ${bono.num_cortes} cortes • ${bono.carros.length} carros
                                </div>
                            </div>
                            <div style="color: #28a745; font-weight: bold;">✓ Activo</div>
                        </div>
                    </div>
                `).join('');
            }
            
            bonosDisponibles.classList.remove('hidden');
        } else {
            mostrarMensaje('Error al cargar bonos disponibles', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('Error al cargar bonos disponibles', 'error');
    }
}

/**
 * Cargar progreso guardado del bono
 */
async function cargarProgresoDelBono(nombreBono) {
    try {
        const response = await fetch(`/api/bonos/${nombreBono}/progreso`);
        const data = await response.json();
        
        if (data.success && data.progreso) {
            // Guardar progreso completo para usar después
            window.progresoCompleto = data.progreso;
            
            if (Object.keys(data.progreso).length > 0) {
                console.log(`💾 Progreso cargado del bono`);
            }
        }
    } catch (error) {
        console.error('Error al cargar progreso:', error);
    }
}

/**
 * Cargar progreso solo para los terminales de la máquina actual
 */
async function cargarProgresoMaquina() {
    terminalesCompletados = [];
    
    if (window.progresoCompleto) {
        // Filtrar solo los terminales de esta máquina que estén completados
        for (const terminal of terminalesAsignados) {
            if (window.progresoCompleto[terminal] && window.progresoCompleto[terminal].estado === 'completado') {
                terminalesCompletados.push(terminal);
            }
        }
        
        if (terminalesCompletados.length > 0) {
            console.log(`💾 ${terminalesCompletados.length} terminales completados en esta máquina`);
        }
    }
}

/**
 * Cargar bono de trabajo V3
 */
async function cargarBono() {
    const codigoBono = document.getElementById('codigo-bono').value.trim();
    
    if (!codigoBono) {
        mostrarMensaje('Por favor, ingresa el código del bono', 'error');
        return;
    }
    
    // Ocultar lista de bonos si estaba visible
    document.getElementById('bonos-disponibles').classList.add('hidden');
    
    try {
        // Validar el bono
        const response = await fetch('/api/bonos/validar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ nombre_bono: codigoBono })
        });
        
        const data = await response.json();
        
        if (data.success) {
            bonoActual = data.bono;
            window.bonoActual = data.bono; // También en window para acceso global
            carrosDelBono = data.bono.carros; // Guardar carros del bono
            
            // Limpiar cache de etiquetas para recargar con el nuevo bono
            gruposEtiquetasCache = null;
            
            // Cargar progreso guardado
            await cargarProgresoDelBono(data.bono.nombre);
            
            // Mostrar información del bono
            document.getElementById('bono-nombre').textContent = data.bono.nombre;
            document.getElementById('bono-num-cortes').textContent = data.bono.num_cortes;
            
            // Mostrar lista de carros
            const listaCarros = document.getElementById('bono-carros-lista');
            listaCarros.innerHTML = data.bono.carros.map((carro, index) => `
                <div style="padding: 8px; background: #f8f9fa; border-radius: 6px; margin-bottom: 5px; border-left: 3px solid #0d6efd;">
                    <strong>Carro ${carro.carro}:</strong> ${carro.proyecto_nombre} (${carro.archivo_excel})
                </div>
            `).join('');
            
            document.getElementById('bono-info').classList.remove('hidden');
            document.getElementById('workspace-v3').classList.remove('hidden');
            
            // Cargar puestos disponibles
            await cargarPuestos();
            
            mostrarMensaje('Bono cargado correctamente. Selecciona un puesto de trabajo.', 'success');
        } else {
            mostrarMensaje(data.message || 'Bono no encontrado', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('Error al cargar el bono', 'error');
    }
}

/**
 * Cargar puestos disponibles
 */
async function cargarPuestos() {
    try {
        const response = await fetch('/api/puestos');
        const data = await response.json();
        
        // Obtener terminales que tienen datos en el bono actual
        let terminalesConDatos = [];
        try {
            const responseTerminales = await fetch(`/api/bonos/${encodeURIComponent(bonoActual.nombre)}/terminales-disponibles`);
            const dataTerminales = await responseTerminales.json();
            
            if (dataTerminales.success) {
                terminalesConDatos = dataTerminales.terminales || [];
            }
        } catch (error) {
            console.error('Error al obtener terminales disponibles:', error);
        }
        
        const puestosGrid = document.getElementById('puestos-grid');
        puestosGrid.innerHTML = '';
        
        if (data.success && data.puestos.length > 0) {
            data.puestos.filter(p => p.activo).forEach(puesto => {
                // Calcular progreso total del puesto (todas las máquinas)
                let totalTerminalesPuesto = 0;
                let completadosPuesto = 0;
                
                if (puesto.maquinas && puesto.maquinas.length > 0) {
                    puesto.maquinas.filter(m => m.activo).forEach(maquina => {
                        const todosTerminalesAsignados = maquina.terminales_asignados || [];
                        
                        // Filtrar solo terminales que tienen datos en el bono
                        const terminalesAsignados = terminalesConDatos.length > 0 
                            ? todosTerminalesAsignados.filter(t => terminalesConDatos.includes(t))
                            : todosTerminalesAsignados;
                        
                        totalTerminalesPuesto += terminalesAsignados.length;
                        
                        if (window.progresoCompleto) {
                            completadosPuesto += terminalesAsignados.filter(terminal => {
                                return window.progresoCompleto[terminal] && window.progresoCompleto[terminal].estado === 'completado';
                            }).length;
                        }
                    });
                }
                
                const todosCompletados = totalTerminalesPuesto > 0 && completadosPuesto === totalTerminalesPuesto;
                const porcentaje = totalTerminalesPuesto > 0 ? Math.round((completadosPuesto / totalTerminalesPuesto) * 100) : 0;
                
                const puestoCard = document.createElement('div');
                puestoCard.className = `puesto-card ${todosCompletados ? 'completada' : ''}`;
                puestoCard.innerHTML = `
                    ${todosCompletados ? '<div class="check-completado">✅</div>' : ''}
                    <h3>${puesto.nombre}</h3>
                    <p>${puesto.descripcion || 'Sin descripción'}</p>
                    <div class="maquinas-count">
                        ${puesto.maquinas?.length || 0} máquinas
                        ${totalTerminalesPuesto > 0 ? `<br><span style="font-size: 0.85em;">${completadosPuesto} / ${totalTerminalesPuesto} terminales</span>` : ''}
                        ${porcentaje > 0 ? `<div class="progreso-mini" style="margin-top: 8px;">
                            <div class="progreso-mini-bar" style="width: ${porcentaje}%; background: ${todosCompletados ? '#28a745' : '#0d6efd'}; height: 6px; border-radius: 3px; transition: width 0.3s;"></div>
                        </div>` : ''}
                    </div>
                `;
                
                puestoCard.addEventListener('click', () => seleccionarPuesto(puesto));
                puestosGrid.appendChild(puestoCard);
            });
        } else {
            puestosGrid.innerHTML = '<p class="no-data">No hay puestos de trabajo disponibles.</p>';
        }
    } catch (error) {
        console.error('Error al cargar puestos:', error);
        mostrarMensaje('Error al cargar puestos de trabajo', 'error');
    }
}

/**
 * Seleccionar puesto de trabajo
 */
async function seleccionarPuesto(puesto) {
    puestoSeleccionado = puesto;
    
    document.getElementById('puesto-seleccionado-nombre').textContent = puesto.nombre;
    document.getElementById('paso-puesto').classList.add('hidden');
    document.getElementById('paso-maquina').classList.remove('hidden');
    
    // Cargar máquinas del puesto
    await cargarMaquinas(puesto.id);
}

/**
 * Cargar máquinas del puesto seleccionado
 */
async function cargarMaquinas(puestoId) {
    const maquinasGrid = document.getElementById('maquinas-grid');
    maquinasGrid.innerHTML = '';
    
    // Obtener terminales que tienen datos en el bono actual
    let terminalesConDatos = [];
    try {
        const response = await fetch(`/api/bonos/${encodeURIComponent(bonoActual.nombre)}/terminales-disponibles`);
        const data = await response.json();
        
        if (data.success) {
            terminalesConDatos = data.terminales || [];
        }
    } catch (error) {
        console.error('Error al obtener terminales disponibles:', error);
    }
    
    if (puestoSeleccionado.maquinas && puestoSeleccionado.maquinas.length > 0) {
        puestoSeleccionado.maquinas.filter(m => m.activo).forEach(maquina => {
            // Verificar cuántos terminales están completados
            const todosTerminalesAsignados = maquina.terminales_asignados || [];
            
            // Filtrar solo terminales que tienen datos en el bono
            const terminalesAsignados = terminalesConDatos.length > 0 
                ? todosTerminalesAsignados.filter(t => terminalesConDatos.includes(t))
                : todosTerminalesAsignados;
            
            const totalTerminales = terminalesAsignados.length;
            let terminalesCompletadosCount = 0;
            
            if (window.progresoCompleto && totalTerminales > 0) {
                terminalesCompletadosCount = terminalesAsignados.filter(terminal => {
                    return window.progresoCompleto[terminal] && window.progresoCompleto[terminal].estado === 'completado';
                }).length;
            }
            
            const todosCompletados = totalTerminales > 0 && terminalesCompletadosCount === totalTerminales;
            const porcentaje = totalTerminales > 0 ? Math.round((terminalesCompletadosCount / totalTerminales) * 100) : 0;
            
            const maquinaCard = document.createElement('div');
            maquinaCard.className = `maquina-card ${todosCompletados ? 'completada' : ''}`;
            maquinaCard.innerHTML = `
                ${todosCompletados ? '<div class="check-completado">✅</div>' : ''}
                <h3>${maquina.nombre}</h3>
                <p><strong>Modelo:</strong> ${maquina.modelo || 'No especificado'}</p>
                <div class="terminales-count">
                    ${terminalesCompletadosCount} / ${totalTerminales} terminales completados
                    ${porcentaje > 0 ? `<div class="progreso-mini" style="margin-top: 8px;">
                        <div class="progreso-mini-bar" style="width: ${porcentaje}%; background: ${todosCompletados ? '#28a745' : '#0d6efd'}; height: 6px; border-radius: 3px; transition: width 0.3s;"></div>
                    </div>` : ''}
                </div>
            `;
            
            maquinaCard.addEventListener('click', () => seleccionarMaquina(maquina));
            maquinasGrid.appendChild(maquinaCard);
        });
    } else {
        maquinasGrid.innerHTML = '<p class="no-data">No hay máquinas disponibles en este puesto.</p>';
    }
}

/**
 * Seleccionar máquina
 */
async function seleccionarMaquina(maquina) {
    maquinaSeleccionada = maquina;
    
    // Obtener terminales que tienen datos en el bono
    let terminalesConDatos = [];
    try {
        const response = await fetch(`/api/bonos/${encodeURIComponent(bonoActual.nombre)}/terminales-disponibles`);
        const data = await response.json();
        
        if (data.success) {
            terminalesConDatos = data.terminales || [];
        }
    } catch (error) {
        console.error('Error al obtener terminales disponibles:', error);
    }
    
    // Filtrar terminales asignados que tienen datos en el bono
    const todosTerminalesAsignados = maquina.terminales_asignados || [];
    if (terminalesConDatos.length > 0) {
        terminalesAsignados = todosTerminalesAsignados.filter(t => terminalesConDatos.includes(t));
    } else {
        // Si no se pudo obtener los terminales con datos, usar todos los asignados
        terminalesAsignados = todosTerminalesAsignados;
    }
    
    // Cargar progreso solo para los terminales de esta máquina
    await cargarProgresoMaquina();
    
    document.getElementById('maquina-seleccionada-nombre').textContent = maquina.nombre;
    document.getElementById('ruta-puesto').textContent = puestoSeleccionado.nombre;
    document.getElementById('ruta-maquina').textContent = maquina.nombre;
    
    document.getElementById('paso-maquina').classList.add('hidden');
    document.getElementById('paso-trabajo').classList.remove('hidden');
    
    // Mostrar terminales asignados
    mostrarTerminalesAsignados();
    
    // Cargar área de trabajo V2
    await cargarAreaTrabajoV2();
}

/**
 * Mostrar terminales asignados a la máquina para selección - CON PROGRESO
 */
function mostrarTerminalesAsignados() {
    const container = document.getElementById('terminales-asignados');
    
    if (terminalesAsignados.length === 0) {
        container.innerHTML = '<p class="no-data">⚠️ Esta máquina no tiene terminales asignados. Ve al panel de administración para asignar terminales.</p>';
        return;
    }
    
    const completados = terminalesCompletados.length;
    const total = terminalesAsignados.length;
    const porcentaje = Math.round((completados / total) * 100);
    
    // Mensaje de progreso cargado
    const mensajeProgreso = completados > 0 ? 
        `<div style="background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 12px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            💾 <strong>Progreso restaurado:</strong> ${completados} terminal${completados > 1 ? 'es' : ''} ya completado${completados > 1 ? 's' : ''}
        </div>` : '';
    
    container.innerHTML = `
        <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            ${mensajeProgreso}
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3>📋 Terminales de ${maquinaSeleccionada.nombre}</h3>
                <div style="text-align: right;">
                    <div style="font-size: 1.5em; font-weight: bold; color: #0d6efd;">
                        ${completados} / ${total}
                    </div>
                    <div style="font-size: 0.9em; color: #6c757d;">completados</div>
                </div>
            </div>
            
            <div style="background: #e9ecef; border-radius: 10px; height: 30px; overflow: hidden; margin-bottom: 20px;">
                <div style="background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: ${porcentaje}%; transition: width 0.5s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    ${porcentaje}%
                </div>
            </div>
            
            <p class="instruccion">Selecciona el siguiente terminal para continuar:</p>
        </div>
        
        <div class="terminales-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px;">
            ${terminalesAsignados.map(terminal => {
                const completado = terminalesCompletados.includes(terminal);
                return `
                    <div class="terminal-seleccionable ${completado ? 'completado' : ''}" 
                         onclick="${completado ? '' : `seleccionarTerminalTrabajo('${terminal}')`}"
                         style="
                            background: ${completado ? '#d4edda' : '#fff'};
                            border: 2px solid ${completado ? '#28a745' : '#0d6efd'};
                            border-radius: 10px;
                            padding: 20px;
                            text-align: center;
                            cursor: ${completado ? 'not-allowed' : 'pointer'};
                            transition: all 0.3s ease;
                            ${completado ? 'opacity: 0.7;' : ''}
                         ">
                        <div style="font-size: 1.3em; font-weight: bold; color: ${completado ? '#155724' : '#0d6efd'}; margin-bottom: 10px;">
                            ${terminal}
                        </div>
                        <div style="font-size: 0.9em; color: ${completado ? '#155724' : '#6c757d'};">
                            ${completado ? '✅ Completado' : '⏳ Pendiente'}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Cargar el área de trabajo V3 (selección de terminal)
 */
async function cargarAreaTrabajoV2() {
    try {
        const areaTrabajoV2 = document.getElementById('area-trabajo');
        areaTrabajoV2.innerHTML = `
            <div class="v3-seleccion-terminal">
                <div class="header-seleccion">
                    <h3>🎯 Configuración de Trabajo</h3>
                    <div class="ruta-completa">
                        <span class="paso">📁 ${proyectoActual}</span> → 
                        <span class="paso">🏭 ${puestoSeleccionado.nombre}</span> → 
                        <span class="paso">🔧 ${maquinaSeleccionada.nombre}</span>
                    </div>
                </div>
                
                <div class="instruccion-principal">
                    <p>📍 <strong>Siguiente paso:</strong> Selecciona un terminal de la lista de arriba para comenzar el trabajo.</p>
                    <p>📊 Una vez seleccionado, el sistema analizará ese terminal y te mostrará los paquetes necesarios.</p>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error al cargar área de trabajo:', error);
    }
}

/**
 * Navegación - Volver a selección de puestos
 */
function volverAPuestos() {
    document.getElementById('paso-maquina').classList.add('hidden');
    document.getElementById('paso-puesto').classList.remove('hidden');
    puestoSeleccionado = null;
}

/**
 * Navegación - Cambiar máquina
 */
function cambiarMaquina() {
    document.getElementById('paso-trabajo').classList.add('hidden');
    document.getElementById('paso-maquina').classList.remove('hidden');
    maquinaSeleccionada = null;
    terminalesAsignados = [];
}

/**
 * Seleccionar terminal específico para trabajar - CON SISTEMA DE BONOS
 */
async function seleccionarTerminalTrabajo(terminal) {
    terminalActual = terminal;
    
    // Recargar progreso del bono antes de verificar carros completados
    await cargarProgresoDelBono(bonoActual.nombre);
    
    // Buscar el primer carro no completado
    carroActualIndex = 0;
    
    if (window.progresoCompleto && window.progresoCompleto[terminal]) {
        const carrosCompletados = window.progresoCompleto[terminal].carros_completados || [];
        
        console.log(`📊 Terminal ${terminal} - Carros completados:`, carrosCompletados);
        
        // Buscar el primer carro que no está completado
        for (let i = 0; i < carrosDelBono.length; i++) {
            const carro = carrosDelBono[i];
            if (!carrosCompletados.includes(carro.carro)) {
                carroActualIndex = i;
                console.log(`▶️ Continuando desde carro ${carro.carro} (índice ${i})`);
                break;
            }
        }
        
        // Si todos los carros están completados
        if (carroActualIndex === 0 && carrosCompletados.includes(carrosDelBono[0].carro)) {
            // Verificar si todos están realmente completados
            const todosCompletados = carrosDelBono.every(c => carrosCompletados.includes(c.carro));
            if (todosCompletados) {
                mostrarMensaje(`✅ Terminal ${terminal} ya completado en todos los carros`, 'success');
                return;
            }
        }
        
        if (carroActualIndex > 0) {
            mostrarMensaje(`Continuando desde carro ${carrosDelBono[carroActualIndex].carro}...`, 'info');
        }
    } else {
        console.log(`ℹ️ Terminal ${terminal} - Sin progreso previo, empezando desde carro 1`);
    }
    
    mostrarMensaje(`Preparando trabajo para terminal ${terminal}...`, 'info');
    
    // Cargar paquetes del primer carro no completado
    await cargarPaquetesDelCarro();
}

/**
 * Mostrar pantalla de paquetes para un terminal específico (igual que V2)
 */
async function mostrarPantallaPaquetesTerminal(terminal, grupos, elementosNecesarios) {
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    
    // Cargar grupos de etiquetas
    const gruposEtiquetas = await cargarGruposEtiquetas();
    
    // Extraer elementos únicos y agregarles números de etiqueta
    const elementosUnicos = [...new Set(elementosNecesarios)];
    const elementosConEtiquetas = elementosUnicos.map(elemento => {
        // Buscar el cod_cable correcto para este elemento en los grupos
        const grupoConElemento = grupos.find(g => g.elemento === elemento);
        const codCable = grupoConElemento ? grupoConElemento.cod_cable : '';
        const numeroEtiqueta = obtenerNumeroEtiqueta(codCable, elemento, gruposEtiquetas);
        return {
            elemento: elemento,
            numeroEtiqueta: numeroEtiqueta
        };
    });
    
    areaTrabajoV2.innerHTML = `
        <div class="pantalla-preparacion">
            <div class="header-preparacion">
                <h2>📦 Preparación - Terminal: <span class="terminal-destacado">${terminal}</span></h2>
                <div class="stats-preparacion">
                    <span class="stat">📊 ${grupos.length} grupos</span>
                    <span class="stat">📦 ${elementosUnicos.length} elementos</span>
                </div>
            </div>

            <div class="instruccion-recoger">
                <h3>🎯 Recoger los siguientes paquetes:</h3>
            </div>

            <div class="elementos-lista">
                ${elementosConEtiquetas.map(item => {
                    const etiquetaHtml = item.numeroEtiqueta 
                        ? `<span style="display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%); color: white; padding: 6px 12px; border-radius: 8px; font-weight: bold; font-size: 1em; margin-right: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🏷️ #${item.numeroEtiqueta}</span>`
                        : '';
                    return `
                    <div class="elemento-item" style="display: flex; align-items: center; gap: 10px;">
                        ${etiquetaHtml}
                        <span class="elemento-numero">${item.elemento}</span>
                    </div>
                `}).join('')}
            </div>

            <div class="resumen-grupos">
                <h3>📋 Resumen del trabajo:</h3>
                <div class="grupos-info">
                    <p><strong>Terminal:</strong> ${terminal}</p>
                    <p><strong>Total grupos:</strong> ${grupos.length}</p>
                    <p><strong>Elementos a recoger:</strong> ${elementosUnicos.length}</p>
                </div>
            </div>

            <div class="acciones-preparacion">
                <button class="btn-volver" onclick="volverATerminales()">
                    ← Cambiar Terminal
                </button>
                <button class="btn-continuar" onclick="tengoLosPaquetes('${terminal}')">
                    ✅ Tengo los Paquetes - Continuar
                </button>
            </div>
        </div>
    `;
    
    // Guardar datos para el trabajo
    window.datosTerminalActual = {
        terminal: terminal,
        grupos: grupos,
        elementosNecesarios: elementosUnicos
    };
}

/**
 * Usuario confirma que tiene los paquetes (igual que V2)
 */
function tengoLosPaquetes(terminal) {
    if (!window.datosTerminalActual) return;
    
    const { grupos } = window.datosTerminalActual;
    
    // Inicializar variables para trabajo por grupos
    window.gruposTerminalActual = grupos;
    window.grupoActualIndex = 0;
    window.terminalTrabajo = terminal;
    
    mostrarMensaje(`¡Perfecto! Iniciando trabajo con ${terminal}...`, 'success');
    
    setTimeout(() => {
        iniciarTrabajoConGrupos();
    }, 1000);
}

/**
 * Iniciar trabajo con grupos (procesar paquete por paquete)
 */
function iniciarTrabajoConGrupos() {
    if (!window.gruposTerminalActual || window.grupoActualIndex >= window.gruposTerminalActual.length) {
        mostrarMensaje(`¡Trabajo con ${window.terminalTrabajo} completado!`, 'success');
        setTimeout(() => {
            terminalCompletoV3();
        }, 2000);
        return;
    }
    
    const grupoActual = window.gruposTerminalActual[window.grupoActualIndex];
    
    // Mostrar interfaz de paquete con todos sus cables
    mostrarPaqueteConCables(window.terminalTrabajo, grupoActual, 
        window.grupoActualIndex + 1, window.gruposTerminalActual.length);
}

/**
 * Volver a la selección de terminales
 */
function volverATerminales() {
    // Limpiar datos temporales
    window.datosTerminalActual = null;
    window.gruposTerminalActual = null;
    window.terminalTrabajo = null;
    
    // Volver a mostrar la selección de terminales
    cargarAreaTrabajoV2();
}

/**
 * Iniciar trabajo con grupos (igual que V2)
 */
function iniciarTrabajoConGrupos() {
    if (!window.gruposTerminalActual || window.grupoActualIndex >= window.gruposTerminalActual.length) {
        mostrarMensaje(`¡Trabajo con ${window.terminalTrabajo} completado!`, 'success');
        setTimeout(() => {
            volverATerminales();
        }, 3000);
        return;
    }
    
    const grupoActual = window.gruposTerminalActual[window.grupoActualIndex];
    
    // Mostrar interfaz de paquete con todos sus cables
    mostrarPaqueteConCables(window.terminalTrabajo, grupoActual, 
        window.grupoActualIndex + 1, window.gruposTerminalActual.length);
}

/**
 * DEPRECADO: Función antigua, ahora se usa seleccionarTerminalTrabajo
 */
async function iniciarTrabajoV2() {
    if (terminalesAsignados.length === 0) {
        mostrarMensaje('No hay terminales asignados a esta máquina', 'error');
        return;
    }
    
    mostrarMensaje('Analizando terminales asignados...', 'info');
    
    try {
        // Buscar todos los terminales asignados
        const todosLosGrupos = [];
        const elementosNecesarios = new Set();
        
        for (const terminal of terminalesAsignados) {
            const response = await fetch('/api/buscar_terminal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ terminal: terminal })
            });
            
            const data = await response.json();
            
            if (data.success && data.grupos.length > 0) {
                todosLosGrupos.push({
                    terminal: terminal,
                    grupos: data.grupos
                });
                
                // Recopilar elementos únicos
                data.grupos.forEach(grupo => {
                    if (grupo.elemento) {
                        elementosNecesarios.add(grupo.elemento);
                    }
                    
                    // También extraer de las listas de cables
                    if (grupo.cables_lista) {
                        grupo.cables_lista.forEach(cable => {
                            if (cable['De Elemento']) {
                                elementosNecesarios.add(cable['De Elemento']);
                            }
                        });
                    }
                });
            }
        }
        
        if (todosLosGrupos.length === 0) {
            mostrarMensaje('No se encontraron datos para los terminales asignados', 'error');
            return;
        }
        
        // Mostrar pantalla de paquetes para V3
        mostrarPantallaPaquetesV3(todosLosGrupos, Array.from(elementosNecesarios));
        
    } catch (error) {
        console.error('Error al analizar terminales:', error);
        mostrarMensaje('Error al analizar terminales asignados', 'error');
    }
}

/**
 * Buscar elemento por número de etiqueta
 */
async function buscarPorNumeroEtiqueta() {
    const input = document.getElementById('input-numero-etiqueta');
    const numeroEtiqueta = input.value.trim();
    
    if (!numeroEtiqueta) {
        alert('⚠️ Por favor, ingresa un número de etiqueta');
        input.focus();
        return;
    }
    
    try {
        const response = await fetch('/api/etiquetas/buscar_por_numero', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_etiqueta: parseInt(numeroEtiqueta) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const grupo = data.grupo;
            
            // Mostrar mensaje de éxito
            const mensaje = `✅ Etiqueta #${numeroEtiqueta} encontrada:\n\n` +
                          `🔌 Elemento: ${grupo.elemento}\n` +
                          `📟 Cable: ${grupo.cod_cable}\n` +
                          `📏 Sección: ${grupo.seccion || 'N/A'}`;
            
            alert(mensaje);
            
            // Resaltar el elemento en la lista si existe
            resaltarElementoEnLista(grupo.elemento);
            
            // Limpiar input
            input.value = '';
            input.focus();
        } else {
            alert(`❌ ${data.message}`);
            input.focus();
        }
    } catch (error) {
        console.error('Error al buscar etiqueta:', error);
        alert('❌ Error al buscar etiqueta. Verifica la conexión.');
    }
}

/**
 * Resaltar elemento en la lista de elementos
 */
function resaltarElementoEnLista(elemento) {
    // Buscar el elemento en la grid
    const elementos = document.querySelectorAll('.elemento-paquete');
    elementos.forEach(el => {
        const codigo = el.querySelector('.elemento-codigo');
        if (codigo && codigo.textContent === elemento) {
            // Animación de resaltado
            el.style.animation = 'pulse 1s ease-in-out 3';
            el.style.background = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
            el.style.transform = 'scale(1.1)';
            
            // Scroll al elemento
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Restaurar después de 3 segundos
            setTimeout(() => {
                el.style.animation = '';
                el.style.background = '';
                el.style.transform = '';
            }, 3000);
        }
    });
}

/**
 * Mostrar pantalla de paquetes para V3 (múltiples terminales)
 */
async function mostrarPantallaPaquetesV3(todosLosGrupos, elementosNecesarios) {
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    
    // Cargar grupos de etiquetas
    const gruposEtiquetas = await cargarGruposEtiquetas();
    
    // Crear un mapa de elementos con sus números de etiqueta
    const elementosConEtiquetas = elementosNecesarios.map(elemento => {
        // Buscar el cod_cable correcto para este elemento en todosLosGrupos
        let codCable = '';
        for (const terminalData of todosLosGrupos) {
            const grupoConElemento = terminalData.grupos.find(g => g.elemento === elemento);
            if (grupoConElemento) {
                codCable = grupoConElemento.cod_cable;
                break;
            }
        }
        const numeroEtiqueta = obtenerNumeroEtiqueta(codCable, elemento, gruposEtiquetas);
        return {
            elemento: elemento,
            numeroEtiqueta: numeroEtiqueta
        };
    });
    
    // Contar total de terminales y grupos
    let totalGrupos = 0;
    todosLosGrupos.forEach(terminalData => {
        totalGrupos += terminalData.grupos.length;
    });
    
    areaTrabajoV2.innerHTML = `
        <div class="pantalla-paquetes-v3">
            <div class="header-paquetes">
                <h2>📦 Preparar Paquetes</h2>
                <div class="resumen-trabajo">
                    <span class="badge badge-info">${terminalesAsignados.length} terminales</span>
                    <span class="badge badge-warning">${totalGrupos} grupos</span>
                    <span class="badge badge-success">${elementosNecesarios.length} elementos</span>
                </div>
            </div>
            
            <div class="busqueda-rapida-etiquetas" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: white; margin: 0 0 15px 0; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5em;">🏷️</span>
                    <span>Búsqueda Rápida por Etiqueta</span>
                </h3>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="number" 
                           id="input-numero-etiqueta" 
                           placeholder="Ej: 3" 
                           min="1"
                           style="flex: 1; padding: 12px; font-size: 16px; border: none; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                           onkeypress="if(event.key==='Enter') buscarPorNumeroEtiqueta()">
                    <button onclick="buscarPorNumeroEtiqueta()" 
                            style="padding: 12px 24px; font-size: 16px; background: white; color: #667eea; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s;"
                            onmouseover="this.style.transform='scale(1.05)'"
                            onmouseout="this.style.transform='scale(1)'">
                        🔍 Buscar
                    </button>
                </div>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 0.9em;">
                    💡 Tip: Ingresa el número de la etiqueta física pegada en el paquete
                </p>
            </div>
            
            <div class="instruccion-paquetes">
                <h3>🎯 Paquetes a recoger (por etiqueta):</h3>
            </div>
            
            <div class="elementos-grid">
                ${elementosConEtiquetas.map(item => {
                    const etiquetaHtml = item.numeroEtiqueta 
                        ? `<span style="background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%); color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.95em; margin-right: 8px;">🏷️ #${item.numeroEtiqueta}</span>`
                        : '';
                    return `
                    <div class="elemento-paquete">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            ${etiquetaHtml}
                            <span class="elemento-codigo">${item.elemento}</span>
                        </div>
                        <button class="btn-check" onclick="marcarElemento(this, '${item.elemento}')">
                            ✓ Recogido
                        </button>
                    </div>
                `;
                }).join('')}
            </div>
            
            <div class="detalle-terminales">
                <h3>📋 Terminales a procesar:</h3>
                <div class="terminales-detalle">
                    ${todosLosGrupos.map(terminalData => `
                        <div class="terminal-detalle">
                            <h4>Terminal: ${terminalData.terminal}</h4>
                            <span class="grupos-count">${terminalData.grupos.length} grupos</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="acciones-paquetes">
                <button class="btn-secondary" onclick="volverASeleccion()">↩️ Volver</button>
                <button class="btn-primary" id="btn-continuar-trabajo" onclick="continuarTrabajoV3()" disabled>
                    🚀 Continuar Trabajo
                </button>
            </div>
        </div>
    `;
    
    // Guardar datos para el trabajo
    window.datosTrabajoV3 = {
        todosLosGrupos: todosLosGrupos,
        elementosNecesarios: elementosNecesarios,
        elementosRecogidos: new Set()
    };
}

/**
 * Marcar elemento como recogido
 */
function marcarElemento(button, elemento) {
    if (!window.datosTrabajoV3) return;
    
    const elementosRecogidos = window.datosTrabajoV3.elementosRecogidos;
    const elementoDiv = button.parentElement;
    
    if (elementosRecogidos.has(elemento)) {
        // Desmarcar
        elementosRecogidos.delete(elemento);
        elementoDiv.classList.remove('recogido');
        button.textContent = '✓ Recogido';
        button.classList.remove('btn-success');
        button.classList.add('btn-check');
    } else {
        // Marcar
        elementosRecogidos.add(elemento);
        elementoDiv.classList.add('recogido');
        button.textContent = '✅ Recogido';
        button.classList.remove('btn-check');
        button.classList.add('btn-success');
    }
    
    // Verificar si todos los elementos están recogidos
    const btnContinuar = document.getElementById('btn-continuar-trabajo');
    const todosRecogidos = window.datosTrabajoV3.elementosNecesarios.every(elem => 
        elementosRecogidos.has(elem)
    );
    
    btnContinuar.disabled = !todosRecogidos;
    if (todosRecogidos) {
        btnContinuar.classList.add('btn-pulse');
    } else {
        btnContinuar.classList.remove('btn-pulse');
    }
}

/**
 * Continuar con el trabajo (iniciar secuencia V2)
 */
function continuarTrabajoV3() {
    if (!window.datosTrabajoV3) return;
    
    const { todosLosGrupos } = window.datosTrabajoV3;
    
    // Inicializar variables globales para V2
    window.gruposTrabajoV3 = todosLosGrupos;
    window.terminalActualIndex = 0;
    window.grupoActualIndex = 0;
    
    mostrarMensaje('¡Todos los elementos recogidos! Iniciando trabajo...', 'success');
    
    // Iniciar trabajo con el primer terminal
    setTimeout(() => {
        iniciarSecuenciaTrabajoV3();
    }, 1000);
}

/**
 * Iniciar secuencia de trabajo V3 (procesamiento de terminales)
 */
function iniciarSecuenciaTrabajoV3() {
    if (!window.gruposTrabajoV3 || window.gruposTrabajoV3.length === 0) {
        mostrarMensaje('Trabajo completado. ¡Excelente!', 'success');
        setTimeout(() => {
            volverASeleccion();
        }, 3000);
        return;
    }
    
    const terminalActual = window.gruposTrabajoV3[window.terminalActualIndex];
    const grupoActual = terminalActual.grupos[window.grupoActualIndex];
    
    // Mostrar interfaz de trabajo (similar a V2)
    mostrarInterfazTrabajoV3(terminalActual.terminal, grupoActual, 
        window.grupoActualIndex + 1, terminalActual.grupos.length);
}

/**
 * Mostrar pantalla de trabajo igual que V2
 */
function mostrarPaqueteConCables(terminal, grupo, numeroGrupo, totalGrupos) {
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    
    // Preparar cables del grupo según su tipo
    const cablesDelPaquete = [];
    let tipoTerminal = '';
    let colorPrincipal = 'verde';
    
    // Detectar tipo y preparar cables
    if (grupo.cables_doble_terminal && grupo.cables_doble_terminal.length > 0) {
        tipoTerminal = 'AMBOS Terminales';
        colorPrincipal = 'rojo';
        grupo.cables_doble_terminal.forEach(cable => {
            cablesDelPaquete.push({ cable, color: 'rojo', tipo: 'AMBOS' });
        });
    } else if (grupo.cables_de_terminal && grupo.cables_de_terminal.length > 0) {
        tipoTerminal = 'DE Terminal';
        colorPrincipal = 'azul';
        grupo.cables_de_terminal.forEach(cable => {
            cablesDelPaquete.push({ cable, color: 'azul', tipo: 'DE' });
        });
    } else if (grupo.cables_para_terminal && grupo.cables_para_terminal.length > 0) {
        tipoTerminal = 'PARA Terminal';
        colorPrincipal = 'verde';
        grupo.cables_para_terminal.forEach(cable => {
            cablesDelPaquete.push({ cable, color: 'verde', tipo: 'PARA' });
        });
    } else if (grupo.cables_lista && grupo.cables_lista.length > 0) {
        tipoTerminal = 'Cable Normal';
        colorPrincipal = 'gris';
        grupo.cables_lista.forEach(cable => {
            cablesDelPaquete.push({ cable: cable['Cod. cable'] || 'N/A', color: 'gris', tipo: 'Normal' });
        });
    }
    
    // Si no hay cables, crear uno representativo
    if (cablesDelPaquete.length === 0) {
        cablesDelPaquete.push({ cable: grupo.cod_cable || 'N/A', color: 'verde', tipo: 'Grupo' });
        tipoTerminal = 'Grupo';
    }
    
    const tiempoTotal = grupo.num_terminales * 3;
    
    areaTrabajoV2.innerHTML = `
        <div class="caja-expandida-v2">
            <div class="header-paquete">
                <h2>⚡ TERMINAL: ${terminal}</h2>
                <div class="progreso-paquete">Paquete ${numeroGrupo} de ${totalGrupos}</div>
            </div>
            
            <div class="info-paquete">
                <div class="elemento-principal">
                    <span class="elemento-label">📦 Elemento:</span>
                    <span class="elemento-valor">${grupo.elemento}</span>
                </div>
                <div class="codigo-cable">
                    <span class="cable-label">🔌 Código Cable:</span>
                    <span class="cable-valor">${grupo.cod_cable}</span>
                </div>
            </div>
            
            <div class="seccion-terminales-filas">
                <h3>Tipo de Trabajo:</h3>
                <div class="tipo-terminal-info tipo-terminal-${colorPrincipal}">
                    <span class="tipo-terminal-label">${tipoTerminal}</span>
                    <span class="terminal-numero-label">${grupo.num_terminales} terminales</span>
                </div>
            </div>
            
            <div class="cables-tabla-v2">
                <h3>🔌 Cables del Paquete:</h3>
                <div class="cables-lista-paquete">
                    ${cablesDelPaquete.map(item => `
                        <div class="cable-item cable-${item.color}">
                            <span class="cable-icono">📍</span>
                            <span class="cable-nombre">${item.cable}</span>
                            <span class="cable-tipo-badge badge-${item.color}">${item.tipo}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <div class="timer-v2" id="timer-container" style="display: none;">
                <div class="timer-texto">Engastando terminales...</div>
                <div class="timer-barra-fondo">
                    <div class="timer-barra-progreso" id="timer-barra"></div>
                </div>
                <div class="timer-tiempo" id="timer-tiempo">${tiempoTotal}s</div>
                <div class="timer-instruccion" id="timer-instruccion" style="display: none;">
                    <strong>✅ Completado - Pulsar ENTER para siguiente paquete</strong>
                </div>
            </div>
            
            <div class="controles-paquete">
                <button class="btn-control btn-iniciar" onclick="iniciarProcesoPaquete()" id="btnIniciarPaquete">
                    ▶️ Pulsar ENTER para Iniciar
                </button>
            </div>
        </div>
    `;
    
    // Guardar datos del paquete actual
    window.paqueteActual = { terminal, grupo, numeroGrupo, totalGrupos, tiempoTotal };
    
    // Configurar Enter para iniciar automáticamente
    configurarEnterParaIniciarPaquete();
}

/**
 * Configurar Enter para iniciar el paquete
 */
function configurarEnterParaIniciarPaquete() {
    // Remover listeners anteriores
    document.removeEventListener('keydown', manejarEnterIniciarPaquete);
    document.removeEventListener('keydown', manejarEnterPaquete);
    
    // Añadir listener para iniciar
    document.addEventListener('keydown', manejarEnterIniciarPaquete);
}

/**
 * Manejar Enter para iniciar el paquete
 */
function manejarEnterIniciarPaquete(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const btnIniciar = document.getElementById('btnIniciarPaquete');
        if (btnIniciar && btnIniciar.style.display !== 'none') {
            iniciarProcesoPaquete();
        }
    }
}

/**
 * Generar filas de cables para el nuevo formato V2
 */
function generarFilasCablesV2(cables) {
    const contenedor = document.getElementById('cablesFilas');
    if (!contenedor) return;
    
    contenedor.innerHTML = cables.map((cable, index) => `
        <div class="cable-fila cable-${cable.color || 'gris'} ${index === 0 ? 'fila-activa' : 'fila-bloqueada'}" 
             data-index="${index}" 
             onclick="${index === 0 ? 'procesarFilaActual()' : ''}">
            <div class="fila-contenido">
                <div class="cable-numero">${cable.nombre || cable.cable || `Cable ${index + 1}`}</div>
                <div class="cable-info">
                    <div class="elemento-badge">📦 ${cable.elemento || 'Elemento'}</div>
                    <div class="tipo-badge">${cable.tipo_descripcion || 'Cable'}</div>
                    <div class="datos-cable">${cable.seccion || 'N/A'} | ${cable.longitud || 'N/A'}</div>
                </div>
                <div class="fila-estado">
                    ${index === 0 ? '✓ Procesar' : '🔒 Bloqueado'}
                </div>
            </div>
        </div>
    `).join('');
    
    // Inicializar variables
    window.cablesFilasV2 = cables;
    window.filaActualIndex = 0;
}

/**
 * Inicializar procesamiento fila por fila
 */
function inicializarProcesamientoFilasPorFila() {
    window.filaActualIndex = 0;
    window.procesandoFila = false;
    configurarEnterListener();
}

/**
 * Procesar la fila actual cuando se hace clic
 */
function procesarFilaActual() {
    if (window.procesandoFila) return;
    
    const filas = document.querySelectorAll('.cable-fila');
    const filaActual = filas[window.filaActualIndex];
    
    if (!filaActual || !filaActual.classList.contains('fila-activa')) return;
    
    window.procesandoFila = true;
    
    // Iniciar timer para esta fila
    iniciarTimerFilaV2();
}

/**
 * Iniciar timer para una fila individual
 */
function iniciarTimerFilaV2() {
    const timerContainer = document.getElementById('timerInstruccion');
    const timerTexto = document.getElementById('timerTexto');
    
    if (!timerContainer || !timerTexto) return;
    
    timerContainer.style.display = 'block';
    
    let segundos = 3;
    timerTexto.textContent = segundos;
    
    const interval = setInterval(() => {
        segundos--;
        timerTexto.textContent = segundos;
        
        if (segundos <= 0) {
            clearInterval(interval);
            mostrarInstruccionEnter();
        }
    }, 1000);
}

/**
 * Mostrar instrucción para presionar Enter
 */
function mostrarInstruccionEnter() {
    const timerContainer = document.getElementById('timerInstruccion');
    if (timerContainer) {
        timerContainer.innerHTML = `
            <div class="timer-texto">Terminal engastado correctamente ✅</div>
            <div style="margin-top: 10px; font-weight: bold; color: #495057; animation: pulse 1s infinite;">
                Pulsar ENTER para continuar
            </div>
        `;
    }
}

/**
 * Configurar listener para tecla Enter
 */
function configurarEnterListener() {
    // Remover listener anterior si existe
    document.removeEventListener('keydown', manejarEnterV2);
    // Añadir nuevo listener
    document.addEventListener('keydown', manejarEnterV2);
}

/**
 * Manejar presión de tecla Enter
 */
function manejarEnterV2(event) {
    if (event.key === 'Enter' && window.procesandoFila) {
        event.preventDefault();
        continuarSiguienteFila();
    }
}

/**
 * Continuar con la siguiente fila
 */
function continuarSiguienteFila() {
    const filas = document.querySelectorAll('.cable-fila');
    
    // Marcar fila actual como completada
    if (filas[window.filaActualIndex]) {
        const filaActual = filas[window.filaActualIndex];
        filaActual.classList.remove('fila-activa');
        filaActual.classList.add('fila-completada');
        filaActual.querySelector('.fila-estado').textContent = '✅ Completado';
        filaActual.onclick = null;
    }
    
    // Avanzar al siguiente
    window.filaActualIndex++;
    window.procesandoFila = false;
    
    // Ocultar timer
    const timerContainer = document.getElementById('timerInstruccion');
    if (timerContainer) {
        timerContainer.style.display = 'none';
    }
    
    if (window.filaActualIndex < filas.length) {
        // Activar siguiente fila
        const siguienteFila = filas[window.filaActualIndex];
        siguienteFila.classList.remove('fila-bloqueada');
        siguienteFila.classList.add('fila-activa');
        siguienteFila.querySelector('.fila-estado').textContent = '✓ Procesar';
        siguienteFila.onclick = procesarFilaActual;
    } else {
        // Todas las filas completadas
        todasFilasCompletadas();
    }
}

/**
 * Iniciar proceso de engastado del paquete
 */
function iniciarProcesoPaquete() {
    if (!window.paqueteActual) return;
    
    // Remover listener de inicio
    document.removeEventListener('keydown', manejarEnterIniciarPaquete);
    
    const btnIniciar = document.getElementById('btnIniciarPaquete');
    const timerContainer = document.getElementById('timer-container');
    
    btnIniciar.style.display = 'none';
    timerContainer.style.display = 'block';
    
    // Iniciar timer
    iniciarTimerPaquete();
}

/**
 * Timer para el paquete completo
 */
function iniciarTimerPaquete() {
    const { tiempoTotal } = window.paqueteActual;
    const timerTiempo = document.getElementById('timer-tiempo');
    const timerBarra = document.getElementById('timer-barra');
    const timerInstruccion = document.getElementById('timer-instruccion');
    
    let segundosRestantes = tiempoTotal;
    timerTiempo.textContent = `${segundosRestantes}s`;
    
    const interval = setInterval(() => {
        segundosRestantes--;
        timerTiempo.textContent = `${segundosRestantes}s`;
        
        const progreso = ((tiempoTotal - segundosRestantes) / tiempoTotal) * 100;
        timerBarra.style.width = `${progreso}%`;
        
        if (segundosRestantes <= 0) {
            clearInterval(interval);
            timerBarra.style.width = '100%';
            timerInstruccion.style.display = 'block';
            
            // Configurar Enter para continuar
            document.addEventListener('keydown', manejarEnterPaquete);
        }
    }, 1000);
}

/**
 * Manejar Enter para pasar al siguiente paquete
 */
function manejarEnterPaquete(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        document.removeEventListener('keydown', manejarEnterPaquete);
        
        // Pasar directamente al siguiente paquete
        siguientePaquete();
    }
}

/**
 * Pasar al siguiente paquete
 */
function siguientePaquete() {
    window.grupoActualIndex++;
    iniciarTrabajoConGrupos();
}

/**
 * Pausar paquete actual
 */
function pausarPaquete() {
    mostrarMensaje('Función de pausa en desarrollo', 'info');
}

/**
 * Regresar a la selección de terminal
 */
function regresarASeleccionTerminal() {
    // Limpiar listeners
    document.removeEventListener('keydown', manejarEnterPaquete);
    
    // Limpiar variables
    window.terminalTrabajo = null;
    window.gruposTerminalActual = null;
    window.grupoActualIndex = 0;
    
    // Volver a la selección
    volverATerminales();
}

/**
 * Mostrar interfaz de trabajo V3 (similar a V2)
 */
function mostrarInterfazTrabajoV3(terminal, grupo, numeroGrupo, totalGrupos) {
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    
    // El grupo tiene la estructura del excel_manager, necesitamos convertirlo a lista de cables
    let cables = [];
    
    // Combinar todos los cables del grupo
    if (grupo.cables_lista) cables = cables.concat(grupo.cables_lista);
    if (grupo.cables_de_terminal) cables = cables.concat(grupo.cables_de_terminal);
    if (grupo.cables_para_terminal) cables = cables.concat(grupo.cables_para_terminal);
    if (grupo.cables_doble_terminal) cables = cables.concat(grupo.cables_doble_terminal);
    
    // Si no hay cables en las listas, crear un cable representativo
    if (cables.length === 0) {
        cables = [{
            'Caja': grupo.cod_cable || 'N/A',
            'De Elemento': grupo.elemento || 'N/A',
            'Posición': 'N/A',
            'Cable': grupo.descripcion || 'N/A',
            'Terminales': grupo.num_terminales || 1
        }];
    }
    
    areaTrabajoV2.innerHTML = `
        <div class="interfaz-trabajo-v3">
            <div class="header-trabajo">
                <h2>⚡ Trabajando: ${terminal}</h2>
                <div class="info-grupo">
                    <strong>Elemento:</strong> ${grupo.elemento || 'N/A'} | 
                    <strong>Código:</strong> ${grupo.cod_cable || 'N/A'} | 
                    <strong>Terminales:</strong> ${grupo.num_terminales || 1}
                </div>
                <div class="progreso-trabajo">
                    <span>Grupo ${numeroGrupo} de ${totalGrupos}</span>
                    <div class="barra-progreso">
                        <div class="progreso" style="width: ${(numeroGrupo/totalGrupos)*100}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="tabla-trabajo">
                <table class="tabla-ensamblaje">
                    <thead>
                        <tr>
                            <th>Código Cable</th>
                            <th>Elemento</th>
                            <th>Descripción</th>
                            <th>Sección</th>
                            <th>Longitud</th>
                            <th>Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${cables.map((cable, index) => `
                            <tr class="fila-trabajo ${index === 0 ? 'fila-activa' : ''}">
                                <td class="caja-numero">${cable['Cod. cable'] || grupo.cod_cable || 'N/A'}</td>
                                <td class="elemento">${cable['De Elemento'] || grupo.elemento || 'N/A'}</td>
                                <td class="cable">${cable['Descripción Cable'] || grupo.descripcion || 'N/A'}</td>
                                <td class="seccion">${cable['Sección'] || grupo.seccion || 'N/A'}</td>
                                <td class="longitud">${cable['Longitud'] || grupo.longitud || 'N/A'}</td>
                                <td>
                                    <button class="btn-accion" onclick="completarPaso(${index})" 
                                            ${index === 0 ? '' : 'disabled'}>
                                        ✓ Completar
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <div class="acciones-trabajo">
                <button class="btn-secondary" onclick="pausarTrabajo()">⏸️ Pausar</button>
                <button class="btn-warning" onclick="saltarGrupo()">⏭️ Saltar Grupo</button>
                <button class="btn-info" onclick="verDetalleGrupo()">📋 Ver Detalle</button>
            </div>
        </div>
    `;
    
    // Inicializar variables del grupo actual
    window.grupoActualV3 = cables;
    window.pasoActualV3 = 0;
    window.infoGrupoActual = grupo;
}

/**
 * Completar paso del trabajo
 */
function completarPaso(index) {
    if (index !== window.pasoActualV3) return;
    
    // Marcar paso actual como completado
    const filaActual = document.querySelector('.fila-activa');
    if (filaActual) {
        filaActual.classList.remove('fila-activa');
        filaActual.classList.add('fila-completada');
    }
    
    window.pasoActualV3++;
    
    // Verificar si hay más pasos
    if (window.pasoActualV3 < window.grupoActualV3.length) {
        // Activar siguiente paso
        const filasTabla = document.querySelectorAll('.fila-trabajo');
        if (filasTabla[window.pasoActualV3]) {
            filasTabla[window.pasoActualV3].classList.add('fila-activa');
            // Habilitar botón del siguiente paso
            const btnSiguiente = filasTabla[window.pasoActualV3].querySelector('.btn-accion');
            if (btnSiguiente) {
                btnSiguiente.disabled = false;
            }
        }
    } else {
        // Grupo completado, pasar al siguiente
        setTimeout(() => {
            siguienteGrupoV3();
        }, 1000);
    }
}

/**
 * Procesar fila actual (igual que V2)
 */
function procesarFilaActual() {
    const filaIndex = window.cabeActualIndex || 0;
    const tiempoTotal = window.grupoTrabajoActual.num_terminales * 3;
    
    // Mostrar timer
    const timerContainer = document.getElementById('timer-container');
    timerContainer.style.display = 'block';
    
    // Deshabilitar click en todas las filas
    const todasFilas = document.querySelectorAll('.cable-fila');
    todasFilas.forEach(fila => {
        fila.style.pointerEvents = 'none';
    });
    
    // Iniciar timer como en V2
    iniciarTimerV2(tiempoTotal);
}

/**
 * Procesar cable V2 con timer (compatibilidad)
 */
function procesarCableV2() {
    procesarFilaActual();
}

/**
 * Iniciar timer igual que en V2
 */
function iniciarTimerV2(tiempoTotal) {
    let tiempoRestante = tiempoTotal;
    const barra = document.getElementById('timer-barra');
    const textoTiempo = document.getElementById('timer-tiempo');
    const instruccion = document.getElementById('timer-instruccion');
    
    window.timerInterval = setInterval(() => {
        tiempoRestante--;
        
        // Actualizar barra de progreso
        const progreso = ((tiempoTotal - tiempoRestante) / tiempoTotal) * 100;
        barra.style.width = progreso + '%';
        
        // Actualizar texto
        textoTiempo.textContent = tiempoRestante + 's';
        
        // Verificar si terminamos
        if (tiempoRestante <= 0) {
            clearInterval(window.timerInterval);
            
            // Mostrar "Pulsar ENTER"
            textoTiempo.textContent = 'Completado!';
            instruccion.style.display = 'block';
            
            // Marcar fila como completada
            const filaActual = document.querySelector(`[data-index="${window.cabeActualIndex || 0}"]`);
            if (filaActual) {
                filaActual.classList.remove('fila-activa');
                filaActual.classList.add('fila-completada');
            }
            
            // Habilitar listener de Enter
            window.esperandoEnter = true;
            document.addEventListener('keydown', manejarEnter);
        }
    }, 1000);
}

/**
 * Manejar tecla Enter
 */
function manejarEnter(event) {
    if (event.key === 'Enter' && window.esperandoEnter) {
        event.preventDefault();
        window.esperandoEnter = false;
        document.removeEventListener('keydown', manejarEnter);
        
        // Ocultar timer
        document.getElementById('timer-container').style.display = 'none';
        document.getElementById('timer-instruccion').style.display = 'none';
        
        // Avanzar al siguiente
        window.cabeActualIndex = (window.cabeActualIndex || 0) + 1;
        
        if (window.cabeActualIndex < window.cablesActuales.length) {
            // Hay más cables en el grupo
            activarSiguienteFila();
        } else {
            // Grupo completado
            mostrarMensaje('Grupo completado! Pasando al siguiente...', 'success');
            setTimeout(() => {
                siguienteGrupoV2();
            }, 1500);
        }
    }
}

/**
 * Activar siguiente fila
 */
function activarSiguienteFila() {
    const siguienteFila = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
    if (siguienteFila) {
        siguienteFila.classList.remove('fila-bloqueada');
        siguienteFila.classList.add('fila-activa');
        siguienteFila.onclick = procesarFilaActual;
    }
    
    // Rehabilitar clicks
    const todasFilas = document.querySelectorAll('.cable-fila');
    todasFilas.forEach(fila => {
        fila.style.pointerEvents = 'auto';
    });
    
    // Reset timer barra
    document.getElementById('timer-barra').style.width = '0%';
}

/**
 * Continuar con el siguiente cable
 */
function continuarSiguienteCable() {
    // Resetear timer
    document.getElementById('timer-container').style.display = 'none';
    const barra = document.getElementById('timer-barra');
    barra.style.width = '0%';
    
    // Activar siguiente cable
    const siguienteCable = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
    if (siguienteCable) {
        siguienteCable.classList.add('cable-actual');
    }
    
    // Actualizar botón
    const btnProcesar = document.querySelector('.btn-procesar-grande');
    const cableActual = window.cablesActuales[window.cabeActualIndex];
    btnProcesar.disabled = false;
    btnProcesar.textContent = `✓ Procesar Cable ${cableActual.cable}`;
    
    // Actualizar navegación si existe
    actualizarNavegacion();
}

/**
 * Navegación anterior cable
 */
function anteriorCable() {
    if (window.cabeActualIndex > 0) {
        // Desmarcar actual
        const cableActual = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
        if (cableActual) cableActual.classList.remove('cable-actual');
        
        window.cabeActualIndex--;
        
        // Marcar nuevo actual
        const nuevoActual = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
        if (nuevoActual) nuevoActual.classList.add('cable-actual');
        
        actualizarNavegacion();
    }
}

/**
 * Navegación siguiente cable
 */
function siguienteCable() {
    if (window.cabeActualIndex < window.cablesActuales.length - 1) {
        // Desmarcar actual
        const cableActual = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
        if (cableActual) cableActual.classList.remove('cable-actual');
        
        window.cabeActualIndex++;
        
        // Marcar nuevo actual
        const nuevoActual = document.querySelector(`[data-index="${window.cabeActualIndex}"]`);
        if (nuevoActual) nuevoActual.classList.add('cable-actual');
        
        actualizarNavegacion();
    }
}

/**
 * Actualizar botones de navegación
 */
function actualizarNavegacion() {
    const btnAnterior = document.querySelector('.btn-nav[onclick="anteriorCable()"]');
    const btnSiguiente = document.querySelector('.btn-nav[onclick="siguienteCable()"]');
    const posicionTexto = document.querySelector('.posicion-actual');
    const btnProcesar = document.querySelector('.btn-procesar-grande');
    
    if (btnAnterior) btnAnterior.disabled = window.cabeActualIndex === 0;
    if (btnSiguiente) btnSiguiente.disabled = window.cabeActualIndex >= window.cablesActuales.length - 1;
    if (posicionTexto) posicionTexto.textContent = `${window.cabeActualIndex + 1} de ${window.cablesActuales.length}`;
    
    if (btnProcesar && window.cablesActuales[window.cabeActualIndex]) {
        btnProcesar.textContent = `✓ Procesar Cable ${window.cablesActuales[window.cabeActualIndex].cable}`;
    }
}

/**
 * Pausar trabajo V2
 */
function pausarTrabajoV2() {
    if (confirm('¿Quieres pausar el trabajo actual?')) {
        volverATerminales();
    }
}

/**
 * Saltar grupo V2 
 */
function saltarGrupoV2() {
    if (confirm('¿Estás seguro de que quieres saltar este grupo?')) {
        siguienteGrupoV2();
    }
}

/**
 * Siguiente grupo V2
 */
function siguienteGrupoV2() {
    window.grupoActualIndex++;
    window.cabeActualIndex = 0;
    
    if (window.grupoActualIndex < window.gruposTerminalActual.length) {
        // Continuar con siguiente grupo del mismo terminal
        iniciarTrabajoConGrupos();
    } else {
        // Terminal completado, verificar si hay más terminales en la máquina
        terminalCompletoV3();
    }
}

/**
 * Terminal completado - continuar flujo V3
 */
function terminalCompletoV3() {
    mostrarMensaje(`Terminal ${window.terminalTrabajo} completado!`, 'success');
    
    // Marcar terminal como completado
    const terminalesRestantes = terminalesAsignados.filter(t => !window.terminalesCompletados?.includes(t));
    
    if (!window.terminalesCompletados) {
        window.terminalesCompletados = [];
    }
    window.terminalesCompletados.push(window.terminalTrabajo);
    
    if (terminalesRestantes.length > 1) {
        // Hay más terminales en la máquina
        setTimeout(() => {
            mostrarMensaje('Selecciona el siguiente terminal de la máquina', 'info');
            volverATerminales();
        }, 2000);
    } else {
        // Máquina completada
        setTimeout(() => {
            maquinaCompletaV3();
        }, 2000);
    }
}

/**
 * Máquina completada - continuar flujo V3
 */
function maquinaCompletaV3() {
    mostrarMensaje(`Máquina ${maquinaSeleccionada.nombre} completada!`, 'success');
    
    // Verificar si hay más máquinas en el puesto
    const maquinasRestantes = puestoSeleccionado.maquinas.filter(m => m.activo && m.id !== maquinaSeleccionada.id);
    
    if (maquinasRestantes.length > 0) {
        // Hay más máquinas en el puesto
        setTimeout(() => {
            mostrarMensaje('Selecciona la siguiente máquina del puesto', 'info');
            cambiarMaquina();
        }, 2000);
    } else {
        // Puesto completado
        setTimeout(() => {
            puestoCompletoV3();
        }, 2000);
    }
}

/**
 * Puesto completado - flujo final V3
 */
function puestoCompletoV3() {
    mostrarMensaje(`Puesto ${puestoSeleccionado.nombre} completado! ¡Excelente trabajo!`, 'success');
    
    setTimeout(() => {
        if (confirm('¿Quieres seleccionar otro puesto para continuar trabajando?')) {
            volverAPuestos();
        } else {
            mostrarMensaje('Trabajo finalizado. ¡Buen trabajo!', 'success');
        }
    }, 3000);
}

/**
 * Pasar al siguiente grupo (compatibilidad V3)
 */
function siguienteGrupoV3() {
    window.grupoActualIndex++;
    
    // Si estamos trabajando con un solo terminal  
    if (window.gruposTerminalActual) {
        iniciarTrabajoConGrupos();
        return;
    }
    
    // Código original para múltiples terminales (mantener compatibilidad)
    if (window.gruposTrabajoV3) {
        const terminalActual = window.gruposTrabajoV3[window.terminalActualIndex];
        if (window.grupoActualIndex < terminalActual.grupos.length) {
            iniciarSecuenciaTrabajoV3();
        } else {
            window.terminalActualIndex++;
            window.grupoActualIndex = 0;
            
            if (window.terminalActualIndex < window.gruposTrabajoV3.length) {
                mostrarMensaje(`Terminal ${terminalActual.terminal} completado. Siguiente terminal...`, 'success');
                setTimeout(() => {
                    iniciarSecuenciaTrabajoV3();
                }, 2000);
            } else {
                mostrarMensaje('¡Trabajo completado! Todos los terminales procesados.', 'success');
                setTimeout(() => {
                    volverASeleccion();
                }, 3000);
            }
        }
    }
}

/**
 * Saltar grupo actual
 */
function saltarGrupo() {
    if (confirm('¿Estás seguro de que quieres saltar este grupo?')) {
        siguienteGrupoV3();
    }
}

/**
 * Pausar trabajo
 */
function pausarTrabajo() {
    if (confirm('¿Quieres pausar el trabajo actual?')) {
        volverASeleccion();
    }
}

/**
 * Ver detalle del grupo actual
 */
function verDetalleGrupo() {
    if (!window.infoGrupoActual) return;
    
    const grupo = window.infoGrupoActual;
    const detalleHtml = `
        <div class="modal-detalle">
            <div class="modal-content">
                <h3>📋 Detalle del Grupo</h3>
                <div class="grupo-info">
                    <p><strong>Elemento:</strong> ${grupo.elemento || 'N/A'}</p>
                    <p><strong>Código Cable:</strong> ${grupo.cod_cable || 'N/A'}</p>
                    <p><strong>Descripción:</strong> ${grupo.descripcion || 'N/A'}</p>
                    <p><strong>Sección:</strong> ${grupo.seccion || 'N/A'}</p>
                    <p><strong>Longitud:</strong> ${grupo.longitud || 'N/A'}</p>
                    <p><strong>Terminal DE:</strong> ${grupo.de_terminal || 'N/A'}</p>
                    <p><strong>Num. Terminales:</strong> ${grupo.num_terminales || 0}</p>
                </div>
                
                <div class="cables-detalle">
                    <h4>Cables en este grupo:</h4>
                    <p><strong>Cables normales:</strong> ${grupo.cables_lista?.length || 0}</p>
                    <p><strong>Cables DE terminal:</strong> ${grupo.cables_de_terminal?.length || 0}</p>
                    <p><strong>Cables PARA terminal:</strong> ${grupo.cables_para_terminal?.length || 0}</p>
                    <p><strong>Cables doble terminal:</strong> ${grupo.cables_doble_terminal?.length || 0}</p>
                </div>
                
                <button class="btn-primary" onclick="cerrarDetalle()">Cerrar</button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', detalleHtml);
}

/**
 * Cerrar modal de detalle
 */
function cerrarDetalle() {
    const modal = document.querySelector('.modal-detalle');
    if (modal) modal.remove();
}

/**
 * Volver a la selección de terminales
 */
function volverASeleccion() {
    // Limpiar datos temporales
    window.datosTrabajoV3 = null;
    window.gruposTrabajoV3 = null;
    window.terminalActualIndex = 0;
    window.grupoActualIndex = 0;
    window.pasoActualV3 = 0;
    window.infoGrupoActual = null;
    
    // Volver a cargar el área de trabajo inicial
    cargarAreaTrabajoV2();
}

/**
 * Mostrar mensaje (reutilizado de V1/V2)
 */
function mostrarMensaje(mensaje, tipo) {
    const elementoMensaje = document.getElementById('mensaje');
    elementoMensaje.textContent = mensaje;
    elementoMensaje.className = `mensaje ${tipo}`;
    elementoMensaje.classList.remove('hidden');
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        elementoMensaje.classList.add('hidden');
    }, 5000);
}

// ========================================
// NUEVAS FUNCIONES PARA TRABAJO CON BONOS
// ========================================

/**
 * Cargar paquetes del carro actual para el terminal actual
 */
async function cargarPaquetesDelCarro() {
    if (carroActualIndex >= carrosDelBono.length) {
        // Terminamos todos los carros para este terminal
        terminarTerminal();
        return;
    }
    
    const carro = carrosDelBono[carroActualIndex];
    
    try {
        // Obtener datos del archivo Excel
        const response = await fetch(`/api/datos_trabajo_v3?archivo=${encodeURIComponent(carro.archivo_excel)}&terminal=${encodeURIComponent(terminalActual)}&maquina=${maquinaSeleccionada.id}`);
        const data = await response.json();
        
        if (!data.success) {
            console.error('Error del servidor:', data.message || 'Sin mensaje');
            console.error('Datos completos:', data);
            mostrarMensaje(data.message || 'Error al cargar datos del carro', 'error');
            return;
        }
        
        if (!data.paquetes || data.paquetes.length === 0) {
            // Este carro no tiene datos para este terminal, pasar al siguiente
            carroActualIndex++;
            cargarPaquetesDelCarro();
            return;
        }
        
        paquetesActuales = data.paquetes;
        
        // Mostrar modal de confirmación de paquetes
        await mostrarModalPaquetes(carro);
        
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('Error al cargar paquetes', 'error');
    }
}

/**
 * Mostrar modal con paquetes a coger del carro
 */
async function mostrarModalPaquetes(carro) {
    // Cargar grupos de etiquetas
    const gruposEtiquetas = await cargarGruposEtiquetas();
    
    // Obtener el cod_cable del proyecto
    let codCableProyecto = '';
    if (paquetesActuales.length > 0) {
        codCableProyecto = paquetesActuales[0].cod_cable;
    }
    
    const modal = document.createElement('div');
    modal.id = 'modal-paquetes';
    modal.className = 'modal-overlay';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    // Calcular totales
    let totalCables = 0;
    let totalTerminales = 0;
    paquetesActuales.forEach(p => {
        totalCables += p.num_cables || 0;
        totalTerminales += p.num_terminales || 0;
    });
    
    modal.innerHTML = `
        <div class="modal-content-large" style="background: white; border-radius: 15px; padding: 30px; max-width: 700px; max-height: 90vh; overflow-y: auto;">
            <h2 style="color: #0d6efd; margin-bottom: 20px;">🚛 Carro ${carro.carro} - ${carro.proyecto_nombre}</h2>
            <div style="display: flex; gap: 20px; margin-bottom: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${terminalActual}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Terminal</div>
                </div>
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${paquetesActuales.length}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Paquetes</div>
                </div>
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${totalCables}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Cables</div>
                </div>
                <div style="flex: 1; text-align: center;">
                    <div style="font-size: 2em; font-weight: bold;">${totalTerminales}</div>
                    <div style="font-size: 0.9em; opacity: 0.9;">Terminales</div>
                </div>
            </div>
            
            <div class="paquetes-lista" style="margin: 20px 0;">
                <h3 style="margin-bottom: 15px;">📦 Paquetes a coger del Carro ${carro.carro}:</h3>
                ${paquetesActuales.map((paquete, index) => {
                    const numeroEtiqueta = obtenerNumeroEtiqueta(paquete.cod_cable, paquete.elemento, gruposEtiquetas);
                    const etiquetaHtml = numeroEtiqueta 
                        ? `<span style="display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%); color: white; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 1.1em; margin-right: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🏷️ #${numeroEtiqueta}</span>`
                        : '';
                    return `
                    <div style="background: #f8f9fa; border-left: 4px solid #0d6efd; border-radius: 8px; padding: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-size: 1.3em; font-weight: bold; color: #212529; margin-bottom: 5px; display: flex; align-items: center; gap: 10px;">
                                ${etiquetaHtml}
                                ${paquete.elemento}
                            </div>
                            <div style="color: #6c757d; font-size: 0.85em;">
                                Paquete ${index + 1}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.3em; font-weight: bold; color: #0d6efd;">${paquete.num_cables}</div>
                            <div style="font-size: 0.85em; color: #6c757d;">cables</div>
                        </div>
                    </div>
                `}).join('')}
            </div>
            
            <div style="margin-top: 30px; text-align: center; border-top: 2px solid #dee2e6; padding-top: 20px;">
                <p style="font-size: 1.3em; color: #0d6efd; margin-bottom: 20px;">
                    <strong>¿Tienes todos los paquetes del Carro ${carro.carro}?</strong>
                </p>
                <div style="display: flex; gap: 15px; justify-content: center;">
                    <button onclick="cerrarModalPaquetes()" class="btn-secondary" style="padding: 15px 30px; font-size: 1.1em; border: none; border-radius: 8px; cursor: pointer;">
                        ❌ Cancelar
                    </button>
                    <button onclick="confirmarPaquetesYComenzar()" class="btn-primary" style="padding: 15px 40px; font-size: 1.1em; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                        ✅ Tengo todos, comenzar
                    </button>
                </div>
                <p style="margin-top: 15px; color: #6c757d; font-size: 0.9em;">
                    💡 Presiona <strong>Enter</strong> para confirmar
                </p>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Permitir Enter para confirmar
    const confirmarConEnter = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.removeEventListener('keypress', confirmarConEnter);
            confirmarPaquetesYComenzar();
        }
    };
    document.addEventListener('keypress', confirmarConEnter);
}

/**
 * Obtener color de fondo para badge de cable
 */
function getColorCable(color) {
    const colores = {
        'Verde': '#28a745',
        'Azul': '#007bff',
        'Rojo': '#dc3545',
        'Gris': '#6c757d',
        'Amarillo': '#ffc107',
        'Naranja': '#fd7e14',
        'Blanco': '#e9ecef',
        'Negro': '#212529'
    };
    return colores[color] || '#6c757d';
}

/**
 * Cerrar modal de paquetes
 */
function cerrarModalPaquetes() {
    const modal = document.getElementById('modal-paquetes');
    if (modal) modal.remove();
}

/**
 * Confirmar paquetes y comenzar trabajo
 */
let paqueteActualIndex = 0;
let handlerEnterPaquete = null; // Handler global para evitar duplicados

function confirmarPaquetesYComenzar() {
    cerrarModalPaquetes();
    
    // Inicializar índice de paquetes
    paqueteActualIndex = 0;
    
    // Mostrar el primer paquete expandido
    mostrarPaqueteExpandido();
}

/**
 * Mostrar paquete expandido con detalles de cables
 */
async function mostrarPaqueteExpandido() {
    if (paqueteActualIndex >= paquetesActuales.length) {
        // Terminamos todos los paquetes de este carro
        paqueteCompletado();
        return;
    }
    
    const paquete = paquetesActuales[paqueteActualIndex];
    
    // Cargar grupos de etiquetas y obtener número
    const gruposEtiquetas = await cargarGruposEtiquetas();
    const numeroEtiqueta = obtenerNumeroEtiqueta(paquete.cod_cable, paquete.elemento, gruposEtiquetas);
    const etiquetaHtml = numeroEtiqueta 
        ? `<span style="display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%); color: white; padding: 10px 20px; border-radius: 10px; font-weight: bold; font-size: 1.2em; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🏷️ #${numeroEtiqueta}</span>`
        : '';
    
    const cablesDeTerminal = paquete.cables_de_terminal || [];
    const cablesParaTerminal = paquete.cables_para_terminal || [];
    const cablesAmbos = paquete.cables_doble_terminal || [];
    
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    areaTrabajoV2.innerHTML = `
        <div style="background: white; border-radius: 15px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 25px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <div style="font-size: 1.5em; font-weight: bold;">Terminal ${terminalActual}</div>
                    <div style="font-size: 1.1em; margin-top: 5px;">Paquete ${paqueteActualIndex + 1} de ${paquetesActuales.length}</div>
                </div>
                ${etiquetaHtml}
                <h2 style="color: #212529; margin-bottom: 10px;">${paquete.elemento}</h2>
                <div style="color: #6c757d; font-size: 1.1em;">Cable: ${paquete.cod_cable}</div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <div style="display: flex; gap: 30px; justify-content: center; text-align: center;">
                    <div>
                        <div style="font-size: 2em; font-weight: bold; color: #0d6efd;">${paquete.num_cables}</div>
                        <div style="color: #6c757d;">Total Cables</div>
                    </div>
                    <div>
                        <div style="font-size: 2em; font-weight: bold; color: #0d6efd;">${paquete.num_terminales}</div>
                        <div style="color: #6c757d;">Total Terminales</div>
                    </div>
                    <div>
                        <div style="font-size: 2em; font-weight: bold; color: #0d6efd;">${paquete.seccion || 'N/A'}</div>
                        <div style="color: #6c757d;">Sección</div>
                    </div>
                </div>
            </div>
            
            <div class="terminals-grid" style="display: grid; gap: 15px; margin-bottom: 30px;">
                <h3 style="margin-bottom: 10px;">Terminales a engastar:</h3>
                
                ${cablesDeTerminal.length > 0 ? `
                    <div class="terminal-group terminal-group-azul" style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-left: 5px solid #2196f3; padding: 15px; border-radius: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                            <span style="font-size: 1.5em;">📍</span>
                            <span style="font-weight: bold; color: #1976d2; font-size: 1.1em;">De Terminal</span>
                            <span style="background: #2196f3; color: white; padding: 4px 12px; border-radius: 12px; font-size: 1em; font-weight: bold; margin-left: auto;">
                                ${cablesDeTerminal.length}
                            </span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${cablesDeTerminal.map(cable => 
                                `<span class="cable-badge" style="background: #2196f3; color: white; padding: 8px 14px; border-radius: 8px; font-weight: bold; font-size: 1em;">${cable}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${cablesParaTerminal.length > 0 ? `
                    <div class="terminal-group terminal-group-verde" style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-left: 5px solid #4caf50; padding: 15px; border-radius: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                            <span style="font-size: 1.5em;">🎯</span>
                            <span style="font-weight: bold; color: #388e3c; font-size: 1.1em;">Para Terminal</span>
                            <span style="background: #4caf50; color: white; padding: 4px 12px; border-radius: 12px; font-size: 1em; font-weight: bold; margin-left: auto;">
                                ${cablesParaTerminal.length}
                            </span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${cablesParaTerminal.map(cable => 
                                `<span class="cable-badge" style="background: #4caf50; color: white; padding: 8px 14px; border-radius: 8px; font-weight: bold; font-size: 1em;">${cable}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${cablesAmbos.length > 0 ? `
                    <div class="terminal-group terminal-group-rojo" style="background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); border-left: 5px solid #f44336; padding: 15px; border-radius: 10px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                            <span style="font-size: 1.5em;">🔗</span>
                            <span style="font-weight: bold; color: #d32f2f; font-size: 1.1em;">Ambos Lados</span>
                            <span style="background: #f44336; color: white; padding: 4px 12px; border-radius: 12px; font-size: 1em; font-weight: bold; margin-left: auto;">
                                ${cablesAmbos.length}
                            </span>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${cablesAmbos.map(cable => 
                                `<span class="cable-badge" style="background: #f44336; color: white; padding: 8px 14px; border-radius: 8px; font-weight: bold; font-size: 1em;">${cable}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div style="text-align: center; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <p style="font-size: 1.2em; color: #0d6efd; margin-bottom: 15px; font-weight: bold;">
                    ${paqueteActualIndex === paquetesActuales.length - 1 ? 
                        '✅ Presiona ENTER para finalizar este carro' : 
                        'Presiona ENTER cuando termines este paquete'}
                </p>
                <div style="font-size: 0.9em; color: #6c757d;">
                    Paquete ${paqueteActualIndex + 1} de ${paquetesActuales.length}
                </div>
            </div>
        </div>
    `;
    
    // Remover handler anterior si existe
    if (handlerEnterPaquete) {
        document.removeEventListener('keypress', handlerEnterPaquete);
    }
    
    // Evento para pasar al siguiente paquete con Enter
    handlerEnterPaquete = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.removeEventListener('keypress', handlerEnterPaquete);
            handlerEnterPaquete = null;
            
            // Mostrar indicador de carga si es el último paquete
            if (paqueteActualIndex === paquetesActuales.length - 1) {
                const areaTrabajoV2 = document.getElementById('area-trabajo');
                areaTrabajoV2.innerHTML = `
                    <div style="background: white; border-radius: 15px; padding: 50px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                        <div style="font-size: 3em; margin-bottom: 20px;">⏳</div>
                        <h2 style="color: #0d6efd; margin-bottom: 15px;">Guardando progreso...</h2>
                        <div style="color: #6c757d;">Por favor espera un momento</div>
                    </div>
                `;
            }
            
            paqueteActualIndex++;
            mostrarPaqueteExpandido();
        }
    };
    document.addEventListener('keypress', handlerEnterPaquete);
    
    // Scroll automático al área de trabajo
    setTimeout(() => {
        const areaTrabajoV2 = document.getElementById('area-trabajo');
        if (areaTrabajoV2) {
            areaTrabajoV2.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 100);
}

/**
 * Paquete completado - continuar con siguiente carro o finalizar
 */
async function paqueteCompletado() {
    try {
        // Guardar progreso del carro actual inmediatamente
        const carroActual = carrosDelBono[carroActualIndex];
        
        // Recopilar terminales del proyecto para este carro
        const terminalesDelProyecto = new Set();
        const response = await fetch(`/api/datos_trabajo_v3?archivo=${encodeURIComponent(carroActual.archivo_excel)}&terminal=${encodeURIComponent(terminalActual)}&maquina=${maquinaSeleccionada.id}`);
        const data = await response.json();
        
        if (data.success && data.paquetes) {
            data.paquetes.forEach(paquete => {
                if (paquete.elemento) {
                    terminalesDelProyecto.add(paquete.elemento);
                }
            });
        }
        
        const listaTerminalesProyecto = Array.from(terminalesDelProyecto);
        
        // Guardar progreso de este carro
        await fetch(`/api/bonos/${bonoActual.nombre}/progreso`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                terminal: terminalActual,
                carro: carroActual.carro,
                terminales_proyecto: listaTerminalesProyecto
            })
        });
        
        console.log(`✅ Progreso guardado para carro ${carroActual.carro}`);
        
    } catch (error) {
        console.error('Error al guardar progreso del carro:', error);
    }
    
    // Avanzar al siguiente carro
    carroActualIndex++;
    
    if (carroActualIndex < carrosDelBono.length) {
        // Hay más carros, cargar paquetes del siguiente
        mostrarMensaje(`✅ Carro completado. Cargando siguiente carro...`, 'success');
        setTimeout(() => {
            cargarPaquetesDelCarro();
        }, 1500);
    } else {
        // Terminamos todos los carros de este terminal
        terminarTerminal();
    }
}

/**
 * Terminar trabajo del terminal actual
 */
async function terminarTerminal() {
    try {
        // Recopilar todos los terminales únicos del proyecto que se han trabajado
        const terminalesDelProyecto = new Set();
        
        // Recorrer todos los carros del bono
        for (let i = 0; i < carrosDelBono.length; i++) {
            const carro = carrosDelBono[i];
            
            // Obtener los paquetes de este carro para este terminal
            try {
                const response = await fetch(`/api/datos_trabajo_v3?archivo=${encodeURIComponent(carro.archivo_excel)}&terminal=${encodeURIComponent(terminalActual)}&maquina=${maquinaSeleccionada.id}`);
                const data = await response.json();
                
                if (data.success && data.paquetes) {
                    // Añadir todos los terminales únicos (elemento) de los paquetes
                    data.paquetes.forEach(paquete => {
                        if (paquete.elemento) {
                            terminalesDelProyecto.add(paquete.elemento);
                        }
                    });
                }
            } catch (error) {
                console.error(`Error obteniendo terminales del carro ${carro.carro}:`, error);
            }
        }
        
        // Convertir Set a Array
        const listaTerminalesProyecto = Array.from(terminalesDelProyecto);
        
        // Guardar progreso en el servidor para cada carro procesado
        for (let i = 0; i < carrosDelBono.length; i++) {
            const carro = carrosDelBono[i];
            await fetch(`/api/bonos/${bonoActual.nombre}/progreso`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    terminal: terminalActual,
                    carro: carro.carro,
                    terminales_proyecto: listaTerminalesProyecto
                })
            });
        }
        
        console.log('✅ Progreso guardado correctamente para todos los carros');
        console.log('📍 Terminales del proyecto:', listaTerminalesProyecto);
    } catch (error) {
        console.error('Error al guardar progreso:', error);
    }
    
    // Agregar terminal a completados solo si no está ya
    if (!terminalesCompletados.includes(terminalActual)) {
        terminalesCompletados.push(terminalActual);
    }
    
    // Actualizar visualización de terminales inmediatamente
    mostrarTerminalesAsignados();
    
    // Forzar un repaint del DOM antes de continuar
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Verificar si terminamos todos
    if (terminalesCompletados.length === terminalesAsignados.length) {
        mostrarMensaje('🎉 ¡Todos los terminales completados!', 'success');
        // Esperar un poco más para que se vea la actualización visual antes de mostrar el resumen
        setTimeout(() => {
            mostrarResumenFinal();
        }, 1000);
    } else {
        mostrarMensaje(`✅ Terminal ${terminalActual} completado. ${terminalesAsignados.length - terminalesCompletados.length} pendientes.`, 'success');
        // Volver al área de selección solo si no terminamos todos
        cargarAreaTrabajoV2();
    }
    
    terminalActual = null;
    carroActualIndex = 0;
}

/**
 * Mostrar resumen final
 */
async function mostrarResumenFinal() {
    // Recargar el progreso completo del bono para tener datos actualizados
    await cargarProgresoDelBono(bonoActual.nombre);
    
    // Obtener terminales con datos del bono
    let terminalesConDatos = [];
    try {
        const response = await fetch(`/api/bonos/${encodeURIComponent(bonoActual.nombre)}/terminales-disponibles`);
        const data = await response.json();
        if (data.success) {
            terminalesConDatos = data.terminales || [];
        }
    } catch (error) {
        console.error('Error al obtener terminales disponibles:', error);
    }
    
    // Contar terminales completados en TODO el bono (no solo esta máquina)
    let totalTerminalesCompletadosBono = 0;
    if (window.progresoCompleto && terminalesConDatos.length > 0) {
        totalTerminalesCompletadosBono = terminalesConDatos.filter(terminal => {
            return window.progresoCompleto[terminal] && window.progresoCompleto[terminal].estado === 'completado';
        }).length;
    }
    
    console.log(`📊 Progreso total del bono: ${totalTerminalesCompletadosBono}/${terminalesConDatos.length}`);
    
    // Verificar si TODO el bono está completo
    if (totalTerminalesCompletadosBono >= terminalesConDatos.length && terminalesConDatos.length > 0) {
        // ¡BONO COMPLETADO!
        mostrarResumenBonoCompleto(terminalesConDatos.length);
        return;
    }
    
    // Verificar si quedan máquinas pendientes en este puesto
    let terminalesPendientesEnPuesto = 0;
    if (puestoSeleccionado && puestoSeleccionado.maquinas) {
        puestoSeleccionado.maquinas.filter(m => m.activo).forEach(maquina => {
            const todosTerminalesAsignados = maquina.terminales_asignados || [];
            const terminalesAsignados = terminalesConDatos.length > 0 
                ? todosTerminalesAsignados.filter(t => terminalesConDatos.includes(t))
                : todosTerminalesAsignados;
            
            terminalesAsignados.forEach(terminal => {
                const estaCompletado = window.progresoCompleto && 
                                      window.progresoCompleto[terminal] && 
                                      window.progresoCompleto[terminal].estado === 'completado';
                if (!estaCompletado) {
                    terminalesPendientesEnPuesto++;
                }
            });
        });
    }
    
    // Decidir el siguiente paso y el mensaje
    let siguientePaso, textoBoton, iconoBoton;
    if (terminalesPendientesEnPuesto > 0) {
        siguientePaso = 'maquina';
        textoBoton = '🔧 Seleccionar otra máquina';
        iconoBoton = '🔧';
    } else {
        siguientePaso = 'puesto';
        textoBoton = '🏭 Seleccionar otro puesto';
        iconoBoton = '🏭';
    }
    
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    areaTrabajoV2.innerHTML = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 15px; text-align: center;">
            <div style="font-size: 4em; margin-bottom: 20px;">${iconoBoton}</div>
            <h2 style="font-size: 2.5em; margin-bottom: 20px;">¡Trabajo Completado!</h2>
            <p style="font-size: 1.3em; margin-bottom: 30px;">
                Has completado todos los terminales de <strong>${maquinaSeleccionada.nombre}</strong>
            </p>
            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-bottom: 30px;">
                <div style="font-size: 3em; font-weight: bold;">${terminalesCompletados.length}</div>
                <div style="font-size: 1.2em;">Terminales procesados en esta máquina</div>
            </div>
            ${terminalesPendientesEnPuesto > 0 ? `
                <p style="font-size: 1.1em; margin-bottom: 20px; background: rgba(255,255,255,0.15); padding: 15px; border-radius: 8px;">
                    ℹ️ Quedan <strong>${terminalesPendientesEnPuesto} terminales</strong> pendientes en otras máquinas de este puesto
                </p>
            ` : ''}
            <button onclick="continuarDespuesDeCompletarMaquina('${siguientePaso}')" class="btn-primary" style="padding: 15px 40px; font-size: 1.2em; background: white; color: #667eea; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                ${textoBoton}
            </button>
        </div>
    `;
}

/**
 * Continuar después de completar una máquina
 */
async function continuarDespuesDeCompletarMaquina(siguientePaso) {
    if (siguientePaso === 'maquina') {
        // Recargar progreso antes de mostrar máquinas
        await cargarProgresoMaquina();
        
        // Forzar repaint del DOM
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Volver a selección de máquinas
        document.getElementById('paso-trabajo').classList.add('hidden');
        document.getElementById('paso-maquina').classList.remove('hidden');
        await cargarMaquinas(puestoSeleccionado.id);
        
        // Esperar para que se vea la actualización antes de permitir interacción
        await new Promise(resolve => setTimeout(resolve, 800));
        
    } else if (siguientePaso === 'puesto') {
        // Recargar todo el progreso antes de mostrar puestos
        await cargarProgresoDelBono(bonoActual.nombre);
        
        // Forzar repaint del DOM
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Volver a selección de puestos
        document.getElementById('paso-trabajo').classList.add('hidden');
        document.getElementById('paso-maquina').classList.add('hidden');
        document.getElementById('paso-puesto').classList.remove('hidden');
        await cargarPuestos();
        
        // Esperar para que se vea la actualización antes de permitir interacción
        await new Promise(resolve => setTimeout(resolve, 800));
        
    } else {
        // Volver al inicio
        window.location.href = '/';
    }
}

/**
 * Mostrar resumen cuando el BONO COMPLETO está terminado
 */
function mostrarResumenBonoCompleto(totalTerminales) {
    const areaTrabajoV2 = document.getElementById('area-trabajo');
    areaTrabajoV2.innerHTML = `
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 50px; border-radius: 15px; text-align: center;">
            <div style="font-size: 5em; margin-bottom: 20px;">🎊🎉🎊</div>
            <h2 style="font-size: 3em; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">¡BONO COMPLETADO!</h2>
            <p style="font-size: 1.5em; margin-bottom: 30px;">
                Has terminado <strong>TODOS</strong> los trabajos del bono <strong>${bonoActual.nombre}</strong>
            </p>
            <div style="background: rgba(255,255,255,0.25); padding: 30px; border-radius: 15px; margin-bottom: 30px;">
                <div style="font-size: 4em; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">${totalTerminales}</div>
                <div style="font-size: 1.3em;">Terminales procesados en total</div>
            </div>
            <p style="font-size: 1.2em; margin-bottom: 30px; font-style: italic;">
                ¡Excelente trabajo! 🏆
            </p>
            <button onclick="window.location.href='/'" class="btn-primary" style="padding: 20px 50px; font-size: 1.3em; background: white; color: #28a745; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                🏠 Volver al Inicio
            </button>
        </div>
    `;
}