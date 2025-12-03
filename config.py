"""
Configuración de la aplicación Flask
"""
import os

class Config:
    # Clave secreta para sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2025'
    
    # Rutas de directorios
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DATA_FOLDER = os.path.join(BASE_DIR, 'data')  # Alias para compatibilidad
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'cortes')
    
    # Archivo de mapeo de códigos de barras
    CODIGOS_FILE = os.path.join(DATA_DIR, 'codigos_cortes.json')
    
    # Configuración de uploads
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB máximo
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # Configuración de Flask
    DEBUG = True
    
    # Hoja de Excel a usar por defecto
    DEFAULT_SHEET = 'Format'
    
    # Sistema de carros y proyectos
    PROYECTOS_FILE = os.path.join(DATA_DIR, 'proyectos_carros.json')
    BONOS_DIR = os.path.join(DATA_DIR, 'bonos')
    NUM_CARROS = 6  # Número de carros disponibles
