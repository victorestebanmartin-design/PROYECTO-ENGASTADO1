# INSTRUCCIONES DE DESARROLLO - SISTEMA DE ENGASTADO AUTOMÁTICO

## 📋 GUÍA PASO A PASO PARA IMPLEMENTAR LA APLICACIÓN

---

## 🚀 FASE 1: CONFIGURACIÓN INICIAL DEL PROYECTO

### 1.1 Preparación del Entorno
```powershell
# Navegar a la carpeta del proyecto
cd "C:\Users\estebanv\PROYECTO ENGASTADO1"

# Crear entorno virtual de Python
python -m venv venv

# Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# Actualizar pip
python -m pip install --upgrade pip
```

### 1.2 Instalar Dependencias
```powershell
# Instalar librerías principales
pip install flask
pip install pandas
pip install openpyxl
pip install python-dotenv

# Guardar dependencias
pip freeze > requirements.txt
```

### 1.3 Estructura de Carpetas
La estructura del proyecto debe ser:
```
PROYECTO ENGASTADO1/
│
├── app/
│   ├── __init__.py           # Inicialización de Flask
│   ├── routes.py             # Rutas de la aplicación
│   ├── excel_handler.py      # Lógica de lectura del Excel
│   └── logic.py              # Lógica de negocio
│
├── templates/
│   ├── index.html            # Página principal
│   ├── preguntas.html        # Interfaz de preguntas
│   └── instrucciones.html    # Mostrar instrucciones
│
├── static/
│   ├── css/
│   │   └── style.css         # Estilos personalizados
│   └── js/
│       └── main.js           # JavaScript interactivo
│
├── data/
│   └── datos_engastado.xlsx  # Archivo Excel con datos
│
├── docs/
│   └── notas.md              # Notas adicionales
│
├── venv/                      # Entorno virtual (no subir a Git)
├── .gitignore
├── requirements.txt
├── config.py                  # Configuración de la app
├── run.py                     # Archivo principal para ejecutar
├── REQUISITOS.md
├── INSTRUCCIONES_DESARROLLO.md
└── README.md
```

---

## 🔧 FASE 2: DESARROLLO DEL BACKEND

### 2.1 Crear `app/__init__.py`
```python
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    
    # Registrar rutas
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app
```

### 2.2 Crear `app/excel_handler.py`
```python
import pandas as pd
import os

class ExcelHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        
    def load_excel(self):
        """Cargar el archivo Excel"""
        if os.path.exists(self.file_path):
            self.df = pd.read_excel(self.file_path)
            return True
        return False
    
    def buscar_por_terminal(self, terminal):
        """Buscar información por terminal/pin"""
        if self.df is not None:
            resultado = self.df[self.df['Terminal'] == terminal]
            return resultado.to_dict('records')
        return None
    
    def obtener_columnas(self):
        """Obtener nombres de columnas"""
        if self.df is not None:
            return list(self.df.columns)
        return []
```

### 2.3 Crear `app/logic.py`
```python
class LogicaEngastado:
    def __init__(self):
        self.preguntas = []
        self.respuestas = {}
    
    def cargar_preguntas(self):
        """
        Definir las preguntas que se harán al operario
        [PENDIENTE: Definir preguntas específicas]
        """
        self.preguntas = [
            {
                'id': 1,
                'texto': '¿Pregunta 1?',
                'tipo': 'opciones',
                'opciones': ['Opción A', 'Opción B']
            },
            # Agregar más preguntas aquí
        ]
        return self.preguntas
    
    def procesar_respuestas(self, respuestas):
        """Procesar las respuestas del operario"""
        self.respuestas = respuestas
        return self.generar_instrucciones()
    
    def generar_instrucciones(self):
        """
        Generar instrucciones basadas en las respuestas
        [PENDIENTE: Definir lógica específica]
        """
        instrucciones = {
            'cables': [],
            'orden': [],
            'notas': ''
        }
        return instrucciones
```

### 2.4 Crear `app/routes.py`
```python
from flask import Blueprint, render_template, request, jsonify
from app.excel_handler import ExcelHandler
from app.logic import LogicaEngastado
import os

bp = Blueprint('main', __name__)

# Inicializar manejadores
excel_handler = ExcelHandler('data/datos_engastado.xlsx')
logica = LogicaEngastado()

@bp.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@bp.route('/buscar_terminal', methods=['POST'])
def buscar_terminal():
    """Buscar información del terminal"""
    data = request.get_json()
    terminal = data.get('terminal')
    
    excel_handler.load_excel()
    resultado = excel_handler.buscar_por_terminal(terminal)
    
    if resultado:
        return jsonify({'success': True, 'data': resultado})
    return jsonify({'success': False, 'message': 'Terminal no encontrado'})

@bp.route('/obtener_preguntas', methods=['GET'])
def obtener_preguntas():
    """Obtener las preguntas para el operario"""
    preguntas = logica.cargar_preguntas()
    return jsonify({'preguntas': preguntas})

@bp.route('/procesar_respuestas', methods=['POST'])
def procesar_respuestas():
    """Procesar respuestas y generar instrucciones"""
    data = request.get_json()
    respuestas = data.get('respuestas')
    
    instrucciones = logica.procesar_respuestas(respuestas)
    return jsonify({'instrucciones': instrucciones})
```

---

## 🎨 FASE 3: DESARROLLO DEL FRONTEND

