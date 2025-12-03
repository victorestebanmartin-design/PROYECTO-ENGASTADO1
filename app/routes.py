"""
Rutas y endpoints de la aplicación
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from app.excel_manager import ExcelManager
from app.proyecto_manager import proyecto_manager

bp = Blueprint('main', __name__)

# Variable global para el gestor de Excel
excel_manager = None

def get_excel_manager():
    """Obtener instancia del gestor de Excel"""
    global excel_manager
    if excel_manager is None:
        excel_manager = ExcelManager(
            upload_folder=current_app.config['UPLOAD_FOLDER'],
            codigos_file=current_app.config['CODIGOS_FILE'],
            default_sheet=current_app.config['DEFAULT_SHEET']
        )
    return excel_manager

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/')
def home():
    """Landing page para seleccionar versión del sistema"""
    # Podríamos pasar métricas simples si hace falta en el futuro
    return render_template('home.html')

@bp.route('/v1')
def index():
    """Operación de engastado V1.0"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('index.html', cortes=cortes)

@bp.route('/v2')
def index_v2():
    """Página principal - Operación de engastado V2.0 Modo Interactivo"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('index-v2.html', cortes=cortes)

@bp.route('/v3')
def index_v3():
    """Página principal - Operación de engastado V3.0 Modo Avanzado"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('index-v3.html', cortes=cortes)

@bp.route('/progreso-bono')
def progreso_bono():
    """Vista de progreso del bono en tiempo real"""
    return render_template('progreso-bono.html')

@bp.route('/visualizacion')
def visualizacion():
    """Seleccionar bono para visualización"""
    return render_template('visualizacion.html')

@bp.route('/visualizacion/<nombre_bono>')
def visualizacion_bono(nombre_bono):
    """Dashboard de visualización para un bono específico"""
    return render_template('progreso-bono.html', bono_nombre=nombre_bono)

