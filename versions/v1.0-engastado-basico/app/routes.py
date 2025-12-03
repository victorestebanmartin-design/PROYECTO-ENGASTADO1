"""
Rutas y endpoints de la aplicación
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for
from werkzeug.utils import secure_filename
import os
from app.excel_manager import ExcelManager

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
def index():
    """Página principal - Operación de engastado"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('index.html', cortes=cortes)

@bp.route('/admin')
def admin():
    """Página de administración de archivos"""
    manager = get_excel_manager()
    cortes = manager.get_cortes()
    return render_template('admin.html', cortes=cortes)

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
