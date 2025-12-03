"""
Inicialización de la aplicación Flask
"""
from flask import Flask
import os

def create_app():
    # Obtener el directorio raíz del proyecto
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # Crear app con rutas explícitas a templates y static
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    
    app.config.from_object('config.Config')
    
    # Crear carpetas necesarias si no existen
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    
    # Registrar blueprints
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app
