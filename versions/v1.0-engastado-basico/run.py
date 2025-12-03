"""
Archivo principal para ejecutar la aplicación
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 SISTEMA DE ENGASTADO AUTOMÁTICO")
    print("=" * 80)
    print(f"📍 Servidor iniciado en: http://localhost:5000")
    print(f"📍 Acceso en red local: http://[TU-IP]:5000")
    print("=" * 80)
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
