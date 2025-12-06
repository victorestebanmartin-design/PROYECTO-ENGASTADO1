/**
 * Sistema de Registro de Órdenes de Producción
 */

let todasLasOrdenes = []; // Array global para filtrado

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    cargarOrdenes();
    
    // Event listener para formulario de escaneo
    const formEscaneo = document.getElementById('form-escanear-orden');
    if (formEscaneo) {
        formEscaneo.addEventListener('submit', procesarCodigoBarras);
    }
    
    // Event listener para formulario manual
    const formOrden = document.getElementById('form-nueva-orden');
    if (formOrden) {
        formOrden.addEventListener('submit', registrarOrden);
    }
    
    // Validación en tiempo real del código de corte
    const inputCodigoCorte = document.getElementById('codigo-corte');
    if (inputCodigoCorte) {
        inputCodigoCorte.addEventListener('blur', validarCodigoCorte);
    }
    
    // Auto-focus en el campo de código de barras
    const inputCodigo = document.getElementById('codigo-barras-orden');
    if (inputCodigo) {
        inputCodigo.focus();
    }
});

/**
 * Validar código de corte en tiempo real
 */
async function validarCodigoCorte(e) {
    const codigoCorte = e.target.value.trim().toUpperCase();
    const validationDiv = document.getElementById('validation-corte');
    
    if (!codigoCorte) {
        validationDiv.textContent = '';
        validationDiv.className = '';
        return;
    }
    
    try {
        const response = await fetch('/api/validar_codigo_corte', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ codigo_corte: codigoCorte })
        });
        
        const data = await response.json();
        
        if (data.success) {
            validationDiv.textContent = data.mensaje;
            validationDiv.className = data.tiene_excel ? 'validation-success' : 'validation-warning';
        } else {
            validationDiv.textContent = '';
            validationDiv.className = '';
        }
    } catch (error) {
        console.error('Error validando código:', error);
        validationDiv.textContent = '';
        validationDiv.className = '';
    }
}

/**
 * Procesar código de barras
 * Formato: CODIGO_CORTE-ORDEN-CANTIDAD-FECHA
 * Ejemplo: CORTE001-OP2024-50-20251215
 */
