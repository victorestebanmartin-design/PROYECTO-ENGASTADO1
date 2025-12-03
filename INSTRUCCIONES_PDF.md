INSTRUCCIONES PARA GENERAR PDF DE LA PRESENTACIÓN
=================================================

Opciones sencillas (recomendado)
--------------------------------
1. Abrir `presentation.html` en el navegador (doble click o `http://localhost:5000/presentation.html` si lo sirves desde Flask).
2. Hacer Archivo → Imprimir (o `Ctrl+P`).
3. Elegir "Guardar como PDF" o "Microsoft Print to PDF".
4. Ajustar tamaño a "A4" y márgenes a "Predeterminado" o "Ninguno" si quieres aprovechar todo el espacio.
5. Guardar el PDF.

Opción con herramienta (wkhtmltopdf)
------------------------------------
Si prefieres convertir desde terminal con `wkhtmltopdf`:

1. Instalar wkhtmltopdf (ejemplo en Windows con chocolatey):

```powershell
choco install wkhtmltopdf
```

2. Ejecutar la conversión:

```powershell
wkhtmltopdf presentation.html PRESENTACION.pdf
```

Opción con Python (weasyprint)
------------------------------
Puedes usar `weasyprint` si lo prefieres (requiere dependencias adicionales):

```powershell
pip install weasyprint
python - <<'PY'
from weasyprint import HTML
HTML('presentation.html').write_pdf('PRESENTACION.pdf')
PY
```

Notas
-----
- Si abres `presentation.html` localmente en el navegador y las fuentes o estilos no se ven bien, simplemente abrir el archivo desde el servidor Flask también funciona (colocar `presentation.html` en la raíz del `static` o servirlo como template).
- La versión HTML está configurada con tamaño A4 y saltos de página (cada "slide" ocupa una página al imprimir).

Si quieres, puedo intentar generar el PDF aquí si me autorizas a instalar y ejecutar una herramienta para convertir (pero normalmente lo más rápido es que lo generes localmente con el navegador).