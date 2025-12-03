"""
Script para analizar el terminal 640204 en el Excel
"""
import pandas as pd

# Cargar Excel
df = pd.read_excel('data/cortes/LISTADO_CABLEADO_CORADIA_ITALIA_APANTALLADOS.xlsx', sheet_name='Format')

print("="*80)
print("ANÁLISIS DEL TERMINAL 640204")
print("="*80)

# Buscar terminal
terminal = '640204'
mask_origen = df['De Terminal'] == terminal
mask_destino = df['Para Terminal'] == terminal
mask_total = mask_origen | mask_destino

print(f"\nTotal de filas en el Excel: {len(df)}")
print(f"Filas donde aparece {terminal}: {mask_total.sum()}")
print(f"  - Como 'De Terminal' (origen): {mask_origen.sum()}")
print(f"  - Como 'Para Terminal' (destino): {mask_destino.sum()}")

# Contar cuántas tienen el terminal en AMBOS lados
mask_ambos = mask_origen & mask_destino
print(f"  - En AMBOS lados (mismo terminal): {mask_ambos.sum()}")

# Ver primera fila de ejemplo
print("\n" + "="*80)
print("PRIMERA FILA DE EJEMPLO:")
print("="*80)
if mask_total.any():
    primera = df[mask_total].iloc[0]
    print(f"De Elemento: {primera['De Elemento']}")
    print(f"De Terminal: {primera['De Terminal']}")
    print(f"Para Elemento: {primera['Para Elemento']}")
    print(f"Para Terminal: {primera['Para Terminal']}")
    print(f"Cable / Marca: {primera['Cable / Marca']}")
    print(f"Cod. cable: {primera['Cod. cable']}")

# Agrupar por elemento de ORIGEN
print("\n" + "="*80)
print("AGRUPACIÓN POR ELEMENTO DE ORIGEN (De Elemento):")
print("="*80)
df_origen = df[mask_origen].copy()
if len(df_origen) > 0:
    grupos_origen = df_origen.groupby('De Elemento').size()
    print(f"\nTotal cables desde elementos de origen: {len(df_origen)}")
    print("\nCables por elemento:")
    for elem, count in grupos_origen.items():
        print(f"  {elem}: {count} cables")
    print(f"\nSUMA TOTAL: {grupos_origen.sum()} cables")

# Ver si hay elementos destino también
print("\n" + "="*80)
print("AGRUPACIÓN POR ELEMENTO DE DESTINO (Para Elemento):")
print("="*80)
df_destino = df[mask_destino].copy()
if len(df_destino) > 0:
    grupos_destino = df_destino.groupby('Para Elemento').size()
    print(f"\nTotal cables hacia elementos de destino: {len(df_destino)}")
    print("\nCables por elemento:")
    for elem, count in grupos_destino.items():
        print(f"  {elem}: {count} cables")
    print(f"\nSUMA TOTAL: {grupos_destino.sum()} cables")

# Casos especiales: mismo terminal en ambas puntas
print("\n" + "="*80)
print("CASOS CON TERMINAL EN AMBAS PUNTAS:")
print("="*80)
df_ambos = df[mask_ambos].copy()
if len(df_ambos) > 0:
    print(f"Total: {len(df_ambos)} cables")
    print("\nEjemplos:")
    for idx, row in df_ambos.head(3).iterrows():
        print(f"  {row['De Elemento']} -> {row['Para Elemento']} | Cable: {row['Cable / Marca']}")
else:
    print("No hay casos con el mismo terminal en ambas puntas")
