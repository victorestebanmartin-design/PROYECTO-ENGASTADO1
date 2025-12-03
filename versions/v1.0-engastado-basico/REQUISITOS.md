# REQUISITOS DEL SISTEMA DE ENGASTADO AUTOMÁTICO

## 📋 DESCRIPCIÓN GENERAL

Sistema web para guiar a operarios en el proceso de engastado automático de cables mediante instrucciones interactivas basadas en datos de archivos Excel.

---

## 🎯 OBJETIVO PRINCIPAL

Proporcionar instrucciones precisas a los operarios sobre qué cables deben seleccionar del peine para engastar, basándose en el terminal o pin introducido en la máquina.

---

## 🏗️ ARQUITECTURA PROPUESTA

**Tipo:** Aplicación Web
**Backend:** Python con Flask/FastAPI
**Frontend:** HTML/CSS/JavaScript
**Procesamiento de datos:** pandas, openpyxl

---

## 📊 ENTRADA DE DATOS

### Archivo Excel
- **Ubicación:** Carpeta `/data` del proyecto
- **Contenido esperado:**
  - Información de terminales/pines
  - Especificaciones de cables
  - Datos de engastado
  - [PENDIENTE: Definir columnas específicas cuando se suba el archivo]

---

## 🔄 FLUJO DE TRABAJO

### 1. **Inicio de Operación**
   - Operario accede a la aplicación web
   - Sistema carga datos del Excel

### 2. **Entrada de Datos**
   - Operario introduce terminal/pin en la interfaz
   - Sistema busca información asociada en el Excel

### 3. **Proceso Interactivo** [PENDIENTE: Definir preguntas específicas]
   - Sistema muestra preguntas en orden específico
   - Operario responde mediante interfaz (botones, selección, etc.)
   - Las respuestas pueden condicionar siguientes preguntas

### 4. **Instrucciones de Engastado**
   - Sistema muestra mediante pop-ups/cuadros de diálogo:
     * Qué cables seleccionar del peine
     * Orden de engastado
     * Especificaciones técnicas necesarias

### 5. **Registro** [OPCIONAL - Por definir]
   - Guardar registro de operaciones realizadas
   - Trazabilidad por operario/fecha/hora

---

## 💻 REQUISITOS TÉCNICOS

### Backend
- Python 3.8+
- Flask o FastAPI
- pandas (procesamiento Excel)
- openpyxl (lectura Excel)

### Frontend
- HTML5/CSS3
- JavaScript (Vanilla o framework ligero)
- Diseño responsive
- Cuadros de diálogo/modales interactivos

### Infraestructura
- Servidor local o red local
- Acceso desde PCs de operarios
- [PENDIENTE: Definir si necesita base de datos para registros]

---

## 👥 USUARIOS

**Operarios de engastado:**
- Operan máquinas de engastado de cables
- Necesitan instrucciones claras y precisas
- Trabajan en área de producción
- [PENDIENTE: Definir número de usuarios simultáneos]

---

## 📝 FUNCIONALIDADES CORE

### Versión 1.0 (MVP)
- [ ] Carga y lectura de archivo Excel
- [ ] Interfaz de entrada de terminal/pin
- [ ] Búsqueda de información en Excel
- [ ] Sistema de preguntas interactivas
- [ ] Mostrar instrucciones de cables a engastar
- [ ] Interfaz responsive y clara

### Versión 2.0 (Futuras mejoras)
- [ ] Sistema de autenticación de operarios
- [ ] Registro de operaciones (log)
- [ ] Estadísticas de producción
- [ ] Soporte para imágenes/diagramas
- [ ] Actualización de Excel en tiempo real
- [ ] Múltiples idiomas

---

## ❓ INFORMACIÓN PENDIENTE DE DEFINIR

### CRÍTICO
1. **Estructura del Excel:**
   - ¿Qué columnas contiene?
   - ¿Cuál es la relación terminal/pin → cables?
   - ¿Hay múltiples hojas?

2. **Preguntas al operario:**
   - ¿Cuántas preguntas hay?
   - ¿Qué tipo de respuestas? (Sí/No, Múltiple opción, Numérico, Texto)
   - ¿Son condicionales? (dependen de respuestas anteriores)
   - ¿Orden específico de preguntas?

3. **Formato de instrucciones:**
   - ¿Qué información exacta mostrar al operario?
   - ¿Necesitan colores/códigos?
   - ¿Posiciones específicas en el peine?
   - ¿Imágenes o solo texto?

### IMPORTANTE
4. **Entorno de uso:**
   - ¿Cuántos operarios simultáneos?
   - ¿Tipo de dispositivos? (PC, tablet, etc.)
   - ¿Red local o internet?
   - ¿Sistema operativo de las máquinas?

5. **Gestión del Excel:**
   - ¿Quién actualiza el Excel?
   - ¿Con qué frecuencia?
   - ¿Necesita validación de datos?

6. **Seguridad y trazabilidad:**
   - ¿Necesita login de operarios?
   - ¿Registro de operaciones?
   - ¿Auditoría de cambios?

---

## 🔐 CONSIDERACIONES DE SEGURIDAD

- Acceso controlado (solo red local si aplica)
- Backup automático de datos
- Validación de entradas de usuario
- Manejo de errores robusto

---

## 📈 ESCALABILIDAD

- Diseño modular para futuras expansiones
- Fácil adición de nuevas preguntas
- Soporte para múltiples líneas de producción
- Posibilidad de integración con otros sistemas

---

## 📅 NOTAS DE DESARROLLO

**Fecha de inicio:** 13 de noviembre de 2025
**Estado:** En fase de análisis de requisitos
**Próximos pasos:** 
1. Recibir archivo Excel de ejemplo
2. Definir preguntas específicas al operario
3. Establecer formato exacto de instrucciones de salida
4. Iniciar desarrollo del MVP

---

## 📞 CONTACTO Y ACTUALIZACIONES

Este documento se actualizará conforme se reciba más información del usuario.
Todas las secciones marcadas como [PENDIENTE] requieren confirmación antes de iniciar el desarrollo completo.
