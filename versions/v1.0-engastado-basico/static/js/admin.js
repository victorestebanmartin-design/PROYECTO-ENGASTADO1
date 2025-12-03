/**
 * Sistema de Engastado Automático
 * JavaScript Administración
 */

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    cargarArchivos();
    cargarCortes();
    
    // Event listener para formulario de upload
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', subirArchivo);
    }
    
    // Event listener para formulario de asociación
    const asociarForm = document.getElementById('asociar-form');
    if (asociarForm) {
        asociarForm.addEventListener('submit', asociarCorte);
    }
});

/**
 * Subir archivo Excel
 */
async function subirArchivo(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-upload');
    const file = fileInput.files[0];
    
    if (!file) {
        mostrarMensaje('upload-mensaje', 'Por favor selecciona un archivo', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensaje('upload-mensaje', 'Archivo subido correctamente: ' + data.filename, 'success');
            fileInput.value = '';
            
            // Recargar listas
            setTimeout(() => {
                cargarArchivos();
            }, 1000);
        } else {
            mostrarMensaje('upload-mensaje', data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('upload-mensaje', 'Error al subir el archivo', 'error');
    }
}

/**
 * Asociar código de barras con archivo
 */
async function asociarCorte(e) {
    e.preventDefault();
    
    const codigoBarras = document.getElementById('codigo-barras').value.trim();
    const archivo = document.getElementById('select-archivo').value;
    const descripcion = document.getElementById('descripcion').value.trim();
    const proyecto = document.getElementById('proyecto').value.trim();
    
    if (!codigoBarras || !archivo || !descripcion) {
        mostrarMensaje('asociar-mensaje', 'Por favor completa todos los campos obligatorios', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/add_corte', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                codigo_barras: codigoBarras,
                archivo: archivo,
                descripcion: descripcion,
                proyecto: proyecto
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensaje('asociar-mensaje', 'Corte asociado correctamente', 'success');
            
            // Limpiar formulario
            document.getElementById('codigo-barras').value = '';
            document.getElementById('select-archivo').value = '';
            document.getElementById('descripcion').value = '';
            document.getElementById('proyecto').value = '';
            
            // Recargar lista de cortes
            setTimeout(() => {
                cargarCortes();
            }, 1000);
        } else {
            mostrarMensaje('asociar-mensaje', data.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarMensaje('asociar-mensaje', 'Error al asociar el corte', 'error');
    }
}

/**
 * Cargar lista de archivos disponibles
 */
async function cargarArchivos() {
    try {
        const response = await fetch('/api/list_files');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('lista-archivos');
            const select = document.getElementById('select-archivo');
            
            if (data.files.length === 0) {
                container.innerHTML = '<p class="text-muted">No hay archivos subidos aún</p>';
                select.innerHTML = '<option value="">-- No hay archivos disponibles --</option>';
            } else {
                // Actualizar tabla
                let html = '<table><thead><tr><th>Nombre del Archivo</th><th>Tamaño</th><th>Acciones</th></tr></thead><tbody>';
                data.files.forEach(file => {
                    html += `
                        <tr>
                            <td>${file.nombre}</td>
                            <td>${file.tamano}</td>
                            <td>
                                <button onclick="eliminarArchivo('${file.nombre}')" class="btn-delete" title="Eliminar">
                                    🗑️
                                </button>
                            </td>
                        </tr>
                    `;
                });
                html += '</tbody></table>';
                container.innerHTML = html;
                
                // Actualizar select
                let optionsHTML = '<option value="">-- Seleccionar archivo --</option>';
                data.files.forEach(file => {
                    optionsHTML += `<option value="${file.nombre}">${file.nombre}</option>`;
                });
                select.innerHTML = optionsHTML;
            }
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('lista-archivos').innerHTML = '<p class="text-muted">Error al cargar archivos</p>';
    }
}

/**
 * Eliminar archivo Excel
 */
async function eliminarArchivo(filename) {
    if (!confirm(`¿Estás seguro de eliminar el archivo "${filename}"?\n\nEsto también eliminará todas las asociaciones de códigos de barras que usen este archivo.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename: filename })
        });
        
        const data = await response.json();
        
        if (data.success) {
            cargarArchivos();
            const container = document.getElementById('lista-archivos');
            const mensaje = document.createElement('div');
            mensaje.className = 'mensaje success';
            mensaje.textContent = 'Archivo eliminado correctamente';
            container.parentElement.insertBefore(mensaje, container);
            setTimeout(() => mensaje.remove(), 3000);
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el archivo');
    }
}

/**
 * Resetear todo el sistema
 */
async function resetearSistema() {
    const confirmacion1 = confirm('⚠️ ADVERTENCIA ⚠️\n\nEsto eliminará:\n- TODOS los archivos Excel\n- TODOS los códigos de barras registrados\n\n¿Estás SEGURO?');
    
    if (!confirmacion1) return;
    
    const confirmacion2 = confirm('⚠️ ÚLTIMA CONFIRMACIÓN ⚠️\n\nEsta acción NO SE PUEDE DESHACER.\n\n¿Continuar?');
    
    if (!confirmacion2) return;
    
    try {
        const response = await fetch('/api/reset_system', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Sistema reseteado correctamente.\n\nTodos los datos han sido eliminados.');
            // Recargar todas las listas
            cargarArchivos();
            cargarCortes();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al resetear el sistema');
    }
}

/**
 * Cargar lista de cortes registrados
 */
async function cargarCortes() {
    try {
        const response = await fetch('/api/list_cortes');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('lista-cortes');
            
            if (data.cortes.length === 0) {
                container.innerHTML = '<p class="text-muted">No hay cortes registrados aún</p>';
            } else {
                let html = `
                    <table>
                        <thead>
                            <tr>
                                <th>Código de Barras</th>
                                <th>Archivo</th>
                                <th>Descripción</th>
                                <th>Proyecto</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                data.cortes.forEach(corte => {
                    html += `
                        <tr>
                            <td><strong>${corte.codigo_barras}</strong></td>
                            <td>${corte.archivo}</td>
                            <td>${corte.descripcion}</td>
                            <td>${corte.proyecto || '-'}</td>
                            <td>
                                <button onclick="eliminarCorte('${corte.codigo_barras}')" class="btn-delete" title="Eliminar">
                                    🗑️
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            }
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('lista-cortes').innerHTML = '<p class="text-muted">Error al cargar cortes</p>';
    }
}

/**
 * Eliminar corte
 */
async function eliminarCorte(codigoBarras) {
    if (!confirm(`¿Estás seguro de eliminar el corte "${codigoBarras}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete_corte', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ codigo_barras: codigoBarras })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Recargar lista
            cargarCortes();
            // Mostrar mensaje temporal
            const container = document.getElementById('lista-cortes');
            const mensaje = document.createElement('div');
            mensaje.className = 'mensaje success';
            mensaje.textContent = 'Corte eliminado correctamente';
            container.parentElement.insertBefore(mensaje, container);
            setTimeout(() => mensaje.remove(), 3000);
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al eliminar el corte');
    }
}

/**
 * Mostrar mensaje
 */
function mostrarMensaje(elementId, texto, tipo = 'info') {
    const mensajeDiv = document.getElementById(elementId);
    mensajeDiv.textContent = texto;
    mensajeDiv.className = `mensaje ${tipo}`;
    mensajeDiv.classList.remove('hidden');
    
    setTimeout(() => {
        mensajeDiv.classList.add('hidden');
    }, 5000);
}