async function procesarCodigoBarras(e) {
    e.preventDefault();
    
    const codigoCompleto = document.getElementById('codigo-barras-orden').value.trim();
    
    if (!codigoCompleto) {
        mostrarMensaje('mensaje-escaneo', 'Por favor escanea un código de barras', 'error');
        return;
    }
    
    // Separar por guiones
    const partes = codigoCompleto.split('-');
    
    if (partes.length !== 4) {
        mostrarMensaje('mensaje-escaneo', 
            `Formato incorrecto. Esperado: CODIGO-ORDEN-CANTIDAD-FECHA. Recibido: ${partes.length} partes`, 
            'error'
        );
        return;
    }
    
    const [codigoCorte, numeroOrden, cantidadStr, fechaStr] = partes;
    
    // Validar cantidad
    const cantidad = parseInt(cantidadStr);
    if (isNaN(cantidad) || cantidad <= 0) {
        mostrarMensaje('mensaje-escaneo', `Cantidad inválida: ${cantidadStr}`, 'error');
        return;
    }
    
    // Validar y formatear fecha (YYYYMMDD -> YYYY-MM-DD)
    if (fechaStr.length !== 8 || isNaN(fechaStr)) {
        mostrarMensaje('mensaje-escaneo', `Fecha inválida: ${fechaStr}. Debe ser YYYYMMDD`, 'error');
        return;
    }
    
    const year = fechaStr.substring(0, 4);
    const month = fechaStr.substring(4, 6);
    const day = fechaStr.substring(6, 8);
    const fechaEntrega = `${year}-${month}-${day}`;
    
    // Validar que sea una fecha válida
    const fecha = new Date(fechaEntrega);
    if (isNaN(fecha.getTime())) {
        mostrarMensaje('mensaje-escaneo', `Fecha inválida: ${fechaEntrega}`, 'error');
        return;
    }
    
    // Calcular prioridad automática basada en la fecha
    const hoy = new Date();
    const diasRestantes = Math.ceil((fecha - hoy) / (1000 * 60 * 60 * 24));
    let prioridad = 'media';
    
    if (diasRestantes < 0) {
        prioridad = 'urgente'; // Fecha pasada
    } else if (diasRestantes <= 3) {
        prioridad = 'urgente';
    } else if (diasRestantes <= 7) {
        prioridad = 'alta';
    } else if (diasRestantes <= 14) {
        prioridad = 'media';
    } else {
        prioridad = 'baja';
    }
    
    // Crear la orden automáticamente
    try {
        const response = await fetch('/api/ordenes/crear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo_corte: codigoCorte,
                numero: numeroOrden,
                proyecto: '', // Se puede agregar después manualmente
                descripcion: `Orden escaneada: ${codigoCompleto}`,
                cantidad: cantidad,
                fecha_entrega: fechaEntrega,
                prioridad: prioridad
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let mensaje = `✅ Orden registrada: ${numeroOrden} - ${cantidad} cables - Entrega: ${fechaEntrega} - Prioridad: ${prioridad}`;
            
            // Agregar información sobre asociación de Excel
            if (data.archivo_encontrado) {
                mensaje += ` - ✓ Excel asociado`;
            } else {
                mensaje += ` - ⚠ Sin Excel asociado`;
            }
            
            mostrarMensaje('mensaje-escaneo', mensaje, 'success');
            
            // Limpiar campo
            document.getElementById('codigo-barras-orden').value = '';
            
            // Recargar lista
            setTimeout(() => {
                cargarOrdenes();
                document.getElementById('codigo-barras-orden').focus();
            }, 1000);
        } else {
            mostrarMensaje('mensaje-escaneo', data.message || 'Error al registrar la orden', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('mensaje-escaneo', 'Error al registrar la orden', 'error');
    }
}

/**
 * Toggle formulario manual
 */
function toggleFormularioManual() {
    const form = document.getElementById('form-nueva-orden');
    if (form.style.display === 'none') {
        form.style.display = 'block';
    } else {
        form.style.display = 'none';
    }
}

/**
 * Registrar nueva orden (manual)
 */
async function registrarOrden(e) {
    e.preventDefault();
    
    const form = document.getElementById('form-nueva-orden');
    
    // Verificar si estamos editando
    if (form.dataset.editingId) {
        await actualizarOrden(form.dataset.editingId);
        return;
    }
    
    const codigoCorte = document.getElementById('orden-codigo-corte').value.trim();
    const numero = document.getElementById('orden-numero').value.trim();
    const proyecto = document.getElementById('orden-proyecto').value.trim();
    const descripcion = document.getElementById('orden-descripcion').value.trim();
    const cantidad = document.getElementById('orden-cantidad').value;
    const fecha = document.getElementById('orden-fecha').value;
    const prioridad = document.getElementById('orden-prioridad').value;
    
    if (!codigoCorte || !numero || !cantidad || !fecha || !prioridad) {
        mostrarMensaje('mensaje-orden', 'Por favor completa todos los campos obligatorios', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/ordenes/crear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo_corte: codigoCorte,
                numero,
                proyecto,
                descripcion,
                cantidad: parseInt(cantidad),
                fecha_entrega: fecha,
                prioridad
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensaje('mensaje-orden', 'Orden registrada correctamente', 'success');
            
            // Limpiar formulario
            document.getElementById('form-nueva-orden').reset();
            
            // Recargar lista
            setTimeout(() => {
                cargarOrdenes();
            }, 1000);
        } else {
            mostrarMensaje('mensaje-orden', data.message || 'Error al registrar la orden', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('mensaje-orden', 'Error al registrar la orden', 'error');
    }
}

/**
 * Cargar lista de órdenes
 */
async function cargarOrdenes() {
    const container = document.getElementById('lista-ordenes');
    container.innerHTML = '<p class="text-muted">Cargando...</p>';
    
    try {
        const response = await fetch('/api/ordenes/listar');
        const data = await response.json();
        
        if (data.success && data.ordenes) {
            todasLasOrdenes = data.ordenes; // Guardar todas las órdenes
            aplicarFiltros(); // Aplicar filtros actuales
        } else {
            container.innerHTML = '<p class="text-muted">No hay órdenes registradas</p>';
        }
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = '<p class="error">Error al cargar las órdenes</p>';
    }
}

/**
 * Aplicar filtros a las órdenes
 */
function aplicarFiltros() {
    const busqueda = document.getElementById('filtro-busqueda')?.value.toLowerCase() || '';
    const estado = document.getElementById('filtro-estado')?.value || '';
    const prioridad = document.getElementById('filtro-prioridad')?.value || '';
    const fechaDesde = document.getElementById('filtro-fecha-desde')?.value || '';
    const fechaHasta = document.getElementById('filtro-fecha-hasta')?.value || '';
    
    let ordenesFiltradas = todasLasOrdenes.filter(orden => {
        // Filtro de búsqueda (número, código, proyecto)
        const textoBusqueda = `${orden.numero} ${orden.codigo_corte} ${orden.proyecto || ''}`.toLowerCase();
        if (busqueda && !textoBusqueda.includes(busqueda)) {
            return false;
        }
        
        // Filtro de estado
        if (estado && orden.estado !== estado) {
            return false;
        }
        
        // Filtro de prioridad
        if (prioridad && orden.prioridad !== prioridad) {
            return false;
        }
        
        // Filtro de fecha desde
        if (fechaDesde && orden.fecha_entrega < fechaDesde) {
            return false;
        }
        
        // Filtro de fecha hasta
        if (fechaHasta && orden.fecha_entrega > fechaHasta) {
            return false;
        }
        
        return true;
    });
    
    mostrarOrdenes(ordenesFiltradas);
    actualizarEstadisticas(ordenesFiltradas);
}

/**
 * Limpiar todos los filtros
 */
function limpiarFiltros() {
    document.getElementById('filtro-busqueda').value = '';
    document.getElementById('filtro-estado').value = '';
    document.getElementById('filtro-prioridad').value = '';
    document.getElementById('filtro-fecha-desde').value = '';
    document.getElementById('filtro-fecha-hasta').value = '';
    aplicarFiltros();
}

/**
 * Mostrar órdenes en tabla
 */
function mostrarOrdenes(ordenes) {
    const container = document.getElementById('lista-ordenes');
    
    if (ordenes.length === 0) {
        container.innerHTML = '<p class="text-muted">No hay órdenes que coincidan con los filtros</p>';
        return;
    }
    
    let html = `
        <div style="margin-bottom: 10px; color: #6c757d; font-size: 0.9em;">
            Mostrando <strong>${ordenes.length}</strong> de <strong>${todasLasOrdenes.length}</strong> órdenes
        </div>
        <table class="tabla-datos">
            <thead>
                <tr>
                    <th>Código Corte</th>
                    <th>Archivo Excel</th>
                    <th>Número Orden</th>
                    <th>Proyecto</th>
                    <th>Cantidad</th>
                    <th>Fecha Liberación</th>
                    <th>Prioridad</th>
                    <th>Estado</th>
                    <th>Bono</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    ordenes.forEach(orden => {
        const prioridadIcono = {
            'baja': '🟢',
            'media': '🟡',
            'alta': '🟠',
            'urgente': '🔴'
        };
        
        // Estados con iconos y colores
        const estadoInfo = {
            'pendiente': { icono: '⏳', color: '#6c757d', texto: 'Pendiente' },
            'en_bono': { icono: '📋', color: '#0d6efd', texto: 'En Bono' },
            'engastando': { icono: '⚙️', color: '#ffc107', texto: 'Engastando' },
            'finalizado': { icono: '✅', color: '#28a745', texto: 'Finalizado' }
        };
        
        const estadoActual = estadoInfo[orden.estado] || { icono: '❓', color: '#6c757d', texto: orden.estado };
        const archivoExcel = orden.archivo_excel ? `<span title="${orden.archivo_excel}">📄 ${orden.archivo_excel.substring(0, 20)}...</span>` : '<span style="color: #ef4444;">❌ No asociado</span>';
        
        html += `
            <tr>
                <td><strong>${orden.codigo_corte || '-'}</strong></td>
                <td>${archivoExcel}</td>
                <td>${orden.numero}</td>
                <td>${orden.proyecto || '-'}</td>
                <td>${orden.cantidad}</td>
                <td>${formatearFecha(orden.fecha_entrega)}</td>
                <td>${prioridadIcono[orden.prioridad] || ''} ${orden.prioridad}</td>
                <td><span style="color: ${estadoActual.color}; font-weight: 600;">${estadoActual.icono} ${estadoActual.texto}</span></td>
                <td>${orden.bono ? `<strong style="color: #0d6efd;">📋 ${orden.bono}</strong>` : '<span style="color: #adb5bd;">-</span>'}</td>
                <td>
                    ${orden.estado === 'pendiente' ? `
                        <button onclick="editarOrden('${orden.id}')" class="btn-small btn-secondary">✏️ Editar</button>
                        <button onclick="eliminarOrden('${orden.id}')" class="btn-small btn-danger">🗑️ Eliminar</button>
                    ` : `
                        <span style="color: #6c757d; font-size: 0.9em;">-</span>
                    `}
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

/**
 * Actualizar estadísticas
 */
function actualizarEstadisticas(ordenes) {
    const total = ordenes.length;
    const pendientes = ordenes.filter(o => o.estado === 'pendiente').length;
    const enBono = ordenes.filter(o => o.estado === 'en_bono').length;
    const engastando = ordenes.filter(o => o.estado === 'engastando').length;
    const finalizadas = ordenes.filter(o => o.estado === 'finalizado').length;
    const urgentes = ordenes.filter(o => o.prioridad === 'urgente' && o.estado === 'pendiente').length;
    
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-pendientes').textContent = pendientes;
    document.getElementById('stat-completadas').textContent = finalizadas;
    document.getElementById('stat-urgentes').textContent = urgentes;
}

/**
 * Eliminar orden
 */
async function eliminarOrden(id) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta orden?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/ordenes/eliminar/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Orden eliminada correctamente');
            cargarOrdenes();
        } else {
            alert('Error al eliminar la orden: ' + (data.message || ''));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar la orden');
    }
}

/**
 * Editar orden
 */
async function editarOrden(id) {
    try {
        // Obtener la orden actual
        const response = await fetch('/api/ordenes/listar');
        const data = await response.json();
        
        if (!data.success) {
            alert('Error al cargar la orden');
            return;
        }
        
        const orden = data.ordenes.find(o => o.id === id);
        if (!orden) {
            alert('Orden no encontrada');
            return;
        }
        
        // Mostrar formulario manual con los datos
        const form = document.getElementById('form-nueva-orden');
        form.style.display = 'block';
        
        // Llenar el formulario
        document.getElementById('orden-codigo-corte').value = orden.codigo_corte || '';
        document.getElementById('orden-numero').value = orden.numero || '';
        document.getElementById('orden-proyecto').value = orden.proyecto || '';
        document.getElementById('orden-descripcion').value = orden.descripcion || '';
        document.getElementById('orden-cantidad').value = orden.cantidad || '';
        document.getElementById('orden-fecha').value = orden.fecha_entrega || '';
        document.getElementById('orden-prioridad').value = orden.prioridad || '';
        
        // Guardar el ID en un atributo del formulario
        form.dataset.editingId = id;
        
        // Cambiar texto del botón
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.textContent = '💾 Actualizar Orden';
        submitBtn.classList.remove('btn-primary');
        submitBtn.classList.add('btn-warning');
        
        // Agregar botón de cancelar
        let cancelBtn = document.getElementById('btn-cancelar-edicion');
        if (!cancelBtn) {
            cancelBtn = document.createElement('button');
            cancelBtn.id = 'btn-cancelar-edicion';
            cancelBtn.type = 'button';
            cancelBtn.className = 'btn-secondary';
            cancelBtn.textContent = '❌ Cancelar';
            cancelBtn.style.marginLeft = '10px';
            cancelBtn.onclick = cancelarEdicion;
            submitBtn.parentNode.insertBefore(cancelBtn, submitBtn.nextSibling);
        }
        
        // Scroll al formulario
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar la orden para editar');
    }
}

/**
 * Actualizar orden existente
 */
async function actualizarOrden(id) {
    const codigoCorte = document.getElementById('orden-codigo-corte').value.trim();
    const numero = document.getElementById('orden-numero').value.trim();
    const proyecto = document.getElementById('orden-proyecto').value.trim();
    const descripcion = document.getElementById('orden-descripcion').value.trim();
    const cantidad = document.getElementById('orden-cantidad').value;
    const fecha = document.getElementById('orden-fecha').value;
    const prioridad = document.getElementById('orden-prioridad').value;
    
    if (!codigoCorte || !numero || !cantidad || !fecha || !prioridad) {
        mostrarMensaje('mensaje-orden', 'Por favor completa todos los campos obligatorios', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/ordenes/actualizar/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo_corte: codigoCorte,
                numero,
                proyecto,
                descripcion,
                cantidad: parseInt(cantidad),
                fecha_entrega: fecha,
                prioridad
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensaje('mensaje-orden', 'Orden actualizada correctamente', 'success');
            cancelarEdicion();
            cargarOrdenes();
        } else {
            mostrarMensaje('mensaje-orden', data.message || 'Error al actualizar la orden', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('mensaje-orden', 'Error al actualizar la orden', 'error');
    }
}

/**
 * Cancelar edición
 */
function cancelarEdicion() {
    const form = document.getElementById('form-nueva-orden');
    form.reset();
    form.style.display = 'none';
    
    // Eliminar el ID de edición
    delete form.dataset.editingId;
    
    // Restaurar botón
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = '✅ Registrar Orden';
    submitBtn.classList.remove('btn-warning');
    submitBtn.classList.add('btn-primary');
    
    // Eliminar botón de cancelar
    const cancelBtn = document.getElementById('btn-cancelar-edicion');
    if (cancelBtn) {
        cancelBtn.remove();
    }
    
    // Limpiar mensaje
    const mensaje = document.getElementById('mensaje-orden');
    mensaje.classList.add('hidden');
}

/**
 * Editar orden (placeholder - DEPRECATED)
 */
function editarOrdenOld(id) {
    alert('Función de edición en desarrollo. ID: ' + id);
}

/**
 * Formatear fecha
 */
function formatearFecha(fecha) {
    if (!fecha) return '-';
    const date = new Date(fecha);
    return date.toLocaleDateString('es-ES');
}

/**
 * Mostrar mensaje
 */
function mostrarMensaje(elementId, mensaje, tipo) {
    const elemento = document.getElementById(elementId);
    elemento.textContent = mensaje;
    elemento.className = `mensaje ${tipo}`;
    elemento.classList.remove('hidden');
    
    setTimeout(() => {
        elemento.classList.add('hidden');
    }, 5000);
}
