"""
Rutas y endpoints de la aplicación
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import logging
from datetime import datetime
import time
import pandas as pd
from app.excel_manager import ExcelManager
from app.proyecto_manager import proyecto_manager

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Variable global para el gestor de Excel
excel_manager = None
terminales_cache = {
    'signature': None,
    'timestamp': 0,
    'terminales': None,
    'archivos_con_error': None
}

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

def _build_terminales_signature(codigos_file, upload_folder, cortes):
    codigos_mtime = os.path.getmtime(codigos_file) if os.path.exists(codigos_file) else None
    archivos_info = []
    for corte in cortes:
        archivo = corte.get('archivo')
        if not archivo:
            continue
        archivo_path = os.path.join(upload_folder, archivo)
        try:
            mtime = os.path.getmtime(archivo_path)
        except OSError:
            mtime = None
        archivos_info.append((archivo, mtime))
    return (codigos_mtime, tuple(sorted(archivos_info)))

def _build_terminales_globales(upload_folder, codigos_file, default_sheet, cortes):
    terminales_sistema = set()
    archivos_con_error = []

    for corte in cortes:
        archivo = corte.get('archivo')
        if not archivo:
            continue

        archivo_path = os.path.join(upload_folder, archivo)
        if not os.path.exists(archivo_path):
            archivos_con_error.append(archivo)
            continue

        try:
            temp_manager = ExcelManager(
                upload_folder=upload_folder,
                codigos_file=codigos_file,
                default_sheet=default_sheet
            )
            temp_manager.cargar_excel_directo(archivo)
            terminales_sistema.update(temp_manager.listar_terminales_unicos())
        except Exception as e:
            archivos_con_error.append(f"{archivo} (error: {str(e)})")

    return terminales_sistema, archivos_con_error

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

@bp.route('/registro-ordenes')
def registro_ordenes():
    """Página de registro de órdenes de producción"""
    return render_template('registro-ordenes.html')

@bp.route('/etiquetas')
def etiquetas():
    """Página de generación de etiquetas para elementos de cortes"""
    return render_template('etiquetas.html')

@bp.route('/api/codigos_cortes/listar', methods=['GET'])
def listar_codigos_cortes():
    """Obtener lista de todos los códigos de corte disponibles"""
    try:
        codigos_file = current_app.config['CODIGOS_FILE']
        
        if not os.path.exists(codigos_file):
            return jsonify({
                'success': True,
                'codigos': []
            })
        
        with open(codigos_file, 'r', encoding='utf-8') as f:
            codigos_data = json.load(f)
        
        cortes = codigos_data.get('cortes', [])
        
        # Retornar solo los códigos y archivos
        codigos_lista = [{
            'codigo': corte.get('codigo_barras', ''),
            'archivo': corte.get('archivo', ''),
            'descripcion': corte.get('descripcion', ''),
            'proyecto': corte.get('proyecto', '')
        } for corte in cortes]
        
        return jsonify({
            'success': True,
            'codigos': codigos_lista
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al listar códigos: {str(e)}'
        })

@bp.route('/api/validar_codigo_corte', methods=['POST'])
def validar_codigo_corte():
    """Validar si un código de corte tiene archivo Excel asociado"""
    try:
        data = request.get_json()
        codigo_corte = data.get('codigo_corte', '').strip().upper()
        
        if not codigo_corte:
            return jsonify({
                'success': False,
                'message': 'Código de corte vacío'
            })
        
        codigos_file = current_app.config['CODIGOS_FILE']
        
        if not os.path.exists(codigos_file):
            return jsonify({
                'success': False,
                'tiene_excel': False,
                'mensaje': 'No hay archivos Excel registrados'
            })
        
        with open(codigos_file, 'r', encoding='utf-8') as f:
            codigos_data = json.load(f)
        
        for corte in codigos_data.get('cortes', []):
            if corte.get('codigo_barras', '').upper() == codigo_corte:
                return jsonify({
                    'success': True,
                    'tiene_excel': True,
                    'archivo': corte.get('archivo'),
                    'descripcion': corte.get('descripcion', ''),
                    'mensaje': f'✓ Asociado a: {corte.get("archivo")}'
                })
        
        return jsonify({
            'success': True,
            'tiene_excel': False,
            'mensaje': '⚠ Sin archivo Excel asociado'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al validar: {str(e)}'
        })

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
        # Generar automáticamente los grupos de etiquetas para V3 y sección Etiquetas
        generar_grupos_etiquetas_json(archivo)
        
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
            file_size = os.path.getsize(filepath)
            
            # Formatear tamaño
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            files.append({
                'nombre': filename,
                'tamano': size_str
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
# API ROUTES PARA ETIQUETAS
# ================================

@bp.route('/api/etiquetas/cargar_grupos', methods=['POST'])
def cargar_grupos_etiquetas():
    """Cargar grupos (cod.cable + elemento) de un archivo Excel para generar etiquetas"""
    try:
        data = request.get_json()
        archivo = data.get('archivo', '').strip()
        
        if not archivo:
            return jsonify({
                'success': False,
                'message': 'Archivo no especificado'
            }), 400
        
        # Primero intentar cargar desde el JSON generado automáticamente
        json_path = os.path.join(current_app.config['DATA_FOLDER'], 'grupos_etiquetas.json')
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data_json = json.load(f)
                    
                # Verificar si es el archivo correcto
                if data_json.get('archivo') == archivo:
                    return jsonify({
                        'success': True,
                        'grupos': data_json.get('grupos', []),
                        'archivo': archivo,
                        'codigo_corte': data_json.get('codigo_corte', ''),
                        'total': data_json.get('total_grupos', 0),
                        'fuente': 'cache'
                    })
            except Exception as e:
                logger.warning(f"Error al leer grupos_etiquetas.json: {str(e)}")
        
        # Si no existe el JSON o es otro archivo, generar en tiempo real
        manager = get_excel_manager()
        
        # Cargar el archivo Excel
        if not manager.cargar_excel(archivo):
            return jsonify({
                'success': False,
                'message': f'Error al cargar archivo: {archivo}'
            }), 500
        
        # Obtener TODOS los datos del Excel
        if manager.current_df is None:
            return jsonify({
                'success': False,
                'message': 'No hay datos en el archivo'
            }), 500
        
        # Convertir DataFrame a lista de diccionarios
        todos_registros = manager.current_df.to_dict('records')
        
        # Agrupar por cod.cable + elemento
        grupos_dict = agrupar_por_cod_cable_elemento(todos_registros)
        
        # Convertir a lista
        grupos_lista = []
        for clave, grupo in grupos_dict.items():
            grupos_lista.append({
                'cod_cable': grupo['cod_cable'],
                'elemento': grupo['elemento'],
                'descripcion': grupo['descripcion'],
                'seccion': grupo['seccion'],
                'longitud': grupo['longitud'],
                'num_cables': grupo['num_cables'],
                'num_terminales': grupo['num_terminales'],
                'de_terminal': grupo['de_terminal']
            })
        
        # Ordenar por cod_cable y elemento
        grupos_lista.sort(key=lambda x: (x['cod_cable'], x['elemento']))
        
        # Filtrar solo grupos con sección
        grupos_con_seccion = [g for g in grupos_lista if g.get('seccion') and str(g.get('seccion')).strip()]
        
        # Añadir numeración secuencial solo a grupos con sección
        for i, grupo in enumerate(grupos_con_seccion, start=1):
            grupo['numero_etiqueta'] = i
        
        # Obtener el código del corte desde codigos_cortes.json
        codigo_corte = ""
        try:
            codigos_path = os.path.join(current_app.config['DATA_FOLDER'], 'codigos_cortes.json')
            with open(codigos_path, 'r', encoding='utf-8') as f:
                codigos_data = json.load(f)
                for corte in codigos_data.get('cortes', []):
                    if corte.get('archivo', '').upper() == archivo.upper():
                        codigo_corte = corte.get('codigo_barras', '')
                        break
        except Exception as e:
            logger.warning(f"No se pudo obtener código de corte para {archivo}: {e}")
        
        return jsonify({
            'success': True,
            'grupos': grupos_con_seccion,
            'archivo': archivo,
            'codigo_corte': codigo_corte,
            'total': len(grupos_con_seccion),
            'fuente': 'generado'
        })
        
    except Exception as e:
        logger.error(f"Error al cargar grupos: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al cargar grupos: {str(e)}'
        }), 500

@bp.route('/api/etiquetas/buscar_por_numero', methods=['POST'])
def buscar_etiqueta_por_numero():
    """Buscar elemento por número de etiqueta para V3"""
    try:
        data = request.get_json()
        numero_etiqueta = data.get('numero_etiqueta')
        
        if not numero_etiqueta:
            return jsonify({
                'success': False,
                'message': 'Número de etiqueta es obligatorio'
            }), 400
        
        # Intentar convertir a número
        try:
            numero_etiqueta = int(numero_etiqueta)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Número de etiqueta debe ser un número entero'
            }), 400
        
        # Leer archivo JSON de grupos de etiquetas
        json_path = os.path.join(current_app.config['DATA_FOLDER'], 'grupos_etiquetas.json')
        
        if not os.path.exists(json_path):
            return jsonify({
                'success': False,
                'message': 'No se encontraron etiquetas generadas. Por favor, genera etiquetas desde el Admin primero.'
            }), 404
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        # Buscar el grupo con ese número
        grupos = data_json.get('grupos', [])
        grupo_encontrado = None
        
        for grupo in grupos:
            if grupo.get('numero_etiqueta') == numero_etiqueta:
                grupo_encontrado = grupo
                break
        
        if not grupo_encontrado:
            return jsonify({
                'success': False,
                'message': f'No se encontró la etiqueta número {numero_etiqueta}'
            }), 404
        
        return jsonify({
            'success': True,
            'grupo': grupo_encontrado,
            'mensaje': f'Etiqueta #{numero_etiqueta}: {grupo_encontrado["elemento"]} - Cable {grupo_encontrado["cod_cable"]}'
        })
        
    except Exception as e:
        logger.error(f"Error al buscar por número de etiqueta: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al buscar etiqueta: {str(e)}'
        }), 500

@bp.route('/api/etiquetas/grupos_json', methods=['GET'])
def get_grupos_etiquetas_json():
    """Obtener el JSON de grupos de etiquetas para V3"""
    try:
        json_path = os.path.join(current_app.config['DATA_FOLDER'], 'grupos_etiquetas.json')
        
        if not os.path.exists(json_path):
            return jsonify({
                'success': False,
                'message': 'Archivo de etiquetas no encontrado',
                'grupos': []
            }), 404
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data_json = json.load(f)
        
        return jsonify({
            'success': True,
            'grupos': data_json.get('grupos', []),
            'archivo': data_json.get('archivo', ''),
            'total_grupos': data_json.get('total_grupos', 0)
        })
        
    except Exception as e:
        logger.error(f"Error al obtener grupos de etiquetas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'grupos': []
        }), 500

@bp.route('/api/etiquetas/grupos_bono/<nombre_bono>', methods=['GET'])
def get_grupos_etiquetas_bono(nombre_bono):
    """Obtener etiquetas de TODOS los archivos de un bono para V3"""
    try:
        bono = proyecto_manager.obtener_bono(nombre_bono)
        if not bono:
            return jsonify({
                'success': False,
                'message': 'Bono no encontrado',
                'grupos': []
            }), 404
        
        todos_los_grupos = []
        
        # Iterar por cada carro/archivo del bono
        for carro_info in bono.get('carros', []):
            archivo = carro_info.get('archivo_excel')
            if not archivo:
                continue
            
            # Cargar o generar las etiquetas de este archivo
            manager = ExcelManager(
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['CODIGOS_FILE']
            )
            
            if not manager.cargar_excel(archivo):
                logger.warning(f"No se pudo cargar archivo {archivo}")
                continue
            
            # Convertir DataFrame a registros
            registros = manager.current_df.to_dict('records')
            
            # Agrupar por cod.cable + elemento
            grupos_dict = agrupar_por_cod_cable_elemento(registros)
            
            # Convertir a lista
            grupos_lista = []
            for clave, grupo in grupos_dict.items():
                grupos_lista.append({
                    'cod_cable': grupo['cod_cable'],
                    'elemento': grupo['elemento'],
                    'descripcion': grupo['descripcion'],
                    'seccion': grupo['seccion'],
                    'longitud': grupo['longitud'],
                    'de_terminal': grupo['de_terminal'],
                    'num_cables': grupo['num_cables'],
                    'num_terminales': grupo['num_terminales'],
                    'archivo': archivo  # Agregar referencia al archivo
                })
            
            # Ordenar por cod_cable y elemento
            grupos_lista.sort(key=lambda x: (x['cod_cable'], x['elemento']))
            
            # Filtrar solo grupos con sección
            grupos_con_seccion = [g for g in grupos_lista if g.get('seccion') and str(g.get('seccion')).strip()]
            
            # Añadir numeración secuencial PROPIA de este archivo (empezar desde 1)
            for i, grupo in enumerate(grupos_con_seccion, start=1):
                grupo['numero_etiqueta'] = i
            
            # Agregar a la lista total
            todos_los_grupos.extend(grupos_con_seccion)
        
        return jsonify({
            'success': True,
            'grupos': todos_los_grupos,
            'total_grupos': len(todos_los_grupos),
            'archivos_procesados': len(bono.get('carros', []))
        })
        
    except Exception as e:
        logger.error(f"Error al obtener grupos del bono {nombre_bono}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'grupos': []
        }), 500

@bp.route('/api/etiquetas/generar_html', methods=['POST'])
def generar_etiquetas_html():
    """Generar HTML de etiquetas para imprimir en impresora normal"""
    try:
        data = request.get_json()
        archivo = data.get('archivo', '').strip()
        grupos = data.get('grupos', [])
        codigo_corte = data.get('codigo_corte', '').strip()
        
        if not archivo or not grupos:
            return jsonify({
                'success': False,
                'message': 'Faltan datos requeridos (archivo, grupos)'
            }), 400
        
        # Generar HTML para imprimir
        html = generar_html_etiquetas_impresion(grupos, archivo, codigo_corte)
        
        return jsonify({
            'success': True,
            'html': html,
            'total_etiquetas': len(grupos)
        })
        
    except Exception as e:
        logger.error(f"Error al generar HTML de etiquetas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al generar HTML: {str(e)}'
        }), 500


def agrupar_por_cod_cable_elemento(registros):
    """
    Agrupar registros por Cod.cable + De Elemento
    Similar a agrupar_por_cable_elemento pero sin filtrar por terminal
    """
    grupos = {}
    
    for row in registros:
        cod_cable = row.get('Cod. cable', 'Sin código')
        de_elemento = row.get('De Elemento', 'Sin elemento')
        
        # Saltar si son valores vacíos
        if pd.isna(cod_cable) or pd.isna(de_elemento):
            continue
        
        cod_cable = str(cod_cable).strip()
        de_elemento = str(de_elemento).strip()
        
        if not cod_cable or not de_elemento:
            continue
        
        clave = f"{cod_cable}|{de_elemento}"
        
        if clave not in grupos:
            grupos[clave] = {
                'cod_cable': cod_cable,
                'elemento': de_elemento,
                'descripcion': str(row.get('Descripción Cable', '')).strip() if not pd.isna(row.get('Descripción Cable')) else '',
                'seccion': str(row.get('Sección', '')).strip() if not pd.isna(row.get('Sección')) else '',
                'longitud': row.get('Longitud', '') if not pd.isna(row.get('Longitud')) else '',
                'de_terminal': str(row.get('De Terminal', '')).strip() if not pd.isna(row.get('De Terminal')) else '',
                'cables_lista': [],
                'num_terminales': 0
            }
        
        # Agregar cable
        cable_marca = str(row.get('Cable / Marca', '')).strip()
        grupos[clave]['cables_lista'].append(cable_marca)
        
        # Contar terminales
        de_terminal = str(row.get('De Terminal', '')).strip().upper() if not pd.isna(row.get('De Terminal')) else ''
        para_terminal = str(row.get('Para Terminal', '')).strip().upper() if not pd.isna(row.get('Para Terminal')) else ''
        
        if de_terminal and de_terminal != 'S/T':
            grupos[clave]['num_terminales'] += 1
        if para_terminal and para_terminal != 'S/T':
            grupos[clave]['num_terminales'] += 1
    
    # Calcular num_cables
    for grupo in grupos.values():
        grupo['num_cables'] = len(grupo['cables_lista'])
        del grupo['cables_lista']
    
    return grupos


def generar_grupos_etiquetas_json(archivo):
    """
    Generar grupos de etiquetas y guardarlos en JSON para uso compartido entre Etiquetas y V3.
    Se llama automáticamente al agregar un nuevo corte.
    """
    try:
        manager = ExcelManager(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['CODIGOS_FILE']
        )
        
        # Cargar el archivo Excel
        if not manager.cargar_excel(archivo):
            logger.error(f"Error al cargar archivo {archivo} para generar grupos")
            return False
        
        # Obtener el código del corte desde codigos_cortes.json
        codigo_corte = ""
        try:
            codigos_path = os.path.join(current_app.config['DATA_FOLDER'], 'codigos_cortes.json')
            with open(codigos_path, 'r', encoding='utf-8') as f:
                codigos_data = json.load(f)
                for corte in codigos_data.get('cortes', []):
                    if corte.get('archivo', '').upper() == archivo.upper():
                        codigo_corte = corte.get('codigo_barras', '')
                        break
        except Exception as e:
            logger.warning(f"No se pudo obtener código de corte para {archivo}: {e}")
        
        # Convertir DataFrame a lista de diccionarios
        todos_registros = manager.current_df.to_dict('records')
        
        # Obtener grupos usando la función existente
        grupos_dict = agrupar_por_cod_cable_elemento(todos_registros)
        
        # Convertir a lista y ordenar
        grupos_lista = []
        for clave, grupo in grupos_dict.items():
            grupos_lista.append({
                'cod_cable': grupo['cod_cable'],
                'elemento': grupo['elemento'],
                'descripcion': grupo['descripcion'],
                'seccion': grupo['seccion'],
                'longitud': grupo['longitud'],
                'de_terminal': grupo['de_terminal'],
                'num_cables': grupo['num_cables'],
                'num_terminales': grupo['num_terminales']
            })
        
        # Ordenar por cod_cable y elemento
        grupos_lista.sort(key=lambda x: (x['cod_cable'], x['elemento']))
        
        # Filtrar solo grupos con sección
        grupos_con_seccion = [g for g in grupos_lista if g.get('seccion') and str(g.get('seccion')).strip()]
        
        # Añadir numeración secuencial solo a grupos con sección
        for i, grupo in enumerate(grupos_con_seccion, start=1):
            grupo['numero_etiqueta'] = i
        
        # Guardar en archivo JSON compartido
        json_path = os.path.join(current_app.config['DATA_FOLDER'], 'grupos_etiquetas.json')
        data_to_save = {
            'archivo': archivo,
            'codigo_corte': codigo_corte,
            'fecha_generacion': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_grupos': len(grupos_con_seccion),
            'grupos': grupos_con_seccion
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Grupos de etiquetas generados: {len(grupos_con_seccion)} grupos para {archivo}")
        return True
        
    except Exception as e:
        logger.error(f"Error al generar grupos de etiquetas: {str(e)}")
        return False


def generar_html_etiquetas_impresion(grupos, archivo, codigo_corte=""):
    """
    Generar HTML con CSS para imprimir etiquetas en impresora normal
    Formato: 3 columnas de etiquetas por página
    """
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Etiquetas - {archivo}</title>
    <style>
        @media print {{
            @page {{
                size: A4 landscape;
                margin: 10mm 10mm 10mm 8mm;
            }}
            body {{
                margin: 0;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
            .page-break {{
                page-break-after: always;
                page-break-inside: avoid;
                break-after: page;
            }}
            .etiquetas-container {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 10px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 5px;
        }}
        
        .no-print {{
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .etiquetas-container {{
            display: grid;
            grid-template-columns: repeat(13, 21.3mm);
            grid-template-rows: repeat(5, 38mm);
            gap: 0;
            width: fit-content;
            margin: 0 auto;
            justify-content: center;
        }}
        
        .etiqueta {{
            width: 21.3mm;
            height: 38mm;
            border: 2px solid #333;
            padding: 0;
            background: white;
            box-sizing: border-box;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            break-inside: avoid;
            page-break-inside: avoid;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            color-adjust: exact;
        }}
        
        .etiqueta-top {{
            height: 19mm;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-bottom: 2px solid #0ea5e9;
            padding: 2mm 1mm;
            gap: 1mm;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            color-adjust: exact;
        }}
        
        .etiqueta-numero {{
            background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
            color: white;
            font-size: 16pt;
            font-weight: bold;
            padding: 2mm 4mm;
            border-radius: 4mm;
            min-width: 10mm;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            color-adjust: exact;
        }}
        
        .etiqueta-elemento {{
            font-size: 9pt;
            font-weight: bold;
            color: #1e40af;
            text-align: center;
            line-height: 1.1;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            word-break: break-word;
        }}
        
        .etiqueta-bottom {{
            height: 19mm;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: white;
            padding: 2mm 1mm;
            gap: 0.5mm;
        }}
        
        .etiqueta-info-line {{
            font-size: 7pt;
            text-align: center;
            line-height: 1.2;
            width: 100%;
        }}
        
        .etiqueta-corte {{
            font-weight: bold;
            color: #059669;
            font-size: 7pt;
            background: #d1fae5;
            padding: 0.5mm 2mm;
            border-radius: 2mm;
            margin-bottom: 0.5mm;
        }}
        
        .etiqueta-cable {{
            font-weight: bold;
            color: #2563eb;
            font-size: 8pt;
        }}
        
        .etiqueta-descripcion {{
            color: #334155;
            font-size: 7pt;
        }}
        
        .etiqueta-seccion {{
            color: #64748b;
            font-size: 7pt;
            background: #f1f5f9;
            padding: 0.5mm 2mm;
            border-radius: 2mm;
            margin-top: 0.5mm;
        }}
        
        /* Estilos para vista previa en pantalla */
        @media screen {{
            .etiquetas-container {{
                transform: scale(1.5);
                transform-origin: top left;
                margin-bottom: 50px;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 5px;">
            🖨️ Imprimir Etiquetas
        </button>
        <button onclick="window.close()" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #f44336; color: white; border: none; border-radius: 5px; margin-left: 10px;">
            ✕ Cerrar
        </button>
        <p style="margin-top: 10px; color: #666;">Formato: A4 Apaisado | 13 columnas × 5 filas | 21mm × 38mm por etiqueta</p>
    </div>
    
    <div class="header no-print">
        <h2>Etiquetas de Grupos - {archivo}</h2>
    </div>
    
    <div class="etiquetas-container">
"""
    
    # Filtrar grupos que tengan sección
    grupos_con_seccion = [g for g in grupos if g.get('seccion') and str(g.get('seccion')).strip()]
    
    # Añadir información del número de etiquetas filtradas al HTML
    html = html.replace('<h2>Etiquetas de Grupos - {archivo}</h2>', 
                       f'<h2>Etiquetas de Grupos - {{archivo}}</h2><p style="margin-top: 10px; color: #666;">Total de etiquetas con sección: {len(grupos_con_seccion)}</p>')
    
    # Generar etiquetas (hasta 65 por página: 13 columnas x 5 filas)
    for i, grupo in enumerate(grupos_con_seccion):
        numero = i + 1  # Numeración secuencial solo para grupos con sección
        
        # Truncar textos para que quepan en etiquetas pequeñas
        elemento = grupo['elemento'][:15] if len(grupo['elemento']) > 15 else grupo['elemento']
        cod_cable = grupo['cod_cable'][:12] if len(grupo['cod_cable']) > 12 else grupo['cod_cable']
        seccion = grupo.get('seccion', '')[:10] if grupo.get('seccion') else ''
        descripcion = grupo.get('descripcion', '')[:18] if grupo.get('descripcion') else ''
        
        html += f"""
        <div class="etiqueta">
            <div class="etiqueta-top">
                <div class="etiqueta-numero">{numero}</div>
                <div class="etiqueta-elemento">{elemento}</div>
            </div>
            <div class="etiqueta-bottom">"""
        
        # Añadir código de corte si existe
        if codigo_corte:
            html += f"""
                <div class="etiqueta-info-line etiqueta-corte">{codigo_corte}</div>"""
        
        html += f"""
                <div class="etiqueta-info-line etiqueta-cable">{cod_cable}</div>"""
        
        if seccion:
            html += f"""
                <div class="etiqueta-info-line etiqueta-seccion">{seccion}</div>"""
        
        html += """
            </div>
        </div>
"""
        
        # Salto de página cada 65 etiquetas (13 columnas x 5 filas)
        if (i + 1) % 65 == 0 and (i + 1) < len(grupos_con_seccion):
            html += """
    </div>
    <div class="page-break"></div>
    <div class="etiquetas-container">
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    return html

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
        # Obtener terminales unicos de todos los proyectos registrados
        codigos_file = current_app.config['CODIGOS_FILE']
        if not os.path.exists(codigos_file):
            return jsonify({'success': False, 'message': 'No hay archivos Excel asociados a codigos de barras'}), 400

        with open(codigos_file, 'r', encoding='utf-8') as f:
            codigos_data = json.load(f)

        cortes = codigos_data.get('cortes', [])
        if not cortes:
            return jsonify({'success': False, 'message': 'No hay archivos Excel asociados a codigos de barras'}), 400

        cache_ttl = current_app.config.get('TERMINALES_CACHE_TTL', 300)
        now = time.time()
        signature = _build_terminales_signature(
            codigos_file,
            current_app.config['UPLOAD_FOLDER'],
            cortes
        )

        cache_valid = (
            terminales_cache['terminales'] is not None and
            terminales_cache['signature'] == signature and
            (cache_ttl <= 0 or (now - terminales_cache['timestamp']) <= cache_ttl)
        )

        if cache_valid:
            terminales_sistema = set(terminales_cache['terminales'])
            archivos_con_error = terminales_cache.get('archivos_con_error') or []
        else:
            terminales_sistema, archivos_con_error = _build_terminales_globales(
                current_app.config['UPLOAD_FOLDER'],
                codigos_file,
                current_app.config['DEFAULT_SHEET'],
                cortes
            )
            terminales_cache['terminales'] = sorted(list(terminales_sistema))
            terminales_cache['archivos_con_error'] = archivos_con_error
            terminales_cache['signature'] = signature
            terminales_cache['timestamp'] = now

        if not terminales_sistema:
            return jsonify({'success': False, 'message': 'No se encontraron terminales en los archivos'}), 400

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
        for terminal in sorted(list(terminales_sistema)):
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
            'sin_asignar': sin_asignar,
            'archivos_con_error': archivos_con_error
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

@bp.route('/api/carros/asignar-orden', methods=['POST'])
def asignar_orden_carro():
    """Asignar una orden de producción directamente a un carro"""
    try:
        datos = request.json
        numero_carro = datos.get('numero_carro')
        proyecto_nombre = datos.get('proyecto_nombre')
        archivo = datos.get('archivo')
        
        if not numero_carro or not proyecto_nombre or not archivo:
            return jsonify({
                'success': False, 
                'message': 'numero_carro, proyecto_nombre y archivo son requeridos'
            })
        
        # Crear proyecto temporal y asignar al carro
        proyecto_manager.crear_proyecto_y_asignar_carro(
            nombre=proyecto_nombre,
            archivo=archivo,
            numero_carro=numero_carro
        )
        
        return jsonify({
            'success': True, 
            'message': f'Orden asignada al carro {numero_carro}'
        })
        
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

@bp.route('/api/bonos/<nombre_bono>/terminales-disponibles', methods=['GET'])
def obtener_terminales_disponibles_bono(nombre_bono):
    """Obtener terminales que tienen datos en los archivos del bono"""
    try:
        bono = proyecto_manager.obtener_bono(nombre_bono)
        if not bono:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
        
        # Obtener todos los archivos del bono
        carros = bono.get('carros', [])
        terminales_con_datos = set()
        
        # Para cada archivo, obtener los terminales únicos
        for carro in carros:
            archivo = carro.get('archivo_excel')
            if not archivo:
                continue
            
            # Cargar el archivo y obtener terminales
            manager = ExcelManager(
                current_app.config['UPLOAD_FOLDER'],
                current_app.config['CODIGOS_FILE']
            )
            
            if manager.cargar_excel(archivo):
                # Convertir a registros
                registros = manager.current_df.to_dict('records')
                
                # Extraer terminales únicos
                for row in registros:
                    de_terminal = str(row.get('De Terminal', '')).strip().upper()
                    para_terminal = str(row.get('Para Terminal', '')).strip().upper()
                    
                    # Solo agregar si no es vacío y no es S/T
                    if de_terminal and de_terminal != 'S/T' and not pd.isna(row.get('De Terminal')):
                        terminales_con_datos.add(de_terminal)
                    if para_terminal and para_terminal != 'S/T' and not pd.isna(row.get('Para Terminal')):
                        terminales_con_datos.add(para_terminal)
        
        return jsonify({
            'success': True,
            'terminales': sorted(list(terminales_con_datos))
        })
            
    except Exception as e:
        logger.error(f"Error al obtener terminales disponibles: {e}")
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

@bp.route('/api/bonos/<nombre_bono>/reset-progreso', methods=['POST'])
def resetear_progreso_bono(nombre_bono):
    """Resetear el progreso de un bono"""
    try:
        exito = proyecto_manager.resetear_progreso_bono(nombre_bono)
        
        if exito:
            return jsonify({'success': True, 'message': 'Progreso del bono reseteado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'Bono no encontrado'})
            
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


@bp.route('/api/comprobar_actualizaciones', methods=['GET'])
def comprobar_actualizaciones():
    """Comprobar si hay actualizaciones disponibles en GitHub"""
    try:
        import subprocess
        
        # Obtener el hash del commit actual
        result_local = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_local = result_local.stdout.strip()
        
        # Obtener el hash del commit remoto
        subprocess.run(['git', 'fetch', 'origin', 'main'], check=True, capture_output=True)
        result_remoto = subprocess.run(
            ['git', 'rev-parse', 'origin/main'],
            capture_output=True,
            text=True,
            check=True
        )
        commit_remoto = result_remoto.stdout.strip()
        
        # Verificar si hay diferencias
        hay_actualizaciones = commit_local != commit_remoto
        
        # Obtener información del último commit remoto si hay actualizaciones
        mensaje_commit = ""
        if hay_actualizaciones:
            result_mensaje = subprocess.run(
                ['git', 'log', 'origin/main', '-1', '--pretty=%B'],
                capture_output=True,
                text=True,
                check=True
            )
            mensaje_commit = result_mensaje.stdout.strip()
        
        return jsonify({
            'success': True,
            'hay_actualizaciones': hay_actualizaciones,
            'commit_local': commit_local[:7],
            'commit_remoto': commit_remoto[:7],
            'mensaje_ultimo_commit': mensaje_commit
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': f'Error al comprobar actualizaciones: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error inesperado: {str(e)}'
        })


@bp.route('/api/actualizar_sistema', methods=['POST'])
def actualizar_sistema():
    """Actualizar el sistema desde GitHub y reiniciar el servicio"""
    try:
        import subprocess
        import sys
        
        # Guardar cambios locales en stash (por si acaso)
        subprocess.run(
            ['git', 'stash'],
            capture_output=True,
            text=True
        )
        
        # Resetear cambios locales para evitar conflictos
        subprocess.run(
            ['git', 'reset', '--hard', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Hacer git pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout + result.stderr
        
        # Verificar si hubo cambios
        if 'Already up to date' in output or 'Ya está actualizado' in output:
            return jsonify({
                'success': True,
                'actualizado': False,
                'message': 'El sistema ya está actualizado',
                'output': output
            })
        
        # Si hubo cambios, instalar dependencias por si acaso
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            check=True
        )
        
        # Reiniciar el servicio (solo en Linux/Raspberry)
        if sys.platform.startswith('linux'):
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'engastado.service'],
                check=True
            )
            mensaje = 'Sistema actualizado correctamente. El servicio se está reiniciando...'
        else:
            mensaje = 'Sistema actualizado correctamente. Reinicia manualmente la aplicación.'
        
        return jsonify({
            'success': True,
            'actualizado': True,
            'message': mensaje,
            'output': output
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': f'Error al actualizar: {e.stderr if e.stderr else str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error inesperado: {str(e)}'
        })


# ================================
# API: Registro de Órdenes
# ================================

@bp.route('/api/ordenes/crear', methods=['POST'])
def crear_orden():
    """Crear una nueva orden de producción"""
    try:
        import uuid
        from datetime import datetime
        
        data = request.get_json()
        ordenes_file = os.path.join(current_app.config['DATA_FOLDER'], 'ordenes_produccion.json')
        codigos_file = current_app.config['CODIGOS_FILE']
        
        # Leer órdenes existentes
        if os.path.exists(ordenes_file):
            with open(ordenes_file, 'r', encoding='utf-8') as f:
                ordenes_data = json.load(f)
        else:
            ordenes_data = {'ordenes': []}
        
        # Buscar archivo Excel asociado al código de corte
        archivo_excel = None
        descripcion_corte = None
        codigo_corte = data.get('codigo_corte', '')
        
        if os.path.exists(codigos_file):
            with open(codigos_file, 'r', encoding='utf-8') as f:
                codigos_data = json.load(f)
            
            for corte in codigos_data.get('cortes', []):
                if corte.get('codigo_barras', '').upper() == codigo_corte.upper():
                    archivo_excel = corte.get('archivo')
                    descripcion_corte = corte.get('descripcion')
                    break
        
        # Crear nueva orden
        nueva_orden = {
            'id': str(uuid.uuid4()),
            'codigo_corte': codigo_corte,
            'archivo_excel': archivo_excel,
            'numero': data.get('numero'),
            'proyecto': data.get('proyecto', descripcion_corte or ''),
            'descripcion': data.get('descripcion', ''),
            'cantidad': data.get('cantidad'),
            'fecha_entrega': data.get('fecha_entrega'),
            'prioridad': data.get('prioridad'),
            'estado': 'pendiente',
            'fecha_creacion': datetime.now().isoformat()
        }
        
        ordenes_data['ordenes'].append(nueva_orden)
        
        # Guardar
        with open(ordenes_file, 'w', encoding='utf-8') as f:
            json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Orden creada correctamente',
            'orden': nueva_orden,
            'archivo_encontrado': archivo_excel is not None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al crear la orden: {str(e)}'
        })


@bp.route('/api/ordenes/listar', methods=['GET'])
def listar_ordenes():
    """Listar todas las órdenes ordenadas por fecha de liberación (más antigua primero)"""
    try:
        ordenes_file = os.path.join(current_app.config['DATA_FOLDER'], 'ordenes_produccion.json')
        codigos_file = current_app.config['CODIGOS_FILE']
        
        if os.path.exists(ordenes_file):
            with open(ordenes_file, 'r', encoding='utf-8') as f:
                ordenes_data = json.load(f)
            ordenes = ordenes_data.get('ordenes', [])
            
            # Cargar códigos de corte
            codigos_map = {}
            if os.path.exists(codigos_file):
                with open(codigos_file, 'r', encoding='utf-8') as f:
                    codigos_data = json.load(f)
                for corte in codigos_data.get('cortes', []):
                    codigos_map[corte.get('codigo_barras', '').upper()] = {
                        'archivo': corte.get('archivo'),
                        'descripcion': corte.get('descripcion', '')
                    }
            
            # Actualizar órdenes sin archivo_excel asociado
            actualizado = False
            for orden in ordenes:
                codigo_corte = orden.get('codigo_corte', '').upper()
                # Si no tiene archivo_excel o es null, buscar asociación
                if not orden.get('archivo_excel') and codigo_corte in codigos_map:
                    orden['archivo_excel'] = codigos_map[codigo_corte]['archivo']
                    actualizado = True
            
            # Guardar cambios si hubo actualizaciones
            if actualizado:
                with open(ordenes_file, 'w', encoding='utf-8') as f:
                    json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
            
            # Ordenar por fecha de entrega (más antigua primero)
            ordenes_ordenadas = sorted(
                ordenes, 
                key=lambda x: x.get('fecha_entrega', '9999-12-31')
            )
        else:
            ordenes_ordenadas = []
        
        return jsonify({
            'success': True,
            'ordenes': ordenes_ordenadas
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al listar órdenes: {str(e)}'
        })


@bp.route('/api/ordenes/eliminar/<orden_id>', methods=['DELETE'])
def eliminar_orden(orden_id):
    """Eliminar una orden"""
    try:
        ordenes_file = os.path.join(current_app.config['DATA_FOLDER'], 'ordenes_produccion.json')
        
        if os.path.exists(ordenes_file):
            with open(ordenes_file, 'r', encoding='utf-8') as f:
                ordenes_data = json.load(f)
        else:
            return jsonify({'success': False, 'message': 'No hay órdenes registradas'})
        
        # Filtrar la orden a eliminar
        ordenes_data['ordenes'] = [o for o in ordenes_data['ordenes'] if o['id'] != orden_id]
        
        # Guardar
        with open(ordenes_file, 'w', encoding='utf-8') as f:
            json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Orden eliminada correctamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al eliminar la orden: {str(e)}'
        })


@bp.route('/api/ordenes/actualizar/<orden_id>', methods=['PUT'])
def actualizar_orden(orden_id):
    """Actualizar una orden existente"""
    try:
        data = request.get_json()
        ordenes_file = os.path.join(current_app.config['DATA_FOLDER'], 'ordenes_produccion.json')
        
        if os.path.exists(ordenes_file):
            with open(ordenes_file, 'r', encoding='utf-8') as f:
                ordenes_data = json.load(f)
        else:
            return jsonify({'success': False, 'message': 'No hay órdenes registradas'})
        
        # Buscar la orden
        orden_encontrada = False
        for orden in ordenes_data['ordenes']:
            if orden['id'] == orden_id:
                # Actualizar campos
                orden['codigo_corte'] = data.get('codigo_corte', orden.get('codigo_corte', ''))
                orden['numero'] = data.get('numero', orden.get('numero'))
                orden['proyecto'] = data.get('proyecto', orden.get('proyecto', ''))
                orden['descripcion'] = data.get('descripcion', orden.get('descripcion', ''))
                orden['cantidad'] = data.get('cantidad', orden.get('cantidad'))
                orden['fecha_entrega'] = data.get('fecha_entrega', orden.get('fecha_entrega'))
                orden['prioridad'] = data.get('prioridad', orden.get('prioridad'))
                # El estado se puede actualizar opcionalmente
                if 'estado' in data:
                    orden['estado'] = data.get('estado')
                orden_encontrada = True
                break
        
        if not orden_encontrada:
            return jsonify({'success': False, 'message': 'Orden no encontrada'})
        
        # Guardar
        with open(ordenes_file, 'w', encoding='utf-8') as f:
            json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Orden actualizada correctamente'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al actualizar la orden: {str(e)}'
        })


# ============================================================================
# ENDPOINTS DE IMPRESORA ZEBRA
# ============================================================================

@bp.route('/api/printer/status', methods=['GET'])
def printer_status():
    """
    Obtener estado de la impresora Zebra
    
    Returns:
        JSON con información de estado:
        - available: bool
        - status: str (idle/printing/offline/simulation/error)
        - mode: str (Producción/Simulación)
        - message: str
        - has_paper: bool (solo en producción)
        - simulated_labels: int (solo en simulación)
    """
    try:
        from app.printer_manager import PrinterManager
        from config import Config
        
        printer = PrinterManager(Config)
        status = printer.get_printer_status()
        
        return jsonify({
            'success': True,
            **status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estado: {str(e)}'
        })


@bp.route('/api/printer/pending', methods=['GET'])
def printer_pending_labels():
    """
    Obtener lista de etiquetas pendientes de impresión
    
    Returns:
        JSON con lista de etiquetas que fallaron al imprimir
    """
    try:
        from app.printer_manager import PrinterManager
        from config import Config
        
        printer = PrinterManager(Config)
        pendientes = printer.get_pending_labels()
        
        return jsonify({
            'success': True,
            'pendientes': pendientes,
            'total': len(pendientes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener pendientes: {str(e)}'
        })


@bp.route('/api/printer/reprint', methods=['POST'])
def printer_reprint():
    """
    Reimprimir una etiqueta manualmente
    
    Body JSON:
        {
            "tipo": "asignacion" | "finalizacion" | "test",
            "bono": "nombre_bono" (opcional),
            "carro": 1-6,
            "orden": "numero_orden" (para asignación),
            "codigo_corte": "codigo" (para asignación),
            "proyecto": "nombre_proyecto" (opcional),
            "operario": "Terminal X" (para finalización),
            "terminales_completados": int (para finalización),
            "terminales_totales": int (para finalización)
        }
    
    Returns:
        JSON con resultado de la impresión
    """
    try:
        from app.printer_manager import PrinterManager
        from app.zpl_templates import ZPLTemplates
        from config import Config
        
        data = request.json
        tipo = data.get('tipo')
        
        if not tipo:
            return jsonify({
                'success': False,
                'message': 'Falta especificar el tipo de etiqueta'
            })
        
        printer = PrinterManager(Config)
        zpl = None
        metadata = {'tipo': tipo}
        
        if tipo == 'test':
            zpl = ZPLTemplates.etiqueta_test()
            metadata['descripcion'] = 'Etiqueta de prueba'
            
        elif tipo == 'asignacion':
            carro = data.get('carro')
            orden = data.get('orden')
            codigo_corte = data.get('codigo_corte')
            proyecto = data.get('proyecto', '')
            cantidad_terminales = data.get('cantidad_terminales', 0)
            
            if not all([carro, orden, codigo_corte]):
                return jsonify({
                    'success': False,
                    'message': 'Faltan datos para etiqueta de asignación (carro, orden, codigo_corte)'
                })
            
            zpl = ZPLTemplates.etiqueta_asignacion_carro(
                carro=int(carro),
                orden=orden,
                codigo_corte=codigo_corte,
                proyecto=proyecto,
                cantidad_terminales=int(cantidad_terminales)
            )
            
            metadata.update({
                'bono': data.get('bono'),
                'carro': carro,
                'orden': orden
            })
            
        elif tipo == 'finalizacion':
            carro = data.get('carro')
            nombre_bono = data.get('bono')
            operario = data.get('operario')
            terminales_completados = data.get('terminales_completados', 0)
            terminales_totales = data.get('terminales_totales', 0)
            proyecto = data.get('proyecto')
            
            if not all([carro, nombre_bono, operario]):
                return jsonify({
                    'success': False,
                    'message': 'Faltan datos para etiqueta de finalización (carro, bono, operario)'
                })
            
            zpl = ZPLTemplates.etiqueta_finalizacion_carro(
                carro=int(carro),
                nombre_bono=nombre_bono,
                operario=operario,
                terminales_completados=int(terminales_completados),
                terminales_totales=int(terminales_totales),
                proyecto=proyecto
            )
            
            metadata.update({
                'bono': nombre_bono,
                'carro': carro,
                'operario': operario
            })
            
        else:
            return jsonify({
                'success': False,
                'message': f'Tipo de etiqueta no válido: {tipo}'
            })
        
        # Imprimir
        resultado = printer.print_zpl(zpl, metadata)
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al reimprimir: {str(e)}'
        })


@bp.route('/api/printer/retry-pending', methods=['POST'])
def printer_retry_pending():
    """
    Reintentar imprimir todas las etiquetas pendientes
    
    Returns:
        JSON con resumen de resultados
    """
    try:
        from app.printer_manager import PrinterManager
        from config import Config
        
        printer = PrinterManager(Config)
        resultado = printer.retry_pending_labels()
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al reintentar pendientes: {str(e)}'
        })


@bp.route('/api/printer/simulated-labels', methods=['GET'])
def printer_simulated_labels():
    """
    Obtener lista de etiquetas simuladas (archivos ZPL guardados)
    
    Returns:
        JSON con lista de archivos de simulación
    """
    try:
        from config import Config
        import os
        from datetime import datetime
        
        sim_dir = Config.PRINTER_SIMULATION_DIR
        
        if not os.path.exists(sim_dir):
            return jsonify({
                'success': True,
                'archivos': [],
                'total': 0
            })
        
        archivos = []
        for filename in os.listdir(sim_dir):
            if filename.endswith('.zpl'):
                filepath = os.path.join(sim_dir, filename)
                stat = os.stat(filepath)
                
                archivos.append({
                    'nombre': filename,
                    'ruta': filepath,
                    'tamano': stat.st_size,
                    'fecha': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Ordenar por fecha descendente
        archivos.sort(key=lambda x: x['fecha'], reverse=True)
        
        return jsonify({
            'success': True,
            'archivos': archivos,
            'total': len(archivos),
            'directorio': sim_dir
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al listar etiquetas simuladas: {str(e)}'
        })


@bp.route('/api/printer/clear-simulated', methods=['POST'])
def printer_clear_simulated():
    """
    Limpiar todas las etiquetas simuladas
    
    Returns:
        JSON con resultado de la operación
    """
    try:
        from app.printer_manager import PrinterManager
        from config import Config
        
        printer = PrinterManager(Config)
        resultado = printer.clear_simulated_labels()
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al limpiar etiquetas: {str(e)}'
        })

