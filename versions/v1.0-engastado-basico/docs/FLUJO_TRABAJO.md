# 🔄 FLUJO DE TRABAJO Y ARQUITECTURA DEL SISTEMA

## Fecha: 13 de noviembre de 2025

---

## 🎯 RESUMEN DEL PROCESO

El sistema debe gestionar múltiples archivos Excel de "cortes de cable" y guiar a los operarios mediante lectores de código de barras para identificar qué cables engastar.

---

## 📱 EQUIPAMIENTO

### Hardware:
- **Pistolas lectoras de código de barras**
- **Ordenadores/Tablets** con navegador web
- **Red local** (para acceso centralizado)

### Software:
- Aplicación web Python (Flask)
- Navegador web moderno

---

## 🔄 FLUJO COMPLETO DEL OPERARIO

```
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: IDENTIFICAR CORTE DE CABLE                         │
│  ─────────────────────────────────────────────────────────  │
│  Operario escanea código de barras del "corte de cable"    │
│  Sistema carga el archivo Excel correspondiente             │
│  Ejemplo: "LISTADO CABLEADO CORADIA ITALIA.xlsx"           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 2: ESCANEAR TERMINAL A ENGASTAR                       │
│  ─────────────────────────────────────────────────────────  │
│  Operario escanea código de barras del terminal            │
│  Ejemplo: "641M155" o "641H10056"                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 3: SISTEMA BUSCA Y FILTRA                             │
│  ─────────────────────────────────────────────────────────  │
│  Sistema busca el terminal en:                              │
│    - Columna "De Terminal"                                  │
│    - Columna "Para Terminal"                                │
│  Agrupa resultados por:                                     │
│    - Código de cable (Cod. cable)                          │
│    - Elemento (De Elemento / Para Elemento)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 4: MOSTRAR EN PANTALLA                                │
│  ─────────────────────────────────────────────────────────  │
│  Sistema muestra elementos que contienen el terminal        │
│  [PENDIENTE: Definir formato exacto de visualización]      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 5: OPERARIO EJECUTA ENGASTADO                         │
│  ─────────────────────────────────────────────────────────  │
│  Operario:                                                  │
│    1. Selecciona grupo de cables (ya preparados)           │
│    2. Realiza el engastado según instrucciones             │
│    3. [¿Confirma operación completada?]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ ORGANIZACIÓN DE CABLES (CONTEXTO IMPORTANTE)

### Cables Preparados y Agrupados:
Los operarios tienen los cables físicamente organizados por:

1. **Código de cable** (ej: 640C10024A)
2. **Elemento** (ej: MCMifB/P1, TB1, Q8)

**Implicación:** El sistema debe mostrar claramente esta agrupación para que el operario pueda identificar rápidamente el grupo correcto de cables.

---

## 💾 GESTIÓN DE MÚLTIPLES ARCHIVOS EXCEL

### Arquitectura propuesta:

```
data/
├── cortes/                          # Carpeta con todos los archivos
│   ├── CORADIA_ITALIA.xlsx
│   ├── PROYECTO_A.xlsx
│   ├── PROYECTO_B.xlsx
│   └── ...
└── codigos_cortes.json             # Mapeo código barras → archivo
```

### Archivo de mapeo (codigos_cortes.json):
```json
{
  "cortes": [
    {
      "codigo_barras": "CORADIA_IT_001",
      "archivo": "CORADIA_ITALIA.xlsx",
      "descripcion": "Listado Cableado Coradia Italia",
      "proyecto": "Coradia Italia"
    },
    {
      "codigo_barras": "PROYECTO_A_001",
      "archivo": "PROYECTO_A.xlsx",
      "descripcion": "Proyecto A - Lote 1",
      "proyecto": "Proyecto A"
    }
  ]
}
```

**❓ PENDIENTE:** Confirmar si esta estructura es adecuada o hay otra forma preferida.

---

## 🔍 LÓGICA DE BÚSQUEDA DEL TERMINAL

### Búsqueda en Excel:
```python
# Pseudocódigo
terminal_buscado = "641M155"  # Escaneado por el operario

# Buscar en ambas columnas
resultados_origen = df[df['De Terminal'] == terminal_buscado]
resultados_destino = df[df['Para Terminal'] == terminal_buscado]

# Combinar resultados
resultados_totales = pd.concat([resultados_origen, resultados_destino])

