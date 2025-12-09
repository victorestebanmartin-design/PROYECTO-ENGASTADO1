# TESTING: Sistema de Impresión de Etiquetas Zebra GK420T

## Estado de Implementación ✅

✅ **COMPLETADO** - Todos los componentes implementados y listos para testing

### Componentes Creados:

1. **app/zpl_templates.py** - Plantillas ZPL para etiquetas de 55x15mm
2. **app/printer_manager.py** - Gestor con modo simulación y producción
3. **config.py** - Configuración completa de impresora
4. **app/proyecto_manager.py** - Integración de impresión en bonos y finalización
5. **app/routes.py** - 7 endpoints nuevos de API
6. **templates/admin.html** - Sección de control de impresora
7. **static/js/admin.js** - Funciones JavaScript de UI

---

## Configuración Actual

```python
# config.py
PRINTER_ENABLED = True
PRINTER_SIMULATION_MODE = True  # ← MODO SIMULACIÓN ACTIVO
LABELS_PER_CARRO = 2             # ← 2 etiquetas por carro
PRINT_ON_BONO_GENERATION = True
PRINT_ON_CARRO_COMPLETION = True
```

**Modo Simulación**: Los archivos ZPL se guardan en `data/etiquetas_simuladas/` en lugar de enviarse a impresora física.

---

## Pruebas a Realizar

### 1. Verificar Estado de Impresora

**URL**: http://127.0.0.1:5000/admin

**Pasos**:
1. Scroll hasta "🖨️ Control de Impresora Zebra GK420T"
2. Click en "🔍 Verificar Estado"
3. **Resultado esperado**:
   - Modo: Modo Simulación
   - Estado: simulation
   - Disponible: ✅ Sí
   - Directorio simulación: data/etiquetas_simuladas
   - Etiquetas simuladas: 0

---

### 2. Imprimir Etiqueta de Prueba

**Pasos**:
1. Click en "🧪 Imprimir Prueba"
2. Confirmar en el diálogo
3. **Resultado esperado**:
   - Alert: "✅ Etiqueta simulada guardada: [timestamp]_etiqueta.zpl"
   - Se crea archivo en `data/etiquetas_simuladas/`

**Verificar**:
```powershell
# Ver archivos generados
Get-ChildItem data\etiquetas_simuladas\*.zpl | Select-Object Name, Length, LastWriteTime
```

