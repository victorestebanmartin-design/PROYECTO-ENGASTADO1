# 🔌 Sistema de Engastado Automático

Sistema web interactivo para guiar a operarios en el proceso de engastado automático de cables mediante instrucciones basadas en datos de archivos Excel.

---

## 📋 Descripción

Esta aplicación web proporciona instrucciones precisas a los operarios sobre qué cables deben seleccionar del peine para engastar, basándose en el terminal o pin introducido en la máquina. El sistema hace preguntas específicas al operario y genera instrucciones personalizadas mediante cuadros de diálogo interactivos.

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Archivo Excel con datos de engastado

### Instalación

1. **Clonar o descargar el proyecto**
   ```powershell
   cd "C:\Users\estebanv\PROYECTO ENGASTADO1"
   ```

2. **Crear entorno virtual**
   ```powershell
   python -m venv venv
   ```

3. **Activar entorno virtual**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Instalar dependencias**
   ```powershell
   pip install -r requirements.txt
   ```
   
   O instalar manualmente:
   ```powershell
   pip install flask pandas openpyxl python-dotenv
   ```

5. **Colocar archivo Excel**
   - Colocar el archivo Excel con los datos en la carpeta `data/`
   - Nombre recomendado: `datos_engastado.xlsx`

6. **Ejecutar la aplicación**
   ```powershell
   python run.py
   ```

7. **Acceder a la aplicación**
   - Abrir navegador en: `http://localhost:5000`

---

## 📁 Estructura del Proyecto

```
PROYECTO ENGASTADO1/
│
├── app/                          # Código de la aplicación
│   ├── __init__.py              # Inicialización de Flask
│   ├── routes.py                # Rutas/endpoints de la API
│   ├── excel_handler.py         # Manejo de archivos Excel
│   └── logic.py                 # Lógica de negocio
│
├── templates/                    # Plantillas HTML
│   ├── index.html               # Página principal
│   ├── preguntas.html           # Interfaz de preguntas
│   └── instrucciones.html       # Visualización de instrucciones
│
├── static/                       # Archivos estáticos
│   ├── css/
│   │   └── style.css            # Estilos personalizados
│   └── js/
│       └── main.js              # JavaScript interactivo
│
├── data/                         # Datos
│   └── datos_engastado.xlsx     # Archivo Excel (a agregar)
│
├── docs/                         # Documentación adicional
│   └── notas.md
│
├── venv/                         # Entorno virtual (no subir a Git)
│
├── .gitignore                    # Archivos a ignorar en Git
├── requirements.txt              # Dependencias del proyecto
├── config.py                     # Configuración de la aplicación
├── run.py                        # Archivo principal de ejecución
├── REQUISITOS.md                 # Requisitos detallados del proyecto
├── INSTRUCCIONES_DESARROLLO.md   # Guía de desarrollo paso a paso
└── README.md                     # Este archivo
```

---

## 🔧 Configuración

### Archivo Excel
El archivo Excel debe estar ubicado en `data/datos_engastado.xlsx` y debe contener:
- [PENDIENTE: Definir columnas específicas]
- Columna de terminales/pines
- Información de cables
- Especificaciones de engastado

### Configuración de la Aplicación
Editar `config.py` para ajustar:
- Ruta del archivo Excel
- Puerto del servidor
- Clave secreta (para producción)
- Modo debug

---

## 💻 Uso de la Aplicación

### Para Operarios

1. **Iniciar sesión** (si aplica)
2. **Introducir terminal/pin** en la interfaz principal
3. **Responder preguntas** que aparecen en los cuadros de diálogo
4. **Seguir instrucciones** mostradas para el engastado
5. **Completar proceso** según indicaciones

### Para Administradores

- Actualizar archivo Excel en carpeta `data/`
- Reiniciar aplicación si es necesario
- Monitorear logs de la aplicación

---

## 🌐 Acceso desde Red Local