### 3.1 Crear `templates/index.html`
```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Engastado Automático</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Sistema de Engastado Automático</h1>
        
        <div class="input-section">
            <label for="terminal">Introduce Terminal/Pin:</label>
            <input type="text" id="terminal" placeholder="Ej: T-001">
            <button onclick="buscarTerminal()">Buscar</button>
        </div>
        
        <div id="resultado" class="hidden"></div>
    </div>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

### 3.2 Crear `static/css/style.css`
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    padding: 20px;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    margin-bottom: 30px;
    text-align: center;
}

.input-section {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
}

input[type="text"] {
    width: 70%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

button {
    padding: 10px 20px;
    font-size: 16px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    margin-left: 10px;
}

button:hover {
    background-color: #0056b3;
}

.hidden {
    display: none;
}

.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
}

.modal-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
}
```

### 3.3 Crear `static/js/main.js`
```javascript
async function buscarTerminal() {
    const terminal = document.getElementById('terminal').value;
    
    if (!terminal) {
        alert('Por favor, introduce un terminal');
        return;
    }
    
    try {
        const response = await fetch('/buscar_terminal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ terminal: terminal })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarPreguntas();
        } else {
            alert('Terminal no encontrado');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al buscar terminal');
    }
}

async function mostrarPreguntas() {
    // Obtener preguntas del servidor
    const response = await fetch('/obtener_preguntas');
    const data = await response.json();
    
    // Mostrar modal con preguntas
    // [PENDIENTE: Implementar interfaz de preguntas]
}

function mostrarInstrucciones(instrucciones) {
    // Mostrar instrucciones en modal
    // [PENDIENTE: Implementar interfaz de instrucciones]
}
```

---

## 🔧 FASE 4: ARCHIVOS DE CONFIGURACIÓN

### 4.1 Crear `config.py`
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'data', 'datos_engastado.xlsx')
    DEBUG = True
```

### 4.2 Crear `run.py`
```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 4.3 Crear `.gitignore`
```
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.env
.vscode/
.idea/
*.log
```

---

## 🧪 FASE 5: TESTING Y EJECUCIÓN

### 5.1 Probar la Aplicación
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar la aplicación
python run.py

# La aplicación estará disponible en: http://localhost:5000
```

### 5.2 Verificaciones
- [ ] El servidor Flask inicia correctamente
- [ ] La página principal carga sin errores
- [ ] El archivo Excel se lee correctamente
- [ ] Las búsquedas funcionan
- [ ] Las preguntas se muestran correctamente
- [ ] Las instrucciones se generan correctamente

---

## 📝 FASE 6: PERSONALIZACIÓN (Según información del usuario)

### 6.1 Adaptar `excel_handler.py`
- Modificar nombres de columnas según el Excel real
- Ajustar búsquedas según estructura de datos

### 6.2 Definir Preguntas en `logic.py`
- Crear lista completa de preguntas
- Implementar lógica condicional si es necesaria
- Definir tipos de respuestas

### 6.3 Implementar Generación de Instrucciones
- Definir formato de salida
- Implementar lógica de selección de cables
- Agregar validaciones

### 6.4 Mejorar Interfaz
- Adaptar diseño a necesidades específicas
- Agregar imágenes si es necesario
- Implementar modales/pop-ups
- Agregar colores/códigos si se requieren

---

## 🚀 FASE 7: DESPLIEGUE (Red Local)

### 7.1 Preparar para Producción
```powershell
# Desactivar modo debug en config.py
# Cambiar SECRET_KEY a valor seguro
# Configurar host y puerto según necesidades
```

### 7.2 Ejecutar en Servidor Local
```powershell
# Opción 1: Flask interno
python run.py

# Opción 2: Con waitress (más robusto)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 run:app
```

### 7.3 Acceso desde Otros PCs
- Asegurar que el firewall permita conexiones al puerto 5000
- Acceder desde otros PCs usando: `http://[IP-DEL-SERVIDOR]:5000`

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### Backend
- [ ] Configurar entorno virtual
- [ ] Instalar dependencias
- [ ] Crear estructura de carpetas
- [ ] Implementar lectura de Excel
- [ ] Crear sistema de rutas Flask
- [ ] Implementar lógica de preguntas
- [ ] Implementar generación de instrucciones

### Frontend
- [ ] Crear templates HTML
- [ ] Diseñar estilos CSS
- [ ] Implementar JavaScript interactivo
- [ ] Crear sistema de modales
- [ ] Implementar interfaz de preguntas
- [ ] Implementar visualización de instrucciones

### Testing
- [ ] Probar carga de Excel
- [ ] Probar búsquedas
- [ ] Probar flujo de preguntas
- [ ] Probar generación de instrucciones
- [ ] Probar en múltiples navegadores
- [ ] Probar desde diferentes PCs

### Documentación
- [ ] Completar REQUISITOS.md
- [ ] Actualizar README.md
- [ ] Documentar código
- [ ] Crear manual de usuario

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### El Excel no se carga
- Verificar ruta del archivo
- Verificar formato del Excel (.xlsx)
- Verificar permisos de lectura

### Error al iniciar Flask
- Verificar que el entorno virtual esté activado
- Verificar que todas las dependencias estén instaladas
- Revisar logs de error

### No se puede acceder desde otros PCs
- Verificar configuración del firewall
- Verificar que host='0.0.0.0' en run.py
- Verificar conectividad de red

---

## 📞 NOTAS FINALES

- Este documento se actualizará conforme avance el desarrollo
- Secciones marcadas como [PENDIENTE] requieren información adicional
- Consultar REQUISITOS.md para detalles del proyecto
- Mantener comentarios en el código para facilitar mantenimiento