# Agrupar por Código de cable y Elemento
grupos = resultados_totales.groupby(['Cod. cable', 'De Elemento'])
```

**❓ PENDIENTE:** ¿Esta lógica es correcta o el terminal solo puede estar en una columna específica?

---

## 🖥️ PROPUESTA DE INTERFAZ (PANTALLA DE RESULTADOS)

### Opción A: Vista en Tarjetas
```
╔══════════════════════════════════════════════════════════════╗
║  TERMINAL ESCANEADO: 641M155                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📦 GRUPO 1: Cable 640C10024A - Elemento MCMifB/P1          ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │ Cables en este grupo: 3                                │ ║
║  │ Descripción: CABLE EN50306-2 1x1.0 mm2                │ ║
║  │ Sección: 1 | Longitud: 0.9m                           │ ║
║  │                                                        │ ║
║  │ Conexiones:                                            │ ║
║  │   • Cable/Marca 202 → TB1 (Pto. 3) - Terminal 641H... │ ║
║  │   • Cable/Marca 203 → TB1 (Pto. 4) - Terminal 641H... │ ║
║  │   • Cable/Marca 804 → Q8 (Pto. A1) - Terminal 640204  │ ║
║  └────────────────────────────────────────────────────────┘ ║
║                                                              ║
║  📦 GRUPO 2: Cable 640C10025B - Elemento TB2                ║
║  ┌────────────────────────────────────────────────────────┐ ║
║  │ [Similar formato...]                                   │ ║
║  └────────────────────────────────────────────────────────┘ ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Opción B: Vista en Tabla
```
╔══════════════════════════════════════════════════════════════╗
║  TERMINAL ESCANEADO: 641M155                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Cod.Cable  │ Elemento   │ Cable/Marca │ Destino           ║
║ ────────────┼────────────┼─────────────┼────────────────── ║
║  640C10024A │ MCMifB/P1  │ 202         │ TB1 (Pto. 3)     ║
║  640C10024A │ MCMifB/P1  │ 203         │ TB1 (Pto. 4)     ║
║  640C10024A │ MCMifB/P1  │ 804         │ Q8 (Pto. A1)     ║
║ ────────────┼────────────┼─────────────┼────────────────── ║
║  640C10025B │ TB2        │ 101         │ Q9 (Pto. B2)     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**❓ CRÍTICO:** ¿Qué formato es más útil para los operarios? ¿O prefieres otro diseño?

---

## 🔧 FUNCIONALIDADES TÉCNICAS NECESARIAS

### Backend:
- [x] Leer múltiples archivos Excel
- [ ] Sistema de mapeo código barras → archivo Excel
- [ ] Búsqueda de terminal en columnas específicas
- [ ] Agrupación por código de cable y elemento
- [ ] Filtrado y ordenamiento de resultados

### Frontend:
- [ ] Interfaz para escaneo de código de barras (input)
- [ ] Selección de corte de cable
- [ ] Visualización de resultados agrupados
- [ ] Interfaz responsive (tablets/PC)
- [ ] Feedback visual claro

### Integración:
- [ ] Soporte para pistolas lectoras USB (input como teclado)
- [ ] Detección automática de escaneos
- [ ] Tiempo de respuesta rápido

---

## ❓ PREGUNTAS TÉCNICAS ADICIONALES

### Pistolas lectoras:
1. ¿Las pistolas envían el código seguido de ENTER automáticamente?
2. ¿O hay que presionar un botón para confirmar?
3. ¿Formato del código de barras? (numérico, alfanumérico, longitud)

### Interfaz:
4. ¿Pantalla táctil o solo teclado/ratón?
5. ¿Tamaño de pantalla típico?
6. ¿Necesitan ver toda la información de una vez o puede haber scroll?

### Operación:
7. ¿Después de ver las instrucciones, el operario tiene que confirmar algo?
8. ¿O simplemente escanea el siguiente terminal?
9. ¿Hay botón de "volver atrás" o "cancelar"?

---

## 📝 PRÓXIMOS PASOS PRIORITARIOS

1. ⏳ **Confirmar formato de pantalla** (Opción A, B, u otra)
2. ⏳ **Definir sistema de mapeo** de códigos de barras a archivos Excel
3. ⏳ **Confirmar columnas de búsqueda** (¿ambas o solo una?)
4. ⏳ **Definir interacción** con pistolas lectoras
5. ✅ Iniciar desarrollo del prototipo

---

*Documento actualizado: 13/11/2025*
*Esperando confirmación de usuario para continuar con implementación*
