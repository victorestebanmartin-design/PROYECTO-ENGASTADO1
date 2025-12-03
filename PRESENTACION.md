PRESENTACIÓN: Sistema de Engastado Automático
=============================================

Objetivo
--------
Explicar de forma sencilla qué hace el software, para quién es y cómo se usa.

Resumen corto (1 frase)
-----------------------
Una aplicación que guía a los operarios en el proceso de engastado de terminales y permite a los administradores gestionar los terminales y los archivos Excel de entrada.

Público objetivo
----------------
- Operarios de taller sin conocimientos técnicos.
- Responsables de producción.
- Administradores que gestionan archivos Excel y configuran terminales.

Por qué es útil
---------------
- Reduce errores humanos en el proceso repetitivo de engastado.
- Ordena el trabajo en paquetes y pasos claros.
- Permite activar/desactivar terminales que no se usan y controlar el inventario por Excel.

Flujo de uso (texto para demo)
------------------------------
1. Abrir la app en el navegador en la máquina de trabajo: `http://localhost:5000/v2`.
2. Seleccionar la tarjeta del terminal que queremos preparar.
3. Verás la pantalla de preparación con información en grande y un temporizador.
4. Preparar la cantidad indicada y presionar `Enter` o dejar que el temporizador avance.
5. La tarjeta marcará el progreso y pasará a completada cuando termines.

Modos disponibles
-----------------
- V1 (básico): búsqueda rápida y agrupado desde Excel.
- V2 (interactivo): flujo guiado paso a paso con temporizador y reanudación.

La vista de administración (`/admin`)
------------------------------------
- Subir archivos Excel.
- Asociar códigos de barras a archivos.
- Cargar y ver terminales detectados.
- Tres indicadores arriba: archivos procesados, archivos con error, total de terminales (visualizados como badges).
- Grid de terminales debajo: tarjetas con estado (Activo / Desactivado) y botones para alternar.

Archivos y rutas importantes
---------------------------
- `run.py` — inicia la aplicación.
- `requirements.txt` — dependencias de Python.
- `app/routes.py` — endpoints del servidor.
- `app/excel_manager.py` — lectura y procesamiento de Excel.
- `static/js/admin.js` — código del panel de administración.
- `static/js/main-v2.js` — flujo interactivo V2.
- `static/css/style.css` — estilos principales (y `style-v1.css`/`style-v2.css`).
- `data/codigos_cortes.json` — mapea códigos a archivos Excel.
- `terminales_desactivados.json` — persiste estados desactivados.

Cómo arrancar (Windows / PowerShell)
-----------------------------------
1. Crear y activar entorno (opcional):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Ejecutar la app:

```powershell
python run.py
```

4. Abrir en el navegador:
- V1: `http://localhost:5000/`
- V2: `http://localhost:5000/v2`
- Admin: `http://localhost:5000/admin`

Recomendaciones para el operario
--------------------------------
- Usa pantalla legible y coloca el ordenador cerca de la mesa de trabajo.
- Sigue las indicaciones grandes en V2: texto y temporizador.
- Si falta un terminal, avisar al administrador para que lo active o revise el Excel.

Preguntas frecuentes (FAQ)
--------------------------
Q: ¿Se pierde el progreso si se cierra la página?
A: El progreso se guarda en memoria en la sesión; para persistencia por turno se puede añadir una base de datos.

Q: ¿Qué pasa si el Excel está mal formado?
A: `/admin` muestra archivos con error en el badge "Archivos con Error". Subir el Excel corregido y volver a asociar.

Siguientes pasos sugeridos
-------------------------
- Guardado de progreso en base de datos por usuario.
- Exportar reportes por turno.
- Integrar escáner de códigos para selección automática de terminal.
- Control de usuarios/roles.

Notas para la demo en vivo
-------------------------
- Abrir `/admin` para mostrar cómo se sube un Excel y cómo aparecen los badges.
- Cargar V2 y seleccionar un terminal para mostrar el temporizador y el avance automático.
- Mostrar cómo desactivar un terminal y ver que desaparece de la selección de operario.

Contacto para dudas técnicas
----------------------------
- Repositorio local: carpeta del proyecto (archivo `README.md` contiene más detalles).
- Para soporte, preguntar al desarrollador responsable (mostrar correo/usuario si aplica).
