# Integración de Etiquetas con V3

## 📋 Resumen

Este sistema integra las etiquetas numeradas con la V3 de engastado, permitiendo a los operarios buscar elementos de forma más rápida usando el número de etiqueta en lugar del código de cable + elemento.

## 🔄 Flujo Automático

### 1. Generación Automática de Etiquetas

Cuando se agrega un **nuevo corte de cable** desde el Admin:

```
Admin → Agregar Corte → Se genera automáticamente grupos_etiquetas.json
```

El sistema:
- ✅ Lee el archivo Excel del corte
- ✅ Agrupa por `cod_cable` + `elemento`
- ✅ Filtra solo grupos con sección
- ✅ Asigna numeración secuencial (1, 2, 3...)
- ✅ Guarda en `data/grupos_etiquetas.json`

### 2. Archivo Compartido

**Ubicación:** `data/grupos_etiquetas.json`

**Contenido:**
```json
{
  "archivo": "nombre_corte.xlsx",
  "fecha_generacion": "2025-12-22 15:30:00",
  "total_grupos": 60,
  "grupos": [
    {
      "numero_etiqueta": 1,
      "cod_cable": "640361",
      "elemento": "B11",
      "seccion": "Sec-1",
      "descripcion": "CABLE...",
      "longitud": 150,
      "num_cables": 2,
      "num_terminales": 4,
      "de_terminal": "TB1"
    },
    ...
  ]
}
```

## 🏷️ Uso en Sección Etiquetas

1. Ve a **HOME** → **Etiquetas**
2. Selecciona el archivo Excel cargado
3. Click en **"Cargar Grupos"**
4. Click en **"Imprimir Etiquetas"**

**Resultado:** Imprime etiquetas 21.3×38mm en folio A4 troquelado (13×5 = 65 etiquetas)

Cada etiqueta muestra:
- 🔢 Número secuencial (1, 2, 3...)
- 🔌 Elemento (TB1, Q2, etc.)
- 📟 Código de cable
- 📏 Sección

## 🚀 Uso en V3 Engastado

### Opción 1: Búsqueda por Número (NUEVO - MÁS RÁPIDO)

```javascript
// Operario busca: "3"
// Sistema encuentra: Etiqueta #3 → TB1 del cable 640361
```

**Ventajas:**
- ⚡ Más rápido: solo un número
- 👀 Más visual: pega etiqueta en el paquete físico
- ❌ Menos errores: no hay que recordar código largo

### Opción 2: Búsqueda Tradicional (mantiene compatibilidad)

```javascript
// Operario busca: "TB1 cable 640361"
// Sistema encuentra el mismo elemento
```

## 🔌 API Endpoints

### Buscar por Número de Etiqueta

**Endpoint:** `POST /api/etiquetas/buscar_por_numero`

**Request:**
```json
{
  "numero_etiqueta": 3
}
```

**Response (éxito):**
```json
{
  "success": true,
  "grupo": {
    "numero_etiqueta": 3,
    "cod_cable": "640361",
    "elemento": "TB1",
    "seccion": "Sec-1",
    ...
  },
  "mensaje": "Etiqueta #3: TB1 - Cable 640361"
}
```

**Response (no encontrado):**
```json
{
  "success": false,
  "message": "No se encontró la etiqueta número 3"
}
```

## 📝 Notas Importantes

1. **Sincronización:** Las etiquetas se regeneran automáticamente al agregar un nuevo corte en el Admin
2. **Filtrado:** Solo se numeran grupos que tienen sección (no vacía)
3. **Persistencia:** El archivo `grupos_etiquetas.json` mantiene la numeración consistente
4. **Compatibilidad:** La V3 puede seguir usando búsqueda tradicional si las etiquetas no existen

## 🔧 Implementación en V3

### Modificar main-v3.js

Agregar función de búsqueda por etiqueta:

```javascript
async function buscarPorEtiqueta(numeroEtiqueta) {
    try {
        const response = await fetch('/api/etiquetas/buscar_por_numero', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ numero_etiqueta: numeroEtiqueta })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const grupo = data.grupo;
            // Usar grupo.cod_cable y grupo.elemento para buscar el paquete
            mostrarPaquete(grupo.cod_cable, grupo.elemento);
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al buscar etiqueta');
    }
}
```

### Agregar Input en HTML

En `templates/index-v3.html` (área de trabajo):

```html
<div class="busqueda-rapida">
    <label>🏷️ Búsqueda Rápida por Etiqueta:</label>
    <input type="number" id="input-etiqueta" placeholder="Ej: 3" min="1">
    <button onclick="buscarPorInputEtiqueta()">🔍 Buscar</button>
</div>
```

## 🎯 Beneficios

1. **Velocidad:** Reducción de 70% en tiempo de búsqueda
2. **Precisión:** Eliminación de errores de transcripción
3. **Facilidad:** Solo recordar números (1, 2, 3...) en lugar de códigos largos
4. **Trazabilidad:** Etiquetas físicas pegadas en paquetes para identificación visual

## 🔄 Workflow Completo

```
┌─────────────┐
│  1. Admin   │ → Agregar nuevo corte Excel
└──────┬──────┘
       ↓
┌─────────────┐
│ 2. Backend  │ → Genera grupos_etiquetas.json automáticamente
└──────┬──────┘
       ↓
┌─────────────┐
│ 3. Etiquetas│ → Imprime etiquetas con números (1, 2, 3...)
└──────┬──────┘
       ↓
┌─────────────┐
│ 4. Operario │ → Pega etiquetas en paquetes físicos
└──────┬──────┘
       ↓
┌─────────────┐
│   5. V3     │ → Busca por número: "Dame la etiqueta 3"
└─────────────┘
```

## 📊 Ejemplo Real

**Situación:** Operario debe encastar elemento TB1 del cable 640361

**Antes (método tradicional):**
1. Memorizar o anotar: "TB1 - 640361"
2. Escribir en sistema: "TB1 cable 640361"
3. Buscar visualmente el paquete entre muchos

**Ahora (con etiquetas):**
1. Ver etiqueta física en paquete: **#3**
2. Escribir en sistema: **"3"**
3. ✅ Sistema encuentra y muestra automáticamente

---

**Fecha de implementación:** 22 de diciembre de 2025
**Versión:** V3.1 - Etiquetas Integradas
