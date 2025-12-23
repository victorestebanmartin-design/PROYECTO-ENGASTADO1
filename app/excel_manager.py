"""
Gestor de archivos Excel para el sistema de engastado
"""
import pandas as pd
import openpyxl
import os
import json
from typing import Dict, List, Optional

class ExcelManager:
    def __init__(self, upload_folder: str, codigos_file: str, default_sheet: str = 'Format'):
        self.upload_folder = upload_folder
        self.codigos_file = codigos_file
        self.default_sheet = default_sheet
        self.current_df = None
        self.current_file = None
        
        # Crear archivo de códigos si no existe
        if not os.path.exists(self.codigos_file):
            self._init_codigos_file()

        # Intentar cargar automáticamente el último archivo usado si existe
        self._try_autoload_last_file()

    def _last_loaded_path(self) -> str:
        """Ruta del archivo que guarda el último Excel cargado"""
        base_dir = os.path.dirname(self.codigos_file) or '.'
        return os.path.join(base_dir, 'last_loaded.json')

    def _save_last_loaded(self, nombre_archivo: str) -> None:
        """Guardar el último archivo Excel cargado para autoload futuro"""
        try:
            payload = {"archivo": nombre_archivo}
            with open(self._last_loaded_path(), 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"No se pudo guardar last_loaded: {e}")

    def _try_autoload_last_file(self) -> None:
        """Intentar cargar el último archivo usado o un único archivo disponible"""
        try:
            last_path = self._last_loaded_path()
            if os.path.exists(last_path):
                with open(last_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    archivo = data.get('archivo')
                    if archivo:
                        self.cargar_excel(archivo)
                        return
            # Si no hay last_loaded, pero hay exactamente un archivo en la carpeta, cargarlo
            if os.path.isdir(self.upload_folder):
                archivos = [f for f in os.listdir(self.upload_folder) if os.path.isfile(os.path.join(self.upload_folder, f))]
                if len(archivos) == 1:
                    self.cargar_excel(archivos[0])
        except Exception as e:
            print(f"No se pudo autoload el último archivo: {e}")
    
    def _init_codigos_file(self):
        """Inicializar archivo de códigos de barras"""
        initial_data = {"cortes": []}
        with open(self.codigos_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    def get_cortes(self) -> List[Dict]:
        """Obtener lista de cortes registrados"""
        if os.path.exists(self.codigos_file):
            with open(self.codigos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('cortes', [])
        return []
    
    def add_corte(self, codigo_barras: str, archivo: str, descripcion: str, proyecto: str = "") -> bool:
        """Agregar nuevo corte de cable"""
        cortes = self.get_cortes()
        
        # Verificar que el código no exista ya
        if any(c['codigo_barras'] == codigo_barras for c in cortes):
            return False
        
        # Agregar nuevo corte
        nuevo_corte = {
            "codigo_barras": codigo_barras,
            "archivo": archivo,
            "descripcion": descripcion,
            "proyecto": proyecto
        }
        
        cortes.append(nuevo_corte)
        
        # Guardar
        with open(self.codigos_file, 'w', encoding='utf-8') as f:
            json.dump({"cortes": cortes}, f, indent=2, ensure_ascii=False)
        
        return True
    
    def delete_corte(self, codigo_barras: str) -> bool:
        """Eliminar corte de cable por código de barras"""
        cortes = self.get_cortes()
        
        # Buscar y eliminar el corte
        cortes_filtrados = [c for c in cortes if c['codigo_barras'] != codigo_barras]
        
        # Si no cambió nada, el código no existía
        if len(cortes_filtrados) == len(cortes):
            return False
        
        # Guardar
        with open(self.codigos_file, 'w', encoding='utf-8') as f:
            json.dump({"cortes": cortes_filtrados}, f, indent=2, ensure_ascii=False)
        
        return True
    
    def delete_file(self, filename: str) -> bool:
        """Eliminar archivo Excel físico"""
        filepath = os.path.join(self.upload_folder, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
                return False
        return False
    
    def reset_system(self) -> bool:
        """Resetear todo el sistema: eliminar todos los archivos y códigos"""
        try:
            # Eliminar todos los archivos Excel
            if os.path.exists(self.upload_folder):
                for filename in os.listdir(self.upload_folder):
                    filepath = os.path.join(self.upload_folder, filename)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
            
            # Resetear archivo de códigos
            self._init_codigos_file()

            # Eliminar memoria del último archivo usado
            try:
                last_path = self._last_loaded_path()
                if os.path.exists(last_path):
                    os.remove(last_path)
            except Exception as e:
                print(f"No se pudo borrar last_loaded: {e}")
            
            # Limpiar DataFrame actual
            self.current_df = None
            self.current_file = None
            
            return True
        except Exception as e:
            print(f"Error al resetear sistema: {e}")
            return False
    
    def get_archivo_by_codigo(self, codigo_barras: str) -> Optional[str]:
        """Obtener nombre de archivo por código de barras"""
        cortes = self.get_cortes()
        for corte in cortes:
            if corte['codigo_barras'] == codigo_barras:
                return corte['archivo']
        return None
    
    def cargar_excel(self, nombre_archivo: str, sheet_name: Optional[str] = None) -> bool:
        """Cargar archivo Excel"""
        filepath = os.path.join(self.upload_folder, nombre_archivo)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            sheet = sheet_name or self.default_sheet
            self.current_df = pd.read_excel(filepath, sheet_name=sheet)
            self.current_file = nombre_archivo
            # Recordar este archivo para futuras sesiones
            self._save_last_loaded(nombre_archivo)
            return True
        except Exception as e:
            print(f"Error al cargar Excel: {e}")
            return False
    
    def cargar_excel_directo(self, nombre_archivo: str, sheet_name: Optional[str] = None) -> bool:
        """Cargar archivo Excel sin guardar como último archivo (para procesamiento temporal)"""
        filepath = os.path.join(self.upload_folder, nombre_archivo)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            sheet = sheet_name or self.default_sheet
            self.current_df = pd.read_excel(filepath, sheet_name=sheet)
            self.current_file = nombre_archivo
            # NO guardar en last_loaded ya que es una carga temporal
            return True
        except Exception as e:
            print(f"Error al cargar Excel: {e}")
            return False

    def cargar_ultimo_si_existe(self) -> bool:
        """Cargar el último Excel utilizado si no hay uno en memoria"""
        if self.current_df is not None:
            return True
        try:
            last_path = self._last_loaded_path()
            if os.path.exists(last_path):
                with open(last_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    archivo = data.get('archivo')
                    if archivo:
                        return self.cargar_excel(archivo)
        except Exception as e:
            print(f"Error al cargar último archivo: {e}")
        return False
    
    def cargar_por_codigo(self, codigo_barras: str) -> bool:
        """Cargar archivo Excel usando código de barras"""
        archivo = self.get_archivo_by_codigo(codigo_barras)
        if archivo:
            return self.cargar_excel(archivo)
        return False
    
    def buscar_terminal(self, terminal: str) -> List[Dict]:
        """
        Buscar terminal en las columnas 'De Terminal' y 'Para Terminal'
        Retorna lista de diccionarios con los datos encontrados
        BÚSQUEDA INSENSIBLE A MAYÚSCULAS/MINÚSCULAS
        """
        if self.current_df is None:
            return []
        
        # Convertir terminal a mayúsculas para búsqueda
        terminal_upper = str(terminal).upper().strip()
        
        # Preparar máscaras seguras incluso si faltan columnas
        cols = self.current_df.columns
        
        if 'De Terminal' in cols:
            mask_origen = self.current_df['De Terminal'].astype(str).str.upper() == terminal_upper
        else:
            mask_origen = pd.Series(False, index=self.current_df.index)
        
        if 'Para Terminal' in cols:
            mask_destino = self.current_df['Para Terminal'].astype(str).str.upper() == terminal_upper
        else:
            mask_destino = pd.Series(False, index=self.current_df.index)

        # Seleccionar filas que coincidan en ORIGEN o DESTINO (una sola vez por fila)
        mask_any = mask_origen | mask_destino
        if not mask_any.any():
            return []

        df = self.current_df[mask_any].copy()

        # Etiquetar el tipo de coincidencia por fila: origen, destino o ambas
        tipo = pd.Series(index=self.current_df.index, dtype=object)
        tipo[(mask_origen) & (~mask_destino)] = 'origen'
        tipo[(~mask_origen) & (mask_destino)] = 'destino'
        tipo[(mask_origen) & (mask_destino)] = 'ambas'
        df['tipo_conexion'] = tipo.loc[df.index].fillna('origen')

        return df.to_dict('records')
    
    def agrupar_por_cable_elemento(self, resultados: List[Dict], terminal_buscado: str) -> Dict:
        """
        Agrupar resultados por código de cable y elemento (De Elemento)
        
        REGLAS:
        1. Agrupar por Código de Cable + De Elemento (como los corta la máquina)
        2. Un mismo cable puede aparecer VARIAS VECES en el mismo elemento (cables duplicados)
        3. AZUL: terminal solo en un lado (1 terminal)
        4. ROJO: terminal en AMBOS lados (2 terminales en la MISMA fila)
        5. Total esperado: ~98 cables mostrados, 150 terminales
        """
        if not resultados:
            return {}
        
        grupos = {}
        
        # Helper para evitar NaN/None en JSON
        def _safe_str(v):
            try:
                import pandas as _pd
                if _pd.isna(v):
                    return ''
            except Exception:
                pass
            return '' if v is None else v
        
        def _safe_num(v):
            try:
                import pandas as _pd
                if _pd.isna(v):
                    return ''
            except Exception:
                pass
            return v
        
        for row in resultados:
            # Datos de la fila
            cod_cable = row.get('Cod. cable', 'Sin código')
            cable_marca = str(row.get('Cable / Marca', '')).strip()
            de_elemento = row.get('De Elemento', 'Sin elemento')
            de_terminal = row.get('De Terminal', '')
            para_terminal = row.get('Para Terminal', '')
            
            # Clave del grupo
            clave = f"{cod_cable}|{de_elemento}"

            if clave not in grupos:
                # Buscar columnas por nombre normalizado (sin acentos/casos) para tolerar problemas de codificación
                def _get_by_normalized_key(d: Dict, target: str, default=''):
                    try:
                        import unicodedata as _ud
                        def _norm(s: str) -> str:
                            s = ''.join(c for c in _ud.normalize('NFKD', s) if not _ud.combining(c))
                            return s.lower().strip()
                        target_norm = _norm(target)
                        for k in d.keys():
                            try:
                                if _norm(str(k)) == target_norm:
                                    return d.get(k, default)
                            except Exception:
                                continue
                    except Exception:
                        pass
                    return default

                descripcion_val = _get_by_normalized_key(row, 'Descripción Cable', '')
                seccion_val = _get_by_normalized_key(row, 'Sección', '')

                grupos[clave] = {
                    'cod_cable': _safe_str(cod_cable),
                    'elemento': _safe_str(de_elemento),
                    'descripcion': _safe_str(descripcion_val),
                    'seccion': _safe_str(seccion_val),
                    'longitud': _safe_num(row.get('Longitud', '')),
                    'de_terminal': _safe_str(de_terminal),
                    'cables_lista': [],
                    'cables_doble_terminal': [],  # ROJO: terminal en ambas puntas (DE ESTA FILA)
                    'cables_de_terminal': [],     # AZUL: terminal solo en "De Terminal"
                    'cables_para_terminal': [],   # VERDE: terminal solo en "Para Terminal"
                    'num_terminales': 0
                }

            if cable_marca:
                # Verificar si ESTA FILA tiene el terminal en ambos lados (CASE-INSENSITIVE)
                terminal_buscado_upper = str(terminal_buscado).upper().strip()
                de_terminal_upper = str(de_terminal).upper().strip()
                para_terminal_upper = str(para_terminal).upper().strip()
                
                tiene_origen = de_terminal_upper == terminal_buscado_upper
                tiene_destino = para_terminal_upper == terminal_buscado_upper
                es_doble_en_esta_fila = tiene_origen and tiene_destino
                
                # Agregar cable a la lista (puede aparecer múltiples veces)
                grupos[clave]['cables_lista'].append(cable_marca)
                
                if es_doble_en_esta_fila:
                    # Esta fila tiene terminal en AMBOS lados (ROJO) - 2 terminales
                    grupos[clave]['cables_doble_terminal'].append(cable_marca)
                    grupos[clave]['num_terminales'] += 2
                elif tiene_origen:
                    # Esta fila tiene terminal solo en "De Terminal" (AZUL) - 1 terminal
                    grupos[clave]['cables_de_terminal'].append(cable_marca)
                    grupos[clave]['num_terminales'] += 1
                elif tiene_destino:
                    # Esta fila tiene terminal solo en "Para Terminal" (VERDE) - 1 terminal
                    grupos[clave]['cables_para_terminal'].append(cable_marca)
                    grupos[clave]['num_terminales'] += 1
        
        # Ordenar cables y preparar datos finales
        for grupo in grupos.values():
            def sort_cable(cable):
                cable_str = str(cable).strip()
                try:
                    return (0, int(cable_str))  # Números primero
                except ValueError:
                    return (1, cable_str)  # Strings después
            
            grupo['todos_cables'] = sorted(grupo['cables_lista'], key=sort_cable)
            grupo['num_cables'] = len(grupo['cables_lista'])
            
            # Limpiar
            del grupo['cables_lista']
        
        return grupos
    
    def get_columnas(self) -> List[str]:
        """Obtener nombres de columnas del DataFrame actual"""
        if self.current_df is not None:
            return list(self.current_df.columns)
        return []
    
    def get_hojas_disponibles(self, nombre_archivo: str) -> List[str]:
        """Obtener nombres de hojas de un archivo Excel"""
        filepath = os.path.join(self.upload_folder, nombre_archivo)
        if os.path.exists(filepath):
            try:
                excel_file = pd.ExcelFile(filepath)
                return excel_file.sheet_names
            except:
                return []
        return []
    
    def listar_terminales_unicos(self) -> List[str]:
        """
        Obtener lista de todos los terminales únicos en el Excel actual
        (De Terminal y Para Terminal), excluyendo 'S/T' y valores vacíos
        """
        if self.current_df is None:
            return []
        
        terminales = set()
        
        # Obtener terminales de origen
        if 'De Terminal' in self.current_df.columns:
            for terminal in self.current_df['De Terminal'].dropna().unique():
                terminal_str = str(terminal).strip().upper()
                if terminal_str and terminal_str != 'S/T' and terminal_str != 'NAN':
                    terminales.add(terminal_str)
        
        # Obtener terminales de destino
        if 'Para Terminal' in self.current_df.columns:
            for terminal in self.current_df['Para Terminal'].dropna().unique():
                terminal_str = str(terminal).strip().upper()
                if terminal_str and terminal_str != 'S/T' and terminal_str != 'NAN':
                    terminales.add(terminal_str)
        
        # Ordenar alfabéticamente
        return sorted(list(terminales))

    def buscar_elementos_por_codigo_cable(self, codigo_cable: str) -> List[Dict]:
        """
        Buscar todos los elementos (De Elemento) asociados a un código de cable específico
        Retorna lista de diccionarios con: elemento, descripción, cantidad, terminal
        """
        if self.current_df is None:
            return []
        
        codigo_cable_upper = str(codigo_cable).upper().strip()
        
        # Filtrar por código de cable
        if 'Cod. cable' not in self.current_df.columns:
            return []
        
        mask = self.current_df['Cod. cable'].astype(str).str.upper().str.strip() == codigo_cable_upper
        df_filtrado = self.current_df[mask].copy()
        
        if df_filtrado.empty:
            return []
        
        # Agrupar por 'De Elemento' y contar
        elementos_dict = {}
        
        for _, row in df_filtrado.iterrows():
            elemento = row.get('De Elemento', 'Sin elemento')
            if pd.isna(elemento):
                elemento = 'Sin elemento'
            
            elemento = str(elemento).strip()
            
            if elemento not in elementos_dict:
                elementos_dict[elemento] = {
                    'elemento': elemento,
                    'descripcion': str(row.get('De Descripción', '')).strip() if not pd.isna(row.get('De Descripción')) else '',
                    'terminal': str(row.get('De Terminal', '')).strip() if not pd.isna(row.get('De Terminal')) else '',
                    'cantidad': 0
                }
            
            elementos_dict[elemento]['cantidad'] += 1
        
        # Convertir a lista
        elementos_lista = list(elementos_dict.values())
        
        # Ordenar por elemento
        elementos_lista.sort(key=lambda x: x['elemento'])
        
        return elementos_lista

