# 🔌 Sistema de Engastado V2.0 - Modo Interactivo

## 🎯 Descripción

La **Versión 2.0** introduce un flujo de trabajo completamente guiado e interactivo para el proceso de engastado de terminales. El operario es dirigido paso a paso a través de todo el proceso, con controles temporales que aseguran el tiempo adecuado de engastado.

## 🚀 Acceso Rápido

- **V1.0 (Modo Manual):** http://localhost:5000
- **V2.0 (Modo Interactivo):** http://localhost:5000/v2
- **Administración:** http://localhost:5000/admin

## ✨ Flujo de Trabajo V2.0

### Paso 1: Escanear Corte de Cable
- Operario escanea el código de barras del corte
- Sistema carga automáticamente el archivo Excel correspondiente

### Paso 2: Seleccionar Terminal
- Sistema muestra **todos los terminales disponibles** en botones grandes
- Operario selecciona el terminal que va a engastar
- Diseño visual: botones grandes, fácil de presionar

### Paso 3: Preparación - Recoger Paquetes
- Sistema muestra lista de **"De Elemento"** (paquetes) que debe recoger
- Contador visual: "Tienes X paquetes que recoger del carro"
- Operario confirma que tiene todos los paquetes antes de continuar

### Paso 4: Engastado Progresivo
- **Vista de lista:** Todas las cajas visibles (bloqueadas excepto la primera)
- **Solo una caja activa:** El operario pincha la caja activa
- **Pantalla completa:** La caja se expande ocupando toda la pantalla
- **Timer obligatorio:** 3 segundos × número de terminales
  - Barra de progreso visual
  - Cuenta regresiva en segundos
  - No se puede saltar hasta completar el tiempo
- **Progresión automática:** Al terminar el timer:
  - Caja marcada como ✅ completada
  - Siguiente caja se activa automáticamente
  - Scroll automático a la caja activa

### Paso 5: Finalización
- Pantalla de éxito con resumen
- Opciones:
  - **Seleccionar otro terminal** (mantiene el mismo corte)
  - **Cambiar corte de cable** (vuelve al inicio)

## 🎨 Características Visuales

### Estados de las Cajas
- **🔒 Bloqueada:** Gris, opacidad 50%, cursor bloqueado
- **🟢 Activa:** Borde verde pulsante, fondo claro
- **✅ Completada:** Fondo verde, marca de verificación

### Animaciones
- Transiciones suaves entre pantallas
- Pulsación del borde en caja activa
- Expansión animada de caja a pantalla completa
- Barra de progreso con transición lineal
- Bounce del icono de éxito

### Color Coding (heredado de V1.0)
- 🔴 **Rojo:** Cable con terminal en AMBAS puntas
- 🔵 **Azul:** Cable con terminal en UNA punta

## 🔧 Especificaciones Técnicas

### Timer
- **Tiempo por terminal:** 3 segundos
- **Cálculo:** Tiempo total = 3 seg × número de terminales de la caja
- **Bloqueo:** El operario DEBE esperar, no puede cancelar
- **Precisión:** Actualización cada segundo

### API Endpoints Nuevos
```
GET  /api/listar_terminales  → Lista de terminales únicos del Excel
```

### Backend
- `ExcelManager.listar_terminales_unicos()` - Extrae terminales únicos
- Filtro automático: Excluye 'S/T' y valores vacíos
- Ordenamiento alfabético

### Frontend
- **JavaScript:** `static/js/main-v2.js`
- **HTML:** `templates/index-v2.html`
- **CSS:** `static/css/style-v2.css`

## 📱 Responsive Design

- Optimizado para tablets industriales
- Grid adaptable en selección de terminales
- Caja expandida ajustable a pantalla
- Botones grandes para fácil interacción

## 🔄 Compatibilidad con V1.0

Ambas versiones coexisten:
- **V1.0** permanece disponible en `/` (modo manual original)
- **V2.0** disponible en `/v2` (modo interactivo nuevo)
- Comparten el mismo backend y datos
- Misma lógica de agrupación y conteo

## 🎯 Ventajas del Modo Interactivo

### Para el Operario
- ✅ Proceso guiado paso a paso
- ✅ No puede saltarse pasos críticos
- ✅ Confirmación visual de progreso
- ✅ Tiempo garantizado de engastado
- ✅ Menos errores

### Para la Calidad
- ✅ Tiempo mínimo asegurado por terminal
- ✅ Proceso estandarizado
- ✅ Trazabilidad completa
- ✅ Reduces posibilidad de omisiones

### Para la Producción
- ✅ Flujo eficiente
- ✅ Feedback inmediato
- ✅ Menos interrupciones
- ✅ Información clara en todo momento

## 🐛 Solución de Problemas

### La lista de terminales no aparece
- Verificar que el archivo Excel se cargó correctamente
- Revisar que el Excel tiene datos en "De Terminal" y/o "Para Terminal"
- Verificar en consola del navegador si hay errores

### No puedo seleccionar una caja
- Solo se puede seleccionar la caja con borde verde (activa)
- Las cajas grises están bloqueadas hasta completar las anteriores
- Las cajas verdes con ✓ ya están completadas

### El timer no avanza
- Verificar conexión de red
- Refrescar la página
- Revisar consola del navegador

## 📝 Próximas Mejoras (V2.1)

- [ ] Sonido al completar cada caja
- [ ] Opción de pausar/reanudar timer
- [ ] Estadísticas de tiempo por operario
- [ ] Modo entrenamiento (sin timer)
- [ ] Exportar reporte de sesión
- [ ] Integración con base de datos

## 🤝 Contribución

Para reportar problemas o sugerir mejoras, contactar al equipo de desarrollo.

---

**Versión:** 2.0  
**Fecha:** 18 de noviembre de 2025  
**Autor:** Sistema de Engastado Automático  
**Licencia:** Uso interno