@bp.route('/admin')
def admin():
    """Página de administración de archivos"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('admin.html', cortes=cortes)

@bp.route('/gestion-puestos')
def gestion_puestos():
    """Página de gestión de puestos y máquinas"""
    return render_template('gestion-puestos.html')

@bp.route('/gestion-proyectos')
def gestion_proyectos():
    """Página de gestión de proyectos y carros"""
    return render_template('gestion-proyectos.html')

@bp.route('/gestion-bonos')
def gestion_bonos():
    """Página de gestión de bonos"""
    return render_template('gestion-bonos.html')

@bp.route('/api/cargar_corte', methods=['POST'])
def cargar_corte():
    """Cargar archivo Excel por código de barras"""
    data = request.get_json()
    codigo_barras = data.get('codigo_barras', '').strip()
    
    if not codigo_barras:
        return jsonify({'success': False, 'message': 'Código de barras vacío'}), 400
    
    manager = get_excel_manager()
    
    if manager.cargar_por_codigo(codigo_barras):
        return jsonify({
            'success': True,
            'message': 'Archivo cargado correctamente',
            'archivo': manager.current_file
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Código de barras no encontrado'
        }), 404

@bp.route('/api/listar_terminales', methods=['GET'])
def listar_terminales():
    """Listar todos los terminales únicos de TODOS los archivos Excel asociados"""
    manager = get_excel_manager()
    
    # Leer códigos de barras asociados
    codigos_file = current_app.config['CODIGOS_FILE']
    
    if not os.path.exists(codigos_file):
        return jsonify({
            'success': False,
            'message': 'No hay archivos Excel asociados a códigos de barras'
        }), 400
    
    with open(codigos_file, 'r', encoding='utf-8') as f:
        codigos_data = json.load(f)
    
    # Obtener la lista de cortes
    cortes = codigos_data.get('cortes', [])
    
    if not cortes:
        return jsonify({
            'success': False,
            'message': 'No hay archivos Excel asociados a códigos de barras'
        }), 400
    
    # Recopilar terminales únicos de todos los archivos
    todos_terminales = set()
    archivos_procesados = []
    archivos_con_error = []
    
    for corte in cortes:
        archivo = corte.get('archivo')
        if not archivo:
            continue
            
        archivo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], archivo)
        
        if not os.path.exists(archivo_path):
            archivos_con_error.append(archivo)
            continue
        
        try:
            # Cargar temporalmente este archivo
            temp_manager = ExcelManager(
                upload_folder=current_app.config['UPLOAD_FOLDER'],
                codigos_file=current_app.config['CODIGOS_FILE'],
                default_sheet=current_app.config['DEFAULT_SHEET']
            )
            temp_manager.cargar_excel_directo(archivo)
            
            # Obtener terminales de este archivo
            terminales = temp_manager.listar_terminales_unicos()
            todos_terminales.update(terminales)
            archivos_procesados.append(archivo)
            
        except Exception as e:
            archivos_con_error.append(f"{archivo} (error: {str(e)})")
    
    if not todos_terminales:
        return jsonify({
            'success': False,
            'message': 'No se encontraron terminales en los archivos'
        }), 400
    
    # Convertir a lista ordenada
    terminales_lista = sorted(list(todos_terminales))
    
    # Obtener terminales desactivados
    desactivados_file = os.path.join(current_app.config['DATA_FOLDER'], 'terminales_desactivados.json')
    desactivados = []
    
    if os.path.exists(desactivados_file):
        with open(desactivados_file, 'r', encoding='utf-8') as f:
            desactivados = json.load(f)
    
    # Marcar terminales desactivados
    terminales_con_estado = []
    for terminal in terminales_lista:
        terminales_con_estado.append({
            'terminal': terminal,
            'desactivado': terminal in desactivados
        })
    
    return jsonify({
        'success': True,
        'total_terminales': len(terminales_lista),
        'terminales': terminales_con_estado,
        'archivos_procesados': archivos_procesados,
        'archivos_con_error': archivos_con_error
    })

@bp.route('/api/buscar_terminal', methods=['POST'])
def buscar_terminal():
    """Buscar terminal en el archivo Excel cargado"""
    data = request.get_json()
    terminal = data.get('terminal', '').strip()
    
    if not terminal:
        return jsonify({'success': False, 'message': 'Terminal vacío'}), 400
    
    manager = get_excel_manager()
    
    if manager.current_df is None:
        # Intentar cargar automáticamente el último archivo usado
        if not manager.cargar_ultimo_si_existe():
            return jsonify({
                'success': False,
                'message': 'No hay ningún archivo Excel cargado'
            }), 400
    
    # Buscar terminal
    resultados = manager.buscar_terminal(terminal)
    
    if not resultados:
        return jsonify({
            'success': False,
            'message': f'Terminal "{terminal}" no encontrado'
        }), 404
    
    # Agrupar resultados
    grupos = manager.agrupar_por_cable_elemento(resultados, terminal)
    
    # Calcular total de terminales necesarios
    total_terminales = sum(grupo['num_terminales'] for grupo in grupos.values())
    
    return jsonify({
        'success': True,
        'terminal': terminal,
        'archivo': manager.current_file,
        'total_resultados': len(resultados),
        'total_grupos': len(grupos),
        'total_terminales': total_terminales,
        'grupos': list(grupos.values())
    })

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Subir archivo Excel"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se seleccionó archivo'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Guardar archivo
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Archivo subido correctamente',
            'filename': filename
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Tipo de archivo no permitido. Solo .xlsx y .xls'
        }), 400

@bp.route('/api/add_corte', methods=['POST'])
def add_corte():
    """Agregar nuevo corte de cable (asociar código de barras con archivo)"""
    data = request.get_json()
    
    codigo_barras = data.get('codigo_barras', '').strip()
    archivo = data.get('archivo', '').strip()
    descripcion = data.get('descripcion', '').strip()
    proyecto = data.get('proyecto', '').strip()
    
    if not codigo_barras or not archivo:
        return jsonify({
            'success': False,
            'message': 'Código de barras y archivo son obligatorios'
        }), 400
    
    # Verificar que el archivo existe
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], archivo)
    if not os.path.exists(filepath):
        return jsonify({
            'success': False,
            'message': f'El archivo "{archivo}" no existe'
        }), 400
    
    manager = get_excel_manager()
    
    if manager.add_corte(codigo_barras, archivo, descripcion, proyecto):
        return jsonify({
            'success': True,
            'message': 'Corte agregado correctamente'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'El código de barras ya existe'
        }), 400

@bp.route('/api/list_cortes', methods=['GET'])
def list_cortes():
    """Listar todos los cortes registrados"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    
    return jsonify({
        'success': True,
        'cortes': cortes
    })

@bp.route('/api/delete_corte', methods=['POST'])
def delete_corte():
    """Eliminar corte de cable"""
    data = request.get_json()
    codigo_barras = data.get('codigo_barras', '').strip()
    
    if not codigo_barras:
        return jsonify({
            'success': False,
            'message': 'Código de barras vacío'
        }), 400
    
    manager = get_excel_manager()
    
    if manager.delete_corte(codigo_barras):
        return jsonify({
            'success': True,
            'message': 'Corte eliminado correctamente'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Corte no encontrado'
        }), 404

