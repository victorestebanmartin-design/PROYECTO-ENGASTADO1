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
    
    # Configuración de impresora Zebra GK420T
    PRINTER_ENABLED = os.environ.get('PRINTER_ENABLED', 'True').lower() == 'true'
    PRINTER_NAME = os.environ.get('PRINTER_NAME', 'ZebraGK420T')
    PRINTER_SIMULATION_MODE = os.environ.get('PRINTER_SIMULATION_MODE', 'True').lower() == 'true'
    PRINTER_SIMULATION_DIR = os.path.join(DATA_DIR, 'etiquetas_simuladas')
    PRINTER_PENDING_FILE = os.path.join(DATA_DIR, 'etiquetas_pendientes.json')
    PRINTER_RETRY_ATTEMPTS = int(os.environ.get('PRINTER_RETRY_ATTEMPTS', '3'))
    PRINTER_TIMEOUT = int(os.environ.get('PRINTER_TIMEOUT', '10'))
    
    # Configuración de etiquetas
    LABELS_PER_CARRO = int(os.environ.get('LABELS_PER_CARRO', '2'))  # 1 o 2 etiquetas por carro
    PRINT_ON_BONO_GENERATION = os.environ.get('PRINT_ON_BONO_GENERATION', 'True').lower() == 'true'
    PRINT_ON_CARRO_COMPLETION = os.environ.get('PRINT_ON_CARRO_COMPLETION', 'True').lower() == 'true'
