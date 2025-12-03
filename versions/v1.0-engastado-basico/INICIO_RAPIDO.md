# 🎉 GUÍA DE INICIO RÁPIDO - Sistema de Engastado Automático

## ✅ SISTEMA COMPLETADO Y FUNCIONANDO

**Fecha:** 13 de noviembre de 2025  
**Estado:** ✅ Aplicación lista para usar

---

## 🚀 CÓMO INICIAR LA APLICACIÓN

### 1. Abrir terminal en la carpeta del proyecto
```powershell
cd "C:\Users\estebanv\PROYECTO ENGASTADO1"
```

### 2. Activar entorno virtual
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Iniciar el servidor
```powershell
python run.py
```

### 4. Acceder a la aplicación
- **En tu PC:** http://localhost:5000
- **Desde otros PCs en red:** http://10.252.10.47:5000

---

## 📱 CÓMO USAR LA APLICACIÓN

### MODO OPERARIO (Pantalla Principal)

#### **PASO 1: Configuración Inicial (Solo primera vez)**
1. Haz clic en **"⚙️ Administración"**
2. Ve a la sección **"🔗 Asociar Código de Barras"**
3. Completa el formulario:
   - **Código de Barras:** CORADIA_IT_001 (o el código que vayas a usar)
   - **Archivo Excel:** LISTADO CABLEADO CORADIA ITALIA.xlsx
   - **Descripción:** Listado Cableado Coradia Italia
   - **Proyecto:** Coradia Italia
4. Haz clic en **"✅ Asociar"**

#### **PASO 2: Operación Normal**
1. **Escanear Corte de Cable:**
   - Usa la pistola lectora para escanear el código: `CORADIA_IT_001`
   - O escríbelo manualmente y presiona ENTER
   - El sistema cargará el archivo Excel

2. **Escanear Terminal:**
   - Escanea el código del terminal a engastar (ej: `641M155`)
   - O escríbelo manualmente y presiona ENTER
   - El sistema mostrará las instrucciones en tarjetas

3. **Ver Instrucciones:**
   - Verás tarjetas agrupadas por código de cable y elemento
   - Cada tarjeta muestra:
     * Código de cable
     * Elemento
     * Descripción del cable
     * Sección y longitud
     * Lista de conexiones con Cable/Marca
     * Terminales origen y destino
     * Puntos de conexión

4. **Continuar Trabajando:**
   - **"🔄 Escanear Otro Terminal"** - Para buscar otro terminal en el mismo corte
   - **"📂 Cambiar Corte"** - Para cambiar a otro archivo Excel

---

## ⚙️ MODO ADMINISTRACIÓN

### Subir Nuevos Archivos Excel
1. Ve a **"⚙️ Administración"**
2. En la sección **"📤 Subir Archivo Excel"**
3. Selecciona el archivo .xlsx o .xls
4. Haz clic en **"📤 Subir Archivo"**

### Asociar Códigos de Barras
1. Después de subir un archivo
2. Ve a **"🔗 Asociar Código de Barras"**
3. Completa:
   - Código de barras único
   - Selecciona el archivo de la lista
   - Descripción y proyecto (opcional)
4. Haz clic en **"✅ Asociar"**

### Ver Archivos y Cortes Registrados
- En la parte inferior verás:
  * **"📋 Cortes Registrados"** - Códigos de barras asociados
  * **"📁 Archivos Excel Disponibles"** - Archivos subidos

---

## 🧪 PRUEBA DE FUNCIONAMIENTO

### Datos de Prueba con el Excel Actual:

**Código de Corte:** `CORADIA_IT_001` (después de asociarlo)

**Terminales para probar:**
- `641M155` - Aparece en múltiples conexiones
- `641H10056` - Terminal de destino
- `640204` - Otro terminal de destino

**Resultado esperado:**
- El sistema mostrará tarjetas con:
  * Cable: 640C10024A
  * Elemento: MCMifB/P1 (u otros)
  * Conexiones con Cable/Marca: 202, 203, 804, etc.

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### ✅ Implementadas:
- [x] Carga múltiples archivos Excel
- [x] Asociación de códigos de barras con archivos
- [x] Búsqueda de terminales en ambas columnas (De Terminal y Para Terminal)
- [x] Agrupación por código de cable y elemento
- [x] Vista de tarjetas clara y organizada
- [x] Muestra Cable/Marca para identificación física
- [x] Interfaz responsive (funciona en PC y tablets)
- [x] Compatible con pistolas lectoras USB
- [x] Sistema de administración completo
- [x] Validación de datos
- [x] Mensajes de error claros

