# Versión 2.0 - Modo Interactivo (Respaldo)

## Descripción
Sistema de engastado interactivo con flujo guiado paso a paso.

## Características V2.0
- Selección visual de terminales con tarjetas
- Pantalla de preparación con temporizador
- Progreso por terminal (completado/en curso/pendiente)
- Pausa automática con Enter para continuar
- Grupos de terminales por colores:
  - **Azul**: Solo "De Terminal"
  - **Verde**: Solo "Para Terminal" 
  - **Rojo**: Ambos lados (doble terminal)
- Cables con tamaño grande y prominente
- Timer minimalista
- Reanudación de progreso en memoria
- Botón "Volver" que preserva progreso

## Archivos principales V2.0
- `main-v2.js` - Lógica JavaScript de la interfaz interactiva
- `style-v2.css` - Estilos específicos para V2
- `index-v2.html` - Template HTML para la interfaz

## Rutas
- Acceso: `/v2`
- Función: `index_v2()` en routes.py

## Estado
✅ **FUNCIONAL Y OPERATIVO**
- Fecha respaldo: 26 noviembre 2025
- Última actualización: Cables grandes + timer minimalista
- Listo para producción

## Notas técnicas
- Backend usa `cables_de_terminal`, `cables_para_terminal`, `cables_doble_terminal`
- Frontend renderiza 3 grupos de colores separados
- Timer: 3 segundos × número de terminales
- Progreso guardado en `progresoGuardado` (memoria)