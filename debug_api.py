"""
Script para debugear lo que devuelve la API
"""
from app.excel_manager import ExcelManager

# Crear instancia del manager
manager = ExcelManager(
    upload_folder='data/cortes',
    codigos_file='data/codigos_cortes.json',
    default_sheet='Format'
)

# Cargar el archivo
archivo = 'LISTADO_CABLEADO_CORADIA_ITALIA_APANTALLADOS.xlsx'
print(f"Cargando archivo: {archivo}")
if manager.cargar_excel(archivo):
    print("✓ Archivo cargado correctamente")
else:
    print("✗ Error al cargar archivo")
    exit(1)

# Buscar terminal
terminal = '640204'
print(f"\nBuscando terminal: {terminal}")
resultados = manager.buscar_terminal(terminal)
print(f"Resultados encontrados: {len(resultados)}")

# Agrupar
print(f"\nAgrupando resultados...")
grupos = manager.agrupar_por_cable_elemento(resultados)
print(f"Grupos creados: {len(grupos)}")

# Calcular total de terminales
total_terminales = sum(grupo['num_terminales'] for grupo in grupos.values())
print(f"Total terminales: {total_terminales}")

# Mostrar algunos grupos
print("\n" + "="*80)
print("GRUPOS CREADOS:")
print("="*80)
for idx, (clave, grupo) in enumerate(grupos.items()):
    if idx < 5:  # Solo primeros 5
        print(f"\n{grupo['elemento']}:")
        print(f"  Cod. cable: {grupo['cod_cable']}")
        print(f"  Cables: {grupo['num_cables']}")
        print(f"  Terminales: {grupo['num_terminales']}")
        print(f"  Cables en rojo: {len(grupo['cables_doble_terminal'])}")