### 🔜 Mejoras Futuras (Opcionales):
- [ ] Sistema de login para operarios
- [ ] Registro de operaciones (log)
- [ ] Estadísticas de producción
- [ ] Soporte para imágenes
- [ ] Impresión de instrucciones
- [ ] Modo offline

---

## 🔧 CONFIGURACIÓN DE RED LOCAL

### Para acceder desde otros PCs:

1. **Obtener tu IP:**
   ```powershell
   ipconfig
   ```
   Buscar "IPv4 Address" (ej: 10.252.10.47)

2. **Configurar Firewall:**
   - Abrir "Firewall de Windows Defender"
   - Permitir puerto 5000 para conexiones entrantes

3. **Acceder desde otros PCs:**
   ```
   http://[TU-IP]:5000
   ```
   Ejemplo: http://10.252.10.47:5000

---

## 📊 ESTRUCTURA DE DATOS

### Archivo Excel - Hoja "Format":
- **Cod. cable:** Código del cable
- **Sección:** Sección del cable
- **Longitud:** Longitud en metros
- **Cable / Marca:** ⭐ Identificación física del cable
- **Descripción Cable:** Descripción técnica
- **De Elemento:** Elemento origen
- **De Terminal:** ⭐ Terminal origen (búsqueda aquí)
- **Para Elemento:** Elemento destino
- **Para Pto.Conexión:** Punto de conexión
- **Para Terminal:** ⭐ Terminal destino (búsqueda aquí)

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### El servidor no inicia:
```powershell
# Verificar que el entorno virtual esté activado
.\.venv\Scripts\Activate.ps1

# Verificar instalación
pip install -r requirements.txt
```

### No encuentra el terminal:
- Verifica que el código sea exacto (respeta mayúsculas/minúsculas)
- Asegúrate de haber cargado el archivo Excel correcto
- El terminal debe existir en las columnas "De Terminal" o "Para Terminal"

### Error al cargar Excel:
- Verifica que el archivo esté en: `data/cortes/`
- El archivo debe estar en formato .xlsx o .xls
- Debe tener una hoja llamada "Format" (o cambiar config.py)

### Pistola lectora no funciona:
- Verifica que esté conectada por USB
- Debería funcionar como un teclado (envía texto + ENTER)
- Prueba escribiendo manualmente primero

---

## 📁 ARCHIVOS IMPORTANTES

```
PROYECTO ENGASTADO1/
├── run.py                          # ⭐ Ejecutar esto para iniciar
├── config.py                       # Configuración
├── requirements.txt                # Dependencias
├── app/
│   ├── __init__.py
│   ├── routes.py                   # Rutas de la API
│   └── excel_manager.py            # Lógica de Excel
├── templates/
│   ├── index.html                  # Página principal (operarios)
│   └── admin.html                  # Página de administración
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js                 # JavaScript principal
│       └── admin.js                # JavaScript admin
├── data/
│   ├── cortes/                     # ⭐ Archivos Excel aquí
│   │   └── LISTADO CABLEADO CORADIA ITALIA.xlsx
│   └── codigos_cortes.json         # ⭐ Mapeo código → archivo
└── docs/                           # Documentación
    ├── ANALISIS_EXCEL.md
    ├── FLUJO_TRABAJO.md
    └── notas.md
```

---

## 💡 CONSEJOS DE USO

1. **Primera vez:** Usa el panel de administración para configurar códigos de barras
2. **Operarios:** Solo necesitan la pantalla principal (http://localhost:5000)
3. **Administrador:** Usa http://localhost:5000/admin para gestionar archivos
4. **Pistolas lectoras:** Funcionan automáticamente, no necesitan configuración extra
5. **Backup:** Haz copias de seguridad de `data/codigos_cortes.json` regularmente

---

## 📞 SOPORTE

Para dudas o problemas:
1. Revisa esta guía
2. Consulta `REQUISITOS.md` para detalles del proyecto
3. Consulta `INSTRUCCIONES_DESARROLLO.md` para desarrollo
4. Revisa logs en la terminal donde ejecutaste `run.py`

---

## 🎉 ¡LISTO PARA USAR!

La aplicación está completamente funcional y lista para producción.

**Servidor ejecutándose en:**
- Local: http://localhost:5000
- Red: http://10.252.10.47:5000

**Próximos pasos:**
1. Configura códigos de barras en el panel de administración
2. Prueba con algunos terminales del Excel
3. Capacita a los operarios en el uso básico
4. ¡Empieza a usar el sistema!

---

*Documento creado: 13 de noviembre de 2025*
*Sistema versión 1.0*