Para que otros PCs accedan a la aplicación:

1. **Obtener IP del servidor**
   ```powershell
   ipconfig
   ```

2. **Configurar firewall** (permitir puerto 5000)

3. **Acceder desde otros PCs**
   ```
   http://[IP-DEL-SERVIDOR]:5000
   ```
   
   Ejemplo: `http://192.168.1.100:5000`

---

## 🛠️ Desarrollo

### Ejecutar en modo desarrollo
```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar con debug activado
python run.py
```

### Agregar nuevas funcionalidades
1. Consultar `INSTRUCCIONES_DESARROLLO.md` para guía detallada
2. Modificar archivos según necesidades
3. Probar cambios en desarrollo
4. Actualizar documentación

---

## 📦 Dependencias Principales

- **Flask** - Framework web
- **pandas** - Procesamiento de datos Excel
- **openpyxl** - Lectura de archivos Excel .xlsx
- **python-dotenv** - Gestión de variables de entorno

Ver `requirements.txt` para lista completa de dependencias.

---

## 🧪 Testing

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar tests (cuando estén implementados)
python -m pytest
```

---

## 📝 Documentación Adicional

- **REQUISITOS.md** - Requisitos funcionales y técnicos detallados
- **INSTRUCCIONES_DESARROLLO.md** - Guía paso a paso para desarrollo
- **docs/notas.md** - Notas y observaciones del proyecto

---

## 🔄 Actualización de Datos

Para actualizar los datos de engastado:

1. Modificar archivo Excel en `data/`
2. Mantener misma estructura de columnas
3. No es necesario reiniciar la aplicación (se recarga automáticamente)

---

## 🐛 Solución de Problemas

### La aplicación no inicia
- Verificar que el entorno virtual esté activado
- Verificar que todas las dependencias estén instaladas
- Revisar mensajes de error en la consola

### No encuentra el archivo Excel
- Verificar que el archivo esté en `data/datos_engastado.xlsx`
- Verificar permisos de lectura del archivo
- Revisar ruta en `config.py`

### Error al acceder desde otro PC
- Verificar firewall de Windows
- Verificar que la aplicación esté ejecutándose en `0.0.0.0`
- Verificar conectividad de red

---

## 📊 Estado del Proyecto

**Versión:** 1.0.0 ✅ COMPLETADO  
**Fecha:** 13 de noviembre de 2025  
**Estado:** Sistema funcional y listo para uso en producción

### ✅ Implementado
- [x] Carga de múltiples archivos Excel
- [x] Sistema de códigos de barras
- [x] Búsqueda de terminales en ambas columnas
- [x] Vista de tarjetas agrupadas por cable y elemento
- [x] Interfaz completa responsive
- [x] Panel de administración
- [x] Compatible con pistolas lectoras USB
- [x] Testing con archivo Excel real
- [x] Documentación completa

---

## 👥 Contribución

Para contribuir al proyecto:
1. Consultar documentación en `REQUISITOS.md`
2. Seguir guía en `INSTRUCCIONES_DESARROLLO.md`
3. Mantener código limpio y documentado
4. Actualizar documentación cuando sea necesario

---

## 📞 Soporte

Para dudas o problemas:
- Consultar documentación en carpeta `docs/`
- Revisar archivos de requisitos e instrucciones
- Contactar al equipo de desarrollo

---

## 📄 Licencia

[Definir licencia según necesidades de la organización]

---

## 🙏 Agradecimientos

Proyecto desarrollado para el área de engastado automático.

---

**Nota:** Este proyecto está completado y funcional. Ver `INICIO_RAPIDO.md` para instrucciones de uso inmediato.

---

## 🚀 INICIO RÁPIDO

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Iniciar servidor
python run.py

# 3. Abrir navegador en:
http://localhost:5000
```

**📖 Para guía completa de uso, ver:** [`INICIO_RAPIDO.md`](INICIO_RAPIDO.md)
