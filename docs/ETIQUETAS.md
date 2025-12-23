# 🏷️ Sistema de Generación de Etiquetas

## Descripción General

La nueva sección de **Etiquetas** permite generar etiquetas para grupos de cables (agrupados por código de cable + elemento) en formato imprimible para **impresora normal** (no Zebra). El sistema agrupa automáticamente los cables siguiendo la misma lógica que el engastado V3.

## Características

- **Selección de archivo Excel**: Elige uno de los archivos cargados en el sistema
- **Agrupamiento automático**: Por cod.cable + elemento (igual que V3)
- **Una etiqueta por grupo**: No múltiples copias, solo una por cada agrupación
- **Vista previa**: Visualiza todas las etiquetas antes de imprimir
- **Impresión estándar**: Compatible con cualquier impresora normal (no Zebra)
- **Formato HTML/CSS**: Listo para imprimir directamente desde el navegador

## Acceso

Desde el **HOME** del sistema, accede a la tarjeta "Etiquetas" con el icono 🏷️.

URL directa: `/etiquetas`

## Flujo de Trabajo

### 1. Seleccionar Archivo Excel

- Abre la sección de Etiquetas
- Selecciona un archivo Excel del desplegable (archivos cargados en el sistema)
- El sistema muestra cuántos archivos están disponibles

### 2. Cargar Grupos

- Haz clic en "Cargar Grupos"
- El sistema lee el archivo y agrupa automáticamente por:
  - **Cod. cable** + **De Elemento**
- Se muestran estadísticas:
  - Número de grupos encontrados
  - Cantidad de etiquetas a generar (una por grupo)
  - Estimación de hojas A4 necesarias

### 3. Vista Previa

- Haz clic en "Vista Previa"
- Visualiza todas las etiquetas en formato de cuadrícula (3 columnas)
- Cada etiqueta muestra:
  - Código de cable
  - Nombre del elemento
  - Cantidad de cables en el grupo
  - Número de terminales

### 4. Imprimir Etiquetas

- Haz clic en "Imprimir Etiquetas"
- Se abre una nueva ventana con las etiquetas formateadas
- Automáticamente se abre el diálogo de impresión del navegador
- Imprime en tu impresora normal (no necesitas Zebra)

## Formato de Etiquetas

### Distribución en Página

- **3 columnas** por página
- **6 filas** por página
- **18 etiquetas** por hoja A4
- Salto de página automático cuando se llena una hoja

### Contenido de Cada Etiqueta

Cada etiqueta incluye:

1. **Código de Cable** (en azul, destacado)
2. **Elemento** (nombre del componente)
3. **Descripción del cable** (si está disponible)
4. **Sección** (calibre del cable)
5. **Longitud** (si está especificada)
6. **Estadísticas**: 
   - Cantidad de cables en el grupo
   - Número total de terminales

### Ejemplo de Etiqueta

```
┌─────────────────────┐
│ CC001               │ ← Código (azul)
│ TERMINAL-45         │ ← Elemento
│ Desc: Cable rojo... │ ← Descripción
│ Sección: 1.5mm²     │ ← Sección
│ Long: 250mm         │ ← Longitud
│ ─────────────────── │
│ Cables: 12 | Term: 24│ ← Estadísticas
└─────────────────────┘
```

## Agrupamiento (Como V3)

El sistema agrupa los cables exactamente igual que en el engastado V3:

### Criterios de Agrupación

- **Clave de grupo**: `Cod. cable` + `De Elemento`
- **Cuenta cables**: Todos los cables que coincidan con esa combinación
- **Cuenta terminales**: Suma de terminales en ambos lados (De Terminal + Para Terminal)

### Ejemplo de Agrupamiento

Si el Excel tiene:

```
| Cod.cable | Cable/Marca | De Elemento  | De Terminal | Para Terminal |
|-----------|-------------|--------------|-------------|---------------|
| CC001     | 1           | TERMINAL-45  | T001        | T002          |
| CC001     | 2           | TERMINAL-45  | T001        | T002          |
| CC001     | 3           | TERMINAL-60  | T003        | S/T           |
| CC002     | 4           | TERMINAL-45  | T004        | T005          |
```

Se generan **3 etiquetas**:
1. **CC001 + TERMINAL-45** (2 cables, 4 terminales)
2. **CC001 + TERMINAL-60** (1 cable, 1 terminal)
3. **CC002 + TERMINAL-45** (1 cable, 2 terminales)

## Archivos Técnicos

### Frontend

- **Template HTML**: `templates/etiquetas.html`
- **JavaScript**: `static/js/etiquetas.js`
- **Estilos**: `static/css/style.css` (sección `.version-etiquetas`)

### Backend

- **Ruta principal**: `/etiquetas` en `app/routes.py`
- **API Endpoints**:
  - `POST /api/etiquetas/cargar_grupos`: Carga y agrupa datos de un archivo
  - `POST /api/etiquetas/generar_html`: Genera HTML imprimible

### Funciones Principales

- **`agrupar_por_cod_cable_elemento(registros)`**: Agrupa registros por código + elemento
- **`generar_html_etiquetas_impresion(grupos, archivo)`**: Genera HTML con CSS para imprimir

## Impresión

### Configuración Recomendada

- **Tamaño**: A4
- **Orientación**: Vertical (portrait)
- **Márgenes**: Normales (10mm)
- **Escala**: 100%
- **Color**: Puede ser blanco y negro

### Proceso de Impresión

1. Se abre ventana nueva con las etiquetas
2. Diálogo de impresión se abre automáticamente
3. Verifica la vista previa de impresión
4. Ajusta configuración si es necesario
5. Haz clic en "Imprimir"

### CSS de Impresión

El sistema incluye estilos específicos para impresión:
- Oculta elementos de navegación
- Optimiza márgenes de página
- Previene cortes en medio de etiquetas
- Saltos de página automáticos

## Ejemplo de Uso Completo

1. **Usuario**: Accede a sección "Etiquetas"
2. **Usuario**: Selecciona archivo "Proyecto_A.xlsx"
3. **Usuario**: Hace clic en "Cargar Grupos"
4. **Sistema**: Agrupa y encuentra 24 grupos diferentes
5. **Sistema**: Muestra "24 grupos, 24 etiquetas, 2 hojas A4"
6. **Usuario**: Hace clic en "Vista Previa"
7. **Sistema**: Muestra todas las etiquetas en cuadrícula
8. **Usuario**: Revisa que todo esté correcto
9. **Usuario**: Hace clic en "Imprimir Etiquetas"
10. **Sistema**: Abre ventana de impresión
11. **Usuario**: Confirma y imprime en su impresora

## Diferencias con Versión Anterior

### ❌ Antigua (Zebra + ZPL)
- Requería impresora Zebra
- Formato ZPL complicado
- 65 etiquetas pequeñas (5x13mm)
- Input manual de código de cable

### ✅ Nueva (Impresora Normal + HTML)
- Cualquier impresora estándar
- Formato HTML simple y visual
- Etiquetas más grandes y legibles
- Selector de archivos del sistema
- Agrupamiento automático
- Una etiqueta por grupo