@bp.route('/api/delete_file', methods=['POST'])
def delete_file():
    """Eliminar archivo Excel"""
    data = request.get_json()
    filename = data.get('filename', '').strip()
    
    if not filename:
        return jsonify({
            'success': False,
            'message': 'Nombre de archivo vacío'
        }), 400
    
    manager = get_excel_manager()
    
    if manager.delete_file(filename):
        return jsonify({
            'success': True,
            'message': 'Archivo eliminado correctamente'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Archivo no encontrado o error al eliminar'
        }), 404

@bp.route('/api/reset_system', methods=['POST'])
def reset_system():
    """Resetear todo el sistema"""
    manager = get_excel_manager()
    
    if manager.reset_system():
        return jsonify({
            'success': True,
            'message': 'Sistema reseteado correctamente'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Error al resetear el sistema'
        }), 500

@bp.route('/api/list_files', methods=['GET'])
def list_files():
    """Listar archivos Excel en la carpeta de uploads"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(upload_folder):
        return jsonify({'success': True, 'files': []})
    
    files = []
    for filename in os.listdir(upload_folder):
        if allowed_file(filename):
            filepath = os.path.join(upload_folder, filename)
            size = os.path.getsize(filepath)
            files.append({
                'nombre': filename,
                'tamano': f"{size / 1024:.2f} KB"
            })
    
    return jsonify({
        'success': True,
        'files': files
    })

@bp.route('/api/terminales_desactivados', methods=['GET'])
def get_terminales_desactivados():
    """Obtener lista de terminales desactivados"""
    desactivados_file = os.path.join(current_app.config['DATA_FOLDER'], 'terminales_desactivados.json')
    
    if os.path.exists(desactivados_file):
        with open(desactivados_file, 'r', encoding='utf-8') as f:
            desactivados = json.load(f)
    else:
        desactivados = []
    
    return jsonify({
        'success': True,
        'terminales': desactivados
    })

@bp.route('/api/terminales_desactivados', methods=['POST'])
def toggle_terminal_desactivado():
    """Activar o desactivar un terminal"""
    data = request.get_json()
    terminal = data.get('terminal', '').strip()
    accion = data.get('accion', 'desactivar')  # 'desactivar' o 'activar'
    
    if not terminal:
        return jsonify({
            'success': False,
            'message': 'Terminal no especificado'
        }), 400
    
    desactivados_file = os.path.join(current_app.config['DATA_FOLDER'], 'terminales_desactivados.json')
    
    # Leer lista actual
    if os.path.exists(desactivados_file):
        with open(desactivados_file, 'r', encoding='utf-8') as f:
            desactivados = json.load(f)
    else:
        desactivados = []
    
    # Modificar lista
    if accion == 'desactivar':
        if terminal not in desactivados:
            desactivados.append(terminal)
            mensaje = f'Terminal {terminal} desactivado'
        else:
            mensaje = f'Terminal {terminal} ya estaba desactivado'
    else:  # activar
        if terminal in desactivados:
            desactivados.remove(terminal)
            mensaje = f'Terminal {terminal} activado'
        else:
            mensaje = f'Terminal {terminal} ya estaba activado'
    
    # Guardar lista actualizada
    with open(desactivados_file, 'w', encoding='utf-8') as f:
        json.dump(desactivados, f, indent=2)
    
    return jsonify({
        'success': True,
        'message': mensaje,
        'terminales': desactivados
    })

# ================================
# API ROUTES PARA PUESTOS Y MÁQUINAS
# ================================

@bp.route('/api/puestos', methods=['GET'])
def get_puestos():
    """Obtener lista de puestos"""
    try:
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({'success': True, 'puestos': data.get('puestos', [])})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/puestos', methods=['POST'])
def create_puesto():
    """Crear nuevo puesto"""
    try:
        datos = request.json
        
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Generar ID único
        existing_ids = [p['id'] for p in data.get('puestos', [])]
        new_id = f"puesto_{len(existing_ids) + 1}"
        while new_id in existing_ids:
            import random
            new_id = f"puesto_{len(existing_ids) + 1}_{random.randint(100, 999)}"
        
        # Crear nuevo puesto
        nuevo_puesto = {
            'id': new_id,
            'nombre': datos['nombre'],
            'descripcion': datos.get('descripcion', ''),
            'activo': True,
            'maquinas': []
        }
        
        data.setdefault('puestos', []).append(nuevo_puesto)
        
        # Guardar cambios
        with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'puesto': nuevo_puesto})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/puestos/<puesto_id>', methods=['PUT'])
def update_puesto(puesto_id):
    """Actualizar puesto existente"""
    try:
        datos = request.json
        
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar y actualizar puesto
        for puesto in data.get('puestos', []):
            if puesto['id'] == puesto_id:
                puesto['nombre'] = datos.get('nombre', puesto['nombre'])
                puesto['descripcion'] = datos.get('descripcion', puesto['descripcion'])
                puesto['activo'] = datos.get('activo', puesto['activo'])
                
                # Guardar cambios
                with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                return jsonify({'success': True, 'puesto': puesto})
        
        return jsonify({'success': False, 'message': 'Puesto no encontrado'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/puestos/<puesto_id>', methods=['DELETE'])
def delete_puesto(puesto_id):
    """Eliminar puesto"""
    try:
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Eliminar puesto
        puestos_originales = len(data.get('puestos', []))
        data['puestos'] = [p for p in data.get('puestos', []) if p['id'] != puesto_id]
        
        if len(data['puestos']) < puestos_originales:
            # Guardar cambios
            with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': 'Puesto eliminado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'Puesto no encontrado'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/maquinas', methods=['GET'])
def get_maquinas():
    """Obtener lista de máquinas con información del puesto"""
    try:
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer todas las máquinas con información del puesto
        maquinas = []
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                maquina_info = maquina.copy()
                maquina_info['puesto_id'] = puesto['id']
                maquina_info['puesto_nombre'] = puesto['nombre']
                maquinas.append(maquina_info)
        
        return jsonify({'success': True, 'maquinas': maquinas})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/maquinas', methods=['POST'])
def create_maquina():
    """Crear nueva máquina"""
    try:
        datos = request.json
        puesto_id = datos.get('puesto_id')
        
        if not puesto_id:
            return jsonify({'success': False, 'message': 'Debe seleccionar un puesto'})
        
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar el puesto
        puesto_encontrado = None
        for puesto in data.get('puestos', []):
            if puesto['id'] == puesto_id:
                puesto_encontrado = puesto
                break
        
        if not puesto_encontrado:
            return jsonify({'success': False, 'message': 'Puesto no encontrado'})
        
        # Generar ID único para la máquina
        existing_ids = []
        for p in data.get('puestos', []):
            for m in p.get('maquinas', []):
                existing_ids.append(m['id'])
        
        import random
        new_id = f"maquina_{len(existing_ids) + 1}"
        while new_id in existing_ids:
            new_id = f"maquina_{len(existing_ids) + 1}_{random.randint(100, 999)}"
        
        # Crear nueva máquina
        nueva_maquina = {
            'id': new_id,
            'nombre': datos['nombre'],
            'modelo': datos.get('modelo', ''),
            'descripcion': datos.get('descripcion', ''),
            'activo': True,
            'terminales_asignados': []
        }
        
        # Agregar máquina al puesto
        puesto_encontrado.setdefault('maquinas', []).append(nueva_maquina)
        
        # Guardar cambios
        with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Preparar respuesta con información completa
        nueva_maquina['puesto_id'] = puesto_id
        nueva_maquina['puesto_nombre'] = puesto_encontrado['nombre']
        
        return jsonify({'success': True, 'maquina': nueva_maquina})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/maquinas/<maquina_id>', methods=['PUT'])
def update_maquina(maquina_id):
    """Actualizar máquina existente"""
    try:
        datos = request.json
        print(f"[DEBUG] Actualizando máquina {maquina_id} con datos: {datos}")
        
        # Validación básica
        if not datos:
            print("[DEBUG] No se recibieron datos")
            return jsonify({'success': False, 'message': 'No se recibieron datos'})
        
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar y actualizar máquina
        maquina_encontrada = None
        puesto_padre = None
        
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                if maquina['id'] == maquina_id:
                    maquina_encontrada = maquina
                    puesto_padre = puesto
                    break
            if maquina_encontrada:
                break
        
        if not maquina_encontrada:
            print(f"[DEBUG] Máquina {maquina_id} no encontrada")
            return jsonify({'success': False, 'message': 'Máquina no encontrada'})
        
        print(f"[DEBUG] Máquina encontrada: {maquina_encontrada}")
        print(f"[DEBUG] Puesto padre: {puesto_padre['id']}")
        
        # Actualizar campos - asegurar que todos los campos existen
        if 'nombre' in datos:
            maquina_encontrada['nombre'] = datos['nombre']
        if 'modelo' in datos:
            maquina_encontrada['modelo'] = datos['modelo']
        if 'descripcion' in datos:
            maquina_encontrada['descripcion'] = datos['descripcion']
        if 'activo' in datos:
            maquina_encontrada['activo'] = datos['activo']
            
        # Asegurar que todos los campos requeridos existen
        if 'descripcion' not in maquina_encontrada:
            maquina_encontrada['descripcion'] = ''
        if 'modelo' not in maquina_encontrada:
            maquina_encontrada['modelo'] = ''
        
        print(f"[DEBUG] Máquina después de actualizar: {maquina_encontrada}")
        
        # Si se cambió el puesto, mover la máquina
        nuevo_puesto_id = datos.get('puesto_id')
        if nuevo_puesto_id and nuevo_puesto_id != puesto_padre['id']:
            # Encontrar nuevo puesto
            nuevo_puesto = None
            for puesto in data.get('puestos', []):
                if puesto['id'] == nuevo_puesto_id:
                    nuevo_puesto = puesto
                    break
            
            if nuevo_puesto:
                # Remover de puesto actual
                puesto_padre['maquinas'].remove(maquina_encontrada)
                # Agregar a nuevo puesto
                nuevo_puesto.setdefault('maquinas', []).append(maquina_encontrada)
                puesto_padre = nuevo_puesto
        
        # Guardar cambios
        with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Preparar respuesta
        maquina_encontrada['puesto_id'] = puesto_padre['id']
        maquina_encontrada['puesto_nombre'] = puesto_padre['nombre']
        
        print(f"[DEBUG] Respuesta exitosa: {maquina_encontrada}")
        return jsonify({'success': True, 'maquina': maquina_encontrada})
        
    except Exception as e:
        print(f"[ERROR] Excepción en update_maquina: {e}")
        print(f"[ERROR] Tipo de excepción: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/maquinas/<maquina_id>', methods=['DELETE'])
def delete_maquina(maquina_id):
    """Eliminar máquina"""
    try:
        # Cargar datos existentes
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar y eliminar máquina
        maquina_eliminada = False
        
        for puesto in data.get('puestos', []):
            maquinas_originales = len(puesto.get('maquinas', []))
            puesto['maquinas'] = [m for m in puesto.get('maquinas', []) if m['id'] != maquina_id]
            
            if len(puesto['maquinas']) < maquinas_originales:
                maquina_eliminada = True
                break
        
        if maquina_eliminada:
            # Guardar cambios
            with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return jsonify({'success': True, 'message': 'Máquina eliminada correctamente'})
        else:
            return jsonify({'success': False, 'message': 'Máquina no encontrada'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/terminales-disponibles', methods=['GET'])
def get_terminales_disponibles():
    """Obtener todos los terminales disponibles con su estado de asignación"""
    try:
        manager = get_excel_manager()
        
        # Obtener todos los terminales únicos del sistema
        terminales_sistema = manager.listar_terminales_unicos()
        
        # Cargar asignaciones actuales
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Crear diccionario de terminales asignados
        terminales_asignados = {}
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                for terminal in maquina.get('terminales_asignados', []):
                    terminales_asignados[terminal] = {
                        'maquina_id': maquina['id'],
                        'maquina_nombre': maquina['nombre'],
                        'puesto_nombre': puesto['nombre']
                    }
        
        # Preparar respuesta con estado de cada terminal
        terminales_con_estado = []
        for terminal in terminales_sistema:
            estado = {
                'terminal': terminal,
                'asignado': terminal in terminales_asignados,
                'asignacion': terminales_asignados.get(terminal, None)
            }
            terminales_con_estado.append(estado)
        
        # Contar terminales sin asignar
        sin_asignar = len([t for t in terminales_con_estado if not t['asignado']])
        
        return jsonify({
            'success': True, 
            'terminales': terminales_con_estado,
            'total': len(terminales_sistema),
            'sin_asignar': sin_asignar
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/asignar-terminal', methods=['POST'])
def asignar_terminal():
    """Asignar un terminal a una máquina"""
    try:
        datos = request.json
        terminal = datos.get('terminal')
        maquina_id = datos.get('maquina_id')
        
        if not terminal or not maquina_id:
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'})
        
        # Cargar datos
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar que el terminal no esté ya asignado
        terminal_ya_asignado = False
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                if terminal in maquina.get('terminales_asignados', []):
                    terminal_ya_asignado = True
                    break
            if terminal_ya_asignado:
                break
        
        if terminal_ya_asignado:
            return jsonify({'success': False, 'message': 'El terminal ya está asignado a otra máquina'})
        
        # Encontrar la máquina y asignar terminal
        maquina_encontrada = False
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                if maquina['id'] == maquina_id:
                    if 'terminales_asignados' not in maquina:
                        maquina['terminales_asignados'] = []
                    maquina['terminales_asignados'].append(terminal)
                    maquina_encontrada = True
                    break
            if maquina_encontrada:
                break
        
        if not maquina_encontrada:
            return jsonify({'success': False, 'message': 'Máquina no encontrada'})
        
        # Guardar cambios
        with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': f'Terminal {terminal} asignado correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/desasignar-terminal', methods=['POST'])
def desasignar_terminal():
    """Desasignar un terminal de su máquina actual"""
    try:
        datos = request.json
        terminal = datos.get('terminal')
        
        if not terminal:
            return jsonify({'success': False, 'message': 'Terminal requerido'})
        
        # Cargar datos
        with open('data/puestos_maquinas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar y remover el terminal
        terminal_removido = False
        for puesto in data.get('puestos', []):
            for maquina in puesto.get('maquinas', []):
                if terminal in maquina.get('terminales_asignados', []):
                    maquina['terminales_asignados'].remove(terminal)
                    terminal_removido = True
                    break
            if terminal_removido:
                break
        
        if not terminal_removido:
            return jsonify({'success': False, 'message': 'Terminal no encontrado'})
        
        # Guardar cambios
        with open('data/puestos_maquinas.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': f'Terminal {terminal} desasignado correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ================================
# API ROUTES PARA PROYECTOS Y CARROS
# ================================

@bp.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    """Obtener lista de proyectos"""
    try:
        proyectos = proyecto_manager.obtener_proyectos()
        return jsonify({'success': True, 'proyectos': proyectos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/proyectos', methods=['POST'])
def create_proyecto():
    """Crear nuevo proyecto"""
    try:
        datos = request.json
        nombre = datos.get('nombre')
        archivo = datos.get('archivo')
        carro = datos.get('carro')
        
        if not nombre or not archivo:
            return jsonify({'success': False, 'message': 'Nombre y archivo son requeridos'})
        
        # Verificar que el archivo existe
        archivo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], archivo)
        if not os.path.exists(archivo_path):
            return jsonify({'success': False, 'message': f'El archivo "{archivo}" no existe'})
        
        proyecto = proyecto_manager.agregar_proyecto(nombre, archivo, carro)
        return jsonify({'success': True, 'proyecto': proyecto})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/proyectos/<int:proyecto_id>', methods=['DELETE'])
def delete_proyecto(proyecto_id):
    """Eliminar proyecto"""
    try:
        proyecto_manager.eliminar_proyecto(proyecto_id)
        return jsonify({'success': True, 'message': 'Proyecto eliminado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/carros', methods=['GET'])
def get_carros():
    """Obtener estado de todos los carros"""
    try:
        carros = proyecto_manager.obtener_carros()
        return jsonify({'success': True, 'carros': carros})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/carros/asignar', methods=['POST'])
def asignar_proyecto_carro():
    """Asignar proyecto a un carro"""
    try:
        datos = request.json
        proyecto_id = datos.get('proyecto_id')
        carro = datos.get('carro')
        
        if not proyecto_id or not carro:
            return jsonify({'success': False, 'message': 'Proyecto y carro son requeridos'})
        
        proyecto_manager.asignar_carro(proyecto_id, carro)
        return jsonify({'success': True, 'message': f'Proyecto asignado al carro {carro}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/carros/<int:carro>/liberar', methods=['POST'])
def liberar_carro(carro):
    """Liberar un carro"""
    try:
        proyecto_manager.liberar_carro(carro)
        return jsonify({'success': True, 'message': f'Carro {carro} liberado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/proyectos/<int:proyecto_id>/progreso', methods=['POST'])
def actualizar_progreso_proyecto(proyecto_id):
    """Actualizar progreso de un proyecto"""
    try:
        datos = request.json
        terminal = datos.get('terminal')
        
        if not terminal:
            return jsonify({'success': False, 'message': 'Terminal requerido'})
        
        proyecto_manager.actualizar_progreso(proyecto_id, terminal)
        return jsonify({'success': True, 'message': 'Progreso actualizado'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/nombre-sugerido', methods=['GET'])
def obtener_nombre_bono_sugerido():
    """Obtener nombre sugerido para nuevo bono"""
    try:
        nombre = proyecto_manager.generar_nombre_bono_sugerido()
        return jsonify({'success': True, 'nombre': nombre})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/generar', methods=['POST'])
def generar_bono():
    """Generar nuevo bono con todos los carros ocupados"""
    try:
        datos = request.json
        nombre_bono = datos.get('nombre', '').strip()
        
        if not nombre_bono:
            return jsonify({'success': False, 'message': 'Nombre de bono requerido'})
        
        bono, error = proyecto_manager.generar_bono(nombre_bono)
        
        if error:
            return jsonify({'success': False, 'message': error})
        
        return jsonify({'success': True, 'bono': bono})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos', methods=['GET'])
def listar_bonos():
    """Obtener lista de todos los bonos"""
    try:
        bonos = proyecto_manager.obtener_todos_bonos()
        return jsonify({'success': True, 'bonos': bonos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>', methods=['GET'])
def obtener_bono(nombre_bono):
    """Obtener información de un bono"""
    try:
        bono = proyecto_manager.obtener_bono(nombre_bono)
        
        if not bono:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
        
        return jsonify({'success': True, 'bono': bono})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/validar', methods=['POST'])
def validar_bono():
    """Validar un código de bono"""
    try:
        datos = request.json
        nombre_bono = datos.get('nombre_bono', '').strip()
        
        if not nombre_bono:
            return jsonify({'success': False, 'message': 'Nombre de bono vacío'})
        
        # Normalizar el nombre (quitar ceros a la izquierda del sufijo)
        # Ejemplo: 20251201_01 -> 20251201_1
        partes = nombre_bono.split('_')
        if len(partes) == 2:
            try:
                numero = int(partes[1])
                nombre_normalizado = f"{partes[0]}_{numero}"
            except:
                nombre_normalizado = nombre_bono
        else:
            nombre_normalizado = nombre_bono
        
        valido, resultado = proyecto_manager.validar_bono(nombre_normalizado)
        
        if not valido:
            # Intentar con el nombre original si la normalización no funcionó
            valido, resultado = proyecto_manager.validar_bono(nombre_bono)
            
        if not valido:
            return jsonify({'success': False, 'message': resultado})
        
        return jsonify({'success': True, 'bono': resultado})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>/progreso', methods=['POST'])
def actualizar_progreso_bono(nombre_bono):
    """Actualizar progreso de un bono"""
    try:
        datos = request.json
        terminal = datos.get('terminal')  # Terminal del operario/puesto
        carro = datos.get('carro')
        terminales_proyecto = datos.get('terminales_proyecto', [])  # Terminales del proyecto completados
        
        if not terminal or not carro:
            return jsonify({'success': False, 'message': 'Terminal y carro requeridos'})
        
        exito = proyecto_manager.actualizar_progreso_bono(
            nombre_bono, 
            terminal, 
            carro,
            terminales_proyecto
        )
        
        if exito:
            return jsonify({'success': True, 'message': 'Progreso actualizado'})
        else:
            return jsonify({'success': False, 'message': 'Error al actualizar progreso'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>/progreso', methods=['GET'])
def obtener_progreso_bono(nombre_bono):
    """Obtener progreso de un bono"""
    try:
        progreso = proyecto_manager.obtener_progreso_bono(nombre_bono)
        
        if progreso is not None:
            return jsonify({'success': True, 'progreso': progreso})
        else:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>/progreso-por-carro', methods=['GET'])
def obtener_progreso_por_carro(nombre_bono):
    """Obtener progreso detallado por carro"""
    try:
        bono = proyecto_manager.obtener_bono(nombre_bono)
        if not bono:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
        
        progreso_por_carro = bono.get('progreso_por_carro', {})
        
        return jsonify({
            'success': True,
            'progreso_por_carro': progreso_por_carro
        })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>', methods=['DELETE'])
def eliminar_bono(nombre_bono):
    """Eliminar un bono"""
    try:
        exito = proyecto_manager.eliminar_bono(nombre_bono)
        
        if exito:
            return jsonify({'success': True, 'message': 'Bono eliminado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'No se pudo eliminar el bono'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/bonos/<nombre_bono>', methods=['PUT'])
def actualizar_bono(nombre_bono):
    """Actualizar información de un bono"""
    try:
        datos = request.json
        nuevo_nombre = datos.get('nombre', nombre_bono)
        estado = datos.get('estado')
        
        resultado = proyecto_manager.actualizar_bono(nombre_bono, nuevo_nombre, estado)
        
        if resultado:
            return jsonify({'success': True, 'message': 'Bono actualizado correctamente'})
        else:
            return jsonify({'success': False, 'error': 'Bono no encontrado'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/bonos/<nombre_bono>/reporte', methods=['GET'])
def generar_reporte_bono(nombre_bono):
    """Generar reporte detallado de un bono"""
    try:
        from datetime import datetime
        
        bono = proyecto_manager.obtener_bono(nombre_bono)
        if not bono:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
        
        progreso = bono.get('progreso', {})
        
        # Generar estadísticas
        total_terminales = len(progreso)
        total_carros_completados = 0
        detalle = []
        
        for terminal, info in progreso.items():
            carros_completados = info.get('carros_completados', [])
            estado = info.get('estado', 'en_progreso')
            
            # Calcular fecha/hora (placeholder - se puede mejorar guardando timestamps)
            fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            detalle.append({
                'terminal': terminal,
                'carros_completados': carros_completados,
                'num_carros': len(carros_completados),
                'estado': estado,
                'fecha_hora': fecha_hora
            })
            
            total_carros_completados += len(carros_completados)
        
        # Calcular progreso general
        total_carros_posibles = total_terminales * len(bono.get('carros', []))
        progreso_general = round((total_carros_completados / total_carros_posibles * 100) if total_carros_posibles > 0 else 0, 2)
        
        reporte = {
            'total_terminales': total_terminales,
            'total_carros': total_carros_completados,
            'progreso_general': progreso_general,
            'detalle': detalle
        }
        
        return jsonify({'success': True, 'reporte': reporte})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/excel/<archivo>/terminales', methods=['GET'])
def obtener_terminales_excel(archivo):
    """Obtener lista de terminales únicos de un archivo Excel"""
    try:
        manager = get_excel_manager()
        
        # Cargar el archivo Excel
        exito = manager.cargar_excel_directo(archivo)
        if not exito:
            return jsonify({'success': False, 'message': f'No se pudo cargar el archivo {archivo}'})
        
        # Obtener terminales únicos
        terminales = manager.listar_terminales_unicos()
        
        return jsonify({
            'success': True,
            'terminales': terminales,
            'total': len(terminales)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/datos_trabajo_v3')
def datos_trabajo_v3():
    """
    Obtener datos de trabajo para V3
    Parámetros: archivo, terminal, maquina
    """
    try:
        archivo = request.args.get('archivo')
        terminal = request.args.get('terminal')
        maquina = request.args.get('maquina')
        
        if not archivo or not terminal:
            return jsonify({
                'success': False,
                'message': 'Parámetros incompletos'
            })
        
        # Cargar el archivo Excel
        manager = get_excel_manager()
        if not manager.cargar_excel_directo(archivo):
            return jsonify({
                'success': False,
                'message': f'No se pudo cargar el archivo {archivo}'
            })
        
        # Buscar datos del terminal
        resultados = manager.buscar_terminal(terminal)
        
        if not resultados:
            return jsonify({
                'success': True,
                'paquetes': [],
                'total_terminales': 0,
                'grupos': []
            })
        
        # Agrupar por cable y elemento
        grupos = manager.agrupar_por_cable_elemento(resultados, terminal)
        
        # Convertir a lista de paquetes
        paquetes = []
        total_terminales = 0
        
        for grupo in grupos.values():
            paquete = {
                'cod_cable': grupo['cod_cable'],
                'elemento': grupo['elemento'],
                'descripcion': grupo['descripcion'],
                'seccion': grupo['seccion'],
                'longitud': grupo['longitud'],
                'cables': grupo['todos_cables'],
                'num_cables': grupo['num_cables'],
                'num_terminales': grupo['num_terminales'],
                'cables_doble_terminal': grupo.get('cables_doble_terminal', []),
                'cables_de_terminal': grupo.get('cables_de_terminal', []),
                'cables_para_terminal': grupo.get('cables_para_terminal', [])
            }
            paquetes.append(paquete)
            total_terminales += grupo['num_terminales']
        
        return jsonify({
            'success': True,
            'paquetes': paquetes,
            'total_terminales': total_terminales,
            'grupos': list(grupos.values())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener datos: {str(e)}'
        })

