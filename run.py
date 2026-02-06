"""
Archivo principal para ejecutar la aplicación
"""
import socket
from app import create_app

app = create_app()

def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        # Crear un socket para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "[IP no disponible]"

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("=" * 80)
    print("🚀 SISTEMA DE ENGASTADO AUTOMÁTICO")
    print("=" * 80)
    print(f"📍 Servidor iniciado en: http://localhost:5000")
    print(f"📍 Acceso en red local: http://{local_ip}:5000")
    print("=" * 80)
    print("💡 Para acceder desde otros dispositivos:")
    print(f"   1. Asegúrate de estar en la misma red")
    print(f"   2. Abre un navegador y ve a: http://{local_ip}:5000")
    print("=" * 80)
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 80)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