**Visualizar ZPL**:
1. Abrir archivo `.zpl` con Notepad
2. Copiar el código ZPL (después de los comentarios con #)
3. Ir a: https://labelary.com/viewer.html
4. Cambiar DPI a: 8 dpmm (203 dpi)
5. Cambiar tamaño a: 2.17 x 0.59 inches (55x15mm)
6. Pegar código y ver preview

---

### 3. Generar Bono con Impresión de Etiquetas

**Pre-requisitos**:
- Tener 6 carros con órdenes asignadas en Gestión de Proyectos
- Las órdenes deben tener formato: "NUMERO_ORDEN - CODIGO_CORTE"

**Pasos**:
1. Ir a http://127.0.0.1:5000/gestion-proyectos
2. Asignar órdenes a los 6 carros (si no están asignados)
3. Click en "Generar Bono"
4. Introducir nombre del bono (ej: "BONO-TEST-001")
5. Confirmar

**Resultado esperado**:
- Bono generado exitosamente
- Se crean **12 archivos ZPL** en `data/etiquetas_simuladas/`:
  - 6 archivos de tipo `asignacion` (formato: `[timestamp]_asignacion_carroX.zpl`)
  - 6 archivos de tipo `asignacion_duplicado` (formato: `[timestamp]_asignacion_duplicado_carroX.zpl`)

**Verificar archivos**:
```powershell
# Contar archivos por tipo
Get-ChildItem data\etiquetas_simuladas\*asignacion*.zpl | Measure-Object | Select-Object Count
```

**Contenido esperado en etiquetas de asignación**:
- Nº de Carro (1-6)
- Nº de Orden
- Código de Corte
- Proyecto (truncado a 20 caracteres)
- Cantidad de Terminales

---

### 4. Finalizar Carro para Imprimir Etiqueta de Finalización

**Pre-requisitos**:
- Tener un bono generado
- Tener la versión V3 funcionando (progreso detallado)

**Pasos**:
1. Ir a http://127.0.0.1:5000/v3
2. Seleccionar el bono creado
3. Seleccionar un terminal/operario
4. Completar todos los terminales de un carro
5. Al finalizar el último terminal del carro

**Resultado esperado**:
- Se genera **1 archivo ZPL** adicional de tipo `finalizacion`:
  - Formato: `[timestamp]_finalizacion_carroX.zpl`

**Contenido esperado en etiqueta de finalización**:
- "CARRO X FINALIZADO"
- Nombre del Bono
- Fecha y Hora
- Operario (Terminal)
- Terminales completados / totales
- Porcentaje de progreso (100%)

---

### 5. Ver Etiquetas Simuladas desde Admin

**Pasos**:
1. Ir a http://127.0.0.1:5000/admin
2. Click en "📋 Ver Etiquetas Simuladas"

**Resultado esperado**:
- Tabla con todas las etiquetas generadas
- Columnas: Archivo, Fecha, Tamaño
- Link a labelary.com para visualización
- Botón "🗑️ Limpiar Todas"

---

### 6. Limpiar Etiquetas Simuladas

**Pasos**:
1. En admin, con lista de etiquetas visible
2. Click en "🗑️ Limpiar Todas"
3. Confirmar

**Resultado esperado**:
- Alert: "✅ Eliminadas X etiquetas simuladas"
- Se vacía el directorio `data/etiquetas_simuladas/`
- Al hacer "Ver Etiquetas Simuladas" aparece: "No hay etiquetas simuladas"

---

### 7. Testing de Endpoints API

#### GET /api/printer/status
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/printer/status -Method GET
```

**Respuesta esperada**:
```json
{
  "success": true,
  "available": true,
  "status": "simulation",
  "mode": "Modo Simulación",
  "message": "Etiquetas se guardan en data/etiquetas_simuladas",
  "has_paper": true,
  "simulation_dir": "data/etiquetas_simuladas",
  "simulated_labels": X
}
```

#### GET /api/printer/simulated-labels
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/printer/simulated-labels -Method GET
```

#### POST /api/printer/reprint (Reimprimir manual)
```powershell
$body = @{
    tipo = "asignacion"
    carro = 1
    orden = "12345"
    codigo_corte = "TEST-001"
    proyecto = "Proyecto Test"
    cantidad_terminales = 100
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:5000/api/printer/reprint -Method POST -Body $body -ContentType "application/json"
```

---

## Estructura de Archivos ZPL Generados

### Ejemplo de Nombre de Archivo:
```
20251209_143525_123456_asignacion_carro3.zpl
20251209_143525_234567_asignacion_duplicado_carro3.zpl
20251209_145830_345678_finalizacion_carro3.zpl
```

### Formato del archivo `.zpl`:
```
# SIMULACIÓN DE IMPRESIÓN ZEBRA GK420T
# Fecha: 2025-12-09 14:35:25
# Metadatos:
#   tipo: asignacion
#   bono: BONO-TEST-001
#   carro: 3
#   orden: 12345
#   codigo_corte: TEST-001
#   proyecto: Proyecto Prueba
# Visualizar en: https://labelary.com/viewer.html
# Dimensiones: 55mm x 15mm (2.17" x 0.59")
# DPI: 203 (8 dpmm)

============================================================

^XA
^FO10,5^A0N,25,25^FDCarro: 3^FS
^FO10,35^GB410,1,1^FS
^FO10,40^A0N,20,20^FDOrden: 12345^FS
...
^XZ
```

---

## Visualización de Etiquetas en Labelary

1. **Abrir**: https://labelary.com/viewer.html
2. **Configurar**:
   - **Printer DPI**: 8 dpmm (203 dpi)
   - **Label Size**: Width=2.17, Height=0.59 inches
   - **Orientation**: Default
3. **Pegar código ZPL** (solo la parte entre `^XA` y `^XZ`)
4. **Ver preview** en tiempo real

**Ejemplo visual esperado**:
```
┌─────────────────────────────┐
│ Carro: 3                    │
│ ───────────────────────────│
│ Orden: 12345                │
│ TEST-001       Term: 100    │
│ Proyecto Prueba             │
└─────────────────────────────┘
```

---

## Preparación para Producción

### Cambiar a Modo Producción (Raspberry Pi)

Cuando tengas la impresora Zebra conectada:

1. **Configurar CUPS en Raspberry Pi**:
```bash
sudo apt-get install cups cups-client printer-driver-all
sudo usermod -a -G lpadmin pi
sudo systemctl restart cups
```

2. **Detectar impresora**:
```bash
lsusb | grep -i zebra
lpinfo -v
```

3. **Agregar impresora**:
```bash
lpadmin -p ZebraGK420T -E -v usb://Zebra/GK420t -P /usr/share/cups/model/Postscript.ppd
lpoptions -d ZebraGK420T
```

4. **Cambiar configuración**:
```python
# En Raspberry Pi: editar config.py
PRINTER_SIMULATION_MODE = False  # ← Cambiar a False
```

5. **Reiniciar aplicación**:
```bash
sudo systemctl restart engastado.service
```

---

## Troubleshooting

### Problema: No se generan archivos ZPL

**Verificar**:
1. Revisar logs en terminal donde corre Flask
2. Verificar que existe directorio: `data/etiquetas_simuladas/`
3. Verificar permisos de escritura

**Logs esperados al generar bono**:
```
INFO - Iniciando impresión de etiquetas para bono BONO-TEST-001
INFO - Etiqueta asignación Carro 1: Etiqueta simulada guardada: [filename]
INFO - Etiqueta duplicado Carro 1: Etiqueta simulada guardada: [filename]
...
INFO - Finalizada impresión de etiquetas para bono BONO-TEST-001
```

### Problema: Errores de import

**Verificar**:
```python
# En Python shell
from app.printer_manager import PrinterManager
from app.zpl_templates import ZPLTemplates
from config import Config

printer = PrinterManager(Config)
status = printer.get_printer_status()
print(status)
```

### Problema: Etiquetas vacías o mal formateadas

**Verificar**:
- Las órdenes tienen formato correcto: "NUMERO - CODIGO"
- Los carros tienen proyectos asignados
- Revisar contenido del archivo ZPL generado

---

## Checklist de Testing Completo

- [ ] Servidor Flask arranca sin errores
- [ ] Sección de impresora visible en admin
- [ ] Verificar estado muestra "Modo Simulación"
- [ ] Imprimir prueba genera archivo .zpl
- [ ] Archivo de prueba visualizable en labelary.com
- [ ] Generar bono crea 12 archivos (6 asignación + 6 duplicado)
- [ ] Etiquetas de asignación tienen datos correctos
- [ ] Finalizar carro genera archivo de finalización
- [ ] Etiqueta de finalización tiene datos correctos
- [ ] "Ver Etiquetas Simuladas" lista todos los archivos
- [ ] "Limpiar Todas" elimina todos los archivos
- [ ] Endpoints API responden correctamente
- [ ] No hay errores en logs de Flask

---

## Próximos Pasos

1. **Testing completo** con órdenes reales
2. **Ajustar dimensiones** de etiquetas si es necesario
3. **Obtener rollos de etiquetas** de 55x15mm
4. **Conectar Zebra** a Raspberry Pi
5. **Configurar CUPS** en Raspberry Pi
6. **Cambiar a modo producción**
7. **Pruebas con impresora física**
8. **Calibración** de posiciones ZPL si es necesario

---

## Recursos

- **Labelary Viewer**: https://labelary.com/viewer.html
- **ZPL Documentation**: https://www.zebra.com/content/dam/zebra/manuals/printers/common/programming/zpl-zbi2-pm-en.pdf
- **Zebra GK420T Manual**: https://www.zebra.com/us/en/support-downloads/printers/desktop/gk420t.html

---

**Fecha**: 9 de diciembre de 2025  
**Sistema**: PROYECTO-ENGASTADO1  
**Versión**: 1.0 - Sistema de Impresión Integrado
