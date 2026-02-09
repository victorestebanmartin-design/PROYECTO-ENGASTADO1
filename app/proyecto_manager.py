import json
import os
from datetime import datetime
from config import Config
from app.excel_manager import ExcelManager

class ProyectoManager:
    """Gestor de proyectos y asignación a carros"""
    
    def __init__(self):
        self.archivo_proyectos = Config.PROYECTOS_FILE
        self.cargar_proyectos()
    
    def cargar_proyectos(self):
        """Cargar proyectos desde archivo JSON"""
        if os.path.exists(self.archivo_proyectos):
            with open(self.archivo_proyectos, 'r', encoding='utf-8') as f:
                self.proyectos = json.load(f)
        else:
            self.proyectos = {
                'proyectos': [],
                'carros': {str(i): None for i in range(1, Config.NUM_CARROS + 1)}
            }
            self.guardar_proyectos()
    
    def guardar_proyectos(self):
        """Guardar proyectos en archivo JSON"""
        os.makedirs(os.path.dirname(self.archivo_proyectos), exist_ok=True)
        with open(self.archivo_proyectos, 'w', encoding='utf-8') as f:
            json.dump(self.proyectos, f, indent=2, ensure_ascii=False)
    
    def agregar_proyecto(self, nombre, archivo_excel, carro=None):
        """Agregar nuevo proyecto"""
        proyecto = {
            'id': len(self.proyectos['proyectos']) + 1,
            'nombre': nombre,
            'archivo': archivo_excel,
            'fecha_carga': datetime.now().isoformat(),
            'carro_asignado': carro,
            'progreso': 0,
            'terminales_completados': [],
            'estado': 'activo'
        }
        
        self.proyectos['proyectos'].append(proyecto)
        
        # Asignar a carro si se especifica
        if carro:
            self.asignar_carro(proyecto['id'], carro)
        
        self.guardar_proyectos()
        return proyecto
    
    def asignar_carro(self, proyecto_id, carro):
        """Asignar proyecto a un carro"""
        carro_str = str(carro)
        
        # Actualizar proyecto
        for p in self.proyectos['proyectos']:
            if p['id'] == proyecto_id:
                p['carro_asignado'] = carro
                break
        
        # Actualizar carro
        self.proyectos['carros'][carro_str] = proyecto_id
        self.guardar_proyectos()
    
    def liberar_carro(self, carro):
        """Liberar un carro"""
        carro_str = str(carro)
        proyecto_id = self.proyectos['carros'][carro_str]
        
        if proyecto_id:
            # Desasignar del proyecto
            for p in self.proyectos['proyectos']:
                if p['id'] == proyecto_id:
                    p['carro_asignado'] = None
                    break
        
        self.proyectos['carros'][carro_str] = None
        self.guardar_proyectos()
    
    def eliminar_proyecto(self, proyecto_id):
        """Eliminar un proyecto"""
        # Liberar carro si está asignado
        for p in self.proyectos['proyectos']:
            if p['id'] == proyecto_id and p['carro_asignado']:
                self.liberar_carro(p['carro_asignado'])
                break
        
        # Eliminar proyecto
        self.proyectos['proyectos'] = [
            p for p in self.proyectos['proyectos'] 
            if p['id'] != proyecto_id
        ]
        self.guardar_proyectos()
    
    def obtener_proyectos(self):
        """Obtener todos los proyectos"""
        return self.proyectos['proyectos']
    
    def obtener_proyecto(self, proyecto_id):
        """Obtener un proyecto específico"""
        for p in self.proyectos['proyectos']:
            if p['id'] == proyecto_id:
                return p
        return None
    
    def obtener_carros(self):
        """Obtener estado de todos los carros"""
        carros_info = []
        for num_carro in range(1, Config.NUM_CARROS + 1):
            carro_str = str(num_carro)
            proyecto_id = self.proyectos['carros'][carro_str]
            
            info = {
                'numero': num_carro,
                'ocupado': proyecto_id is not None,
                'proyecto_id': proyecto_id,
                'proyecto_nombre': None,
                'progreso': 0
            }
            
            if proyecto_id:
                proyecto = self.obtener_proyecto(proyecto_id)
                if proyecto:
                    info['proyecto_nombre'] = proyecto['nombre']
                    info['progreso'] = proyecto.get('progreso', 0)
            
            carros_info.append(info)
        
        return carros_info
    
    def actualizar_progreso(self, proyecto_id, terminal_completado):
        """Actualizar progreso de un proyecto"""
        for p in self.proyectos['proyectos']:
            if p['id'] == proyecto_id:
                if terminal_completado not in p['terminales_completados']:
                    p['terminales_completados'].append(terminal_completado)
                # El progreso se calculará en base a terminales completados
                self.guardar_proyectos()
                break

    def generar_nombre_bono_sugerido(self):
        """Generar nombre sugerido para nuevo bono"""
        from datetime import datetime
        
        if 'bonos' not in self.proyectos:
            self.proyectos['bonos'] = {}
        
        fecha = datetime.now().strftime('%Y%m%d')
        
        # Contar cuántos bonos existen hoy
        contador = 1
        for bono in self.proyectos['bonos'].values():
            if bono['nombre'].startswith(fecha):
                # Extraer el número del sufijo _X
                try:
                    partes = bono['nombre'].split('_')
                    if len(partes) > 1:
                        num = int(partes[-1])
                        if num >= contador:
                            contador = num + 1
                except:
                    pass
        
        return f"{fecha}_{contador}"
    
    def generar_bono(self, nombre_bono):
        """Generar bono con todos los carros ocupados"""
        from datetime import datetime
        
        # Obtener todos los carros ocupados
        carros_ocupados = []
        ordenes_ids = []  # IDs de órdenes asociadas
        
        for num_carro, proyecto_id in self.proyectos['carros'].items():
            if proyecto_id:
                proyecto = self.obtener_proyecto(proyecto_id)
                if proyecto:
                    carros_ocupados.append({
                        'carro': int(num_carro),
                        'proyecto_id': proyecto_id,
                        'proyecto_nombre': proyecto['nombre'],
                        'archivo_excel': proyecto['archivo']
                    })
                    
                    # Extraer número de orden del nombre del proyecto si existe
                    # Formato: "NUMERO_ORDEN - CODIGO_CORTE"
                    if ' - ' in proyecto['nombre']:
                        numero_orden = proyecto['nombre'].split(' - ')[0]
                        ordenes_ids.append(numero_orden)
        
        if not carros_ocupados:
            return None, 'No hay carros con proyectos asignados'
        
        if len(carros_ocupados) > 6:
            return None, 'No se pueden incluir más de 6 carros en un bono'
        
        # Verificar que el nombre no exista
        if 'bonos' not in self.proyectos:
            self.proyectos['bonos'] = {}
        
        if nombre_bono in self.proyectos['bonos']:
            return None, f'Ya existe un bono con el nombre "{nombre_bono}"'
        
        # Actualizar estado de las órdenes a "en_bono"
        self._actualizar_estado_ordenes(ordenes_ids, 'en_bono', nombre_bono)
        
        # Crear bono
        self.proyectos['bonos'][nombre_bono] = {
            'nombre': nombre_bono,
            'carros': carros_ocupados,
            'ordenes': ordenes_ids,
            'fecha_generacion': datetime.now().isoformat(),
            'estado': 'activo',
            'num_cortes': len(carros_ocupados)
        }
        
        self.guardar_proyectos()
        
        # IMPRESIÓN DE ETIQUETAS: Imprimir etiquetas para cada carro
        if Config.PRINT_ON_BONO_GENERATION:
            self._imprimir_etiquetas_bono(nombre_bono, carros_ocupados)
        
        return self.proyectos['bonos'][nombre_bono], None
    
    def _actualizar_estado_ordenes(self, numeros_ordenes, nuevo_estado, nombre_bono=None):
        """Actualizar estado de múltiples órdenes"""
        from config import Config
        
        ordenes_file = os.path.join(Config.DATA_FOLDER, 'ordenes_produccion.json')
        
        if not os.path.exists(ordenes_file):
            return
        
        with open(ordenes_file, 'r', encoding='utf-8') as f:
            ordenes_data = json.load(f)
        
        for orden in ordenes_data.get('ordenes', []):
            if orden.get('numero') in numeros_ordenes:
                orden['estado'] = nuevo_estado
                if nombre_bono:
                    orden['bono'] = nombre_bono
                if nuevo_estado == 'en_bono':
                    orden['fecha_inicio_bono'] = datetime.now().isoformat()
                elif nuevo_estado == 'engastando':
                    orden['fecha_inicio_engaste'] = datetime.now().isoformat()
                elif nuevo_estado == 'finalizado':
                    orden['fecha_finalizacion'] = datetime.now().isoformat()
        
        with open(ordenes_file, 'w', encoding='utf-8') as f:
            json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
    
    def obtener_bono(self, nombre_bono):
        """Obtener información de un bono"""
        bonos = self.proyectos.get('bonos', {})
        return bonos.get(nombre_bono)
    
    def obtener_todos_bonos(self):
        """Obtener lista de todos los bonos"""
        bonos = self.proyectos.get('bonos', {})
        return list(bonos.values())
    
    def validar_bono(self, nombre_bono):
        """Validar que un bono existe y está activo"""
        bono = self.obtener_bono(nombre_bono)
        if not bono:
            return False, 'Bono no encontrado'
        
        if bono.get('estado') != 'activo':
            return False, 'Bono inactivo'
        
        return True, bono
    
    def actualizar_progreso_bono(self, nombre_bono, terminal, carro, terminales_proyecto=None):
        """
        Actualizar progreso de un terminal en un carro del bono
        Args:
            nombre_bono: Nombre del bono
            terminal: Terminal del operario/puesto (ej: "Terminal 1")
            carro: Número de carro
            terminales_proyecto: Lista de terminales del proyecto completados (ej: ["1A", "1B", "2A"])
        """
        if 'bonos' not in self.proyectos:
            return False
        
        bono = self.proyectos['bonos'].get(nombre_bono)
        if not bono:
            return False
        
        # Inicializar estructura de progreso si no existe
        if 'progreso' not in bono:
            bono['progreso'] = {}
        
        if terminal not in bono['progreso']:
            bono['progreso'][terminal] = {
                'carros_completados': [],
                'estado': 'en_proceso'
            }
        
        # Marcar carro como completado para este terminal
        if carro not in bono['progreso'][terminal]['carros_completados']:
            bono['progreso'][terminal]['carros_completados'].append(carro)
        
        # Inicializar progreso por carro si no existe
        if 'progreso_por_carro' not in bono:
            bono['progreso_por_carro'] = {}
        
        if str(carro) not in bono['progreso_por_carro']:
            bono['progreso_por_carro'][str(carro)] = {
                'terminales_completados': [],
                'operarios': []
            }
        
        # Añadir terminales del proyecto completados
        if terminales_proyecto:
            for term in terminales_proyecto:
                if term not in bono['progreso_por_carro'][str(carro)]['terminales_completados']:
                    bono['progreso_por_carro'][str(carro)]['terminales_completados'].append(term)
        
        # Añadir operario si no está
        if terminal not in bono['progreso_por_carro'][str(carro)]['operarios']:
            bono['progreso_por_carro'][str(carro)]['operarios'].append(terminal)
        
        # VERIFICAR SI ESTE CARRO SE ACABA DE COMPLETAR (para imprimir etiqueta)
        carro_recien_completado = False
        if terminales_proyecto:
            # Obtener información del carro para verificar si está completo
            carro_info = None
            for c in bono['carros']:
                if c['carro'] == carro:
                    carro_info = c
                    break
            
            if carro_info:
                proyecto_id = carro_info['proyecto_id']
                proyecto = self.obtener_proyecto(proyecto_id)
                
                # Si el proyecto existe y podemos obtener total de terminales
                if proyecto:
                    # Verificar si se completó en este scan
                    terminales_completos = len(bono['progreso_por_carro'][str(carro)]['terminales_completados'])
                    
                    # Marcar como recién completado si no tenía el flag y ahora tiene todos
                    if not bono['progreso_por_carro'][str(carro)].get('finalizado', False):
                        # Por ahora asumir que está completo si se envió terminales_proyecto
                        # En el futuro se puede comparar con total del Excel
                        carro_recien_completado = True
                        bono['progreso_por_carro'][str(carro)]['finalizado'] = True
                        bono['progreso_por_carro'][str(carro)]['fecha_finalizacion'] = datetime.now().isoformat()
        
        # Actualizar estado de órdenes a "engastando" cuando se empieza a trabajar
        ordenes_bono = bono.get('ordenes', [])
        if ordenes_bono:
            # Buscar si alguna orden está aún en estado "en_bono"
            self._actualizar_estado_ordenes_si_necesario(ordenes_bono, 'en_bono', 'engastando')
        
        # Verificar si el terminal está completo
        # Un terminal está completo cuando procesó TODOS los carros que LO TIENEN
        carros_con_terminal = []
        for carro_info in bono.get('carros', []):
            archivo = carro_info.get('archivo_excel')
            if not archivo:
                continue
            
            # Verificar si este carro tiene el terminal
            try:
                temp_manager = ExcelManager(Config.UPLOAD_FOLDER, Config.CODIGOS_FILE)
                if temp_manager.cargar_excel_directo(archivo):
                    # Buscar si el terminal existe en este archivo
                    registros = temp_manager.current_df.to_dict('records')
                    terminal_en_carro = False
                    for row in registros:
                        de_term = str(row.get('De Terminal', '')).strip().upper()
                        para_term = str(row.get('Para Terminal', '')).strip().upper()
                        
                        if de_term == terminal.upper() or para_term == terminal.upper():
                            terminal_en_carro = True
                            break
                    
                    if terminal_en_carro:
                        carros_con_terminal.append(carro_info['carro'])
            except Exception as e:
                print(f"Error verificando terminal en carro: {e}")
        
        # Marcar como completado si procesó todos los carros que lo tienen
        carros_completados_terminal = bono['progreso'][terminal]['carros_completados']
        if len(carros_con_terminal) > 0 and all(c in carros_completados_terminal for c in carros_con_terminal):
            bono['progreso'][terminal]['estado'] = 'completado'
        
        # Verificar si el bono está completamente terminado
        # Para esto necesitamos obtener TODOS los terminales del bono desde los archivos Excel
        try:
            terminales_totales = set()
            for carro in bono.get('carros', []):
                archivo = carro.get('archivo_excel')
                if not archivo:
                    continue
                
                # Cargar Excel y extraer terminales
                manager = ExcelManager(Config.UPLOAD_FOLDER, Config.CODIGOS_FILE)
                if manager.cargar_excel(archivo):
                    registros = manager.current_df.to_dict('records')
                    for row in registros:
                        de_terminal = str(row.get('De Terminal', '')).strip().upper()
                        para_terminal = str(row.get('Para Terminal', '')).strip().upper()
                        
                        if de_terminal and de_terminal != 'S/T':
                            terminales_totales.add(de_terminal)
                        if para_terminal and para_terminal != 'S/T':
                            terminales_totales.add(para_terminal)
            
            # Verificar si TODOS los terminales del bono están en progreso Y completados
            todos_terminales_completados = False
            if terminales_totales and bono.get('progreso'):
                # Verificar que todos los terminales del Excel estén completados
                terminales_en_progreso = set(bono['progreso'].keys())
                
                # Solo está completado si:
                # 1. Todos los terminales del Excel están en progreso
                # 2. Todos tienen estado 'completado'
                if terminales_en_progreso >= terminales_totales:
                    todos_completados = True
                    for term in terminales_totales:
                        if term not in bono['progreso'] or bono['progreso'][term].get('estado') != 'completado':
                            todos_completados = False
                            break
                    todos_terminales_completados = todos_completados
        except Exception as e:
            print(f"Error al verificar terminales totales del bono: {e}")
            todos_terminales_completados = False
        
        # Si todos los terminales están completados, actualizar estado del bono a completado
        if todos_terminales_completados:
            bono['estado'] = 'completado'
            bono['fecha_finalizacion'] = datetime.now().isoformat()
        
        # Si todos los terminales están completados, marcar órdenes como finalizadas
        if todos_terminales_completados and ordenes_bono:
            self._actualizar_estado_ordenes(ordenes_bono, 'finalizado')
        
        self.guardar_proyectos()
        
        # IMPRIMIR ETIQUETA DE FINALIZACIÓN si el carro se acaba de completar
        if carro_recien_completado and Config.PRINT_ON_CARRO_COMPLETION:
            terminales_completados_count = len(bono['progreso_por_carro'][str(carro)]['terminales_completados'])
            proyecto_nombre = carro_info.get('proyecto_nombre', '') if carro_info else None
            
            self._imprimir_etiqueta_finalizacion(
                nombre_bono=nombre_bono,
                carro=carro,
                operario=terminal,
                terminales_completados=terminales_completados_count,
                terminales_totales=terminales_completados_count,  # Por ahora usar el mismo valor
                proyecto_nombre=proyecto_nombre
            )
        
        return True
    
    def _actualizar_estado_ordenes_si_necesario(self, numeros_ordenes, estado_actual, nuevo_estado):
        """Actualizar estado solo si las órdenes están en el estado_actual"""
        from config import Config
        
        ordenes_file = os.path.join(Config.DATA_FOLDER, 'ordenes_produccion.json')
        
        if not os.path.exists(ordenes_file):
            return
        
        with open(ordenes_file, 'r', encoding='utf-8') as f:
            ordenes_data = json.load(f)
        
        cambios = False
        for orden in ordenes_data.get('ordenes', []):
            if orden.get('numero') in numeros_ordenes and orden.get('estado') == estado_actual:
                orden['estado'] = nuevo_estado
                if nuevo_estado == 'engastando':
                    orden['fecha_inicio_engaste'] = datetime.now().isoformat()
                cambios = True
        
        if cambios:
            with open(ordenes_file, 'w', encoding='utf-8') as f:
                json.dump(ordenes_data, f, ensure_ascii=False, indent=2)
    
    def obtener_progreso_bono(self, nombre_bono):
        """Obtener progreso completo de un bono"""
        bono = self.obtener_bono(nombre_bono)
        if not bono:
            return None
        
        return bono.get('progreso', {})
    
    def obtener_progreso_por_carro(self, nombre_bono):
        """
        Obtener progreso detallado por carro.
        Devuelve un dict con la estructura:
        {
            carro_num: {
                'terminales_completados': [lista de terminales del proyecto],
                'operarios': [lista de operarios que han trabajado]
            }
        }
        """
        bono = self.obtener_bono(nombre_bono)
        if not bono:
            return {}
        
        progreso_por_carro = {}
        
        # Inicializar estructura para cada carro
        for carro_info in bono.get('carros', []):
            carro_num = carro_info['carro']
            progreso_por_carro[carro_num] = {
                'terminales_completados': [],
                'operarios': []
            }
        
        # Procesar progreso de cada operario/terminal
        progreso = bono.get('progreso', {})
        for terminal_operario, info in progreso.items():
            carros_completados = info.get('carros_completados', [])
            
            for carro_num in carros_completados:
                if carro_num in progreso_por_carro:
                    # Añadir operario si no está ya
                    if terminal_operario not in progreso_por_carro[carro_num]['operarios']:
                        progreso_por_carro[carro_num]['operarios'].append(terminal_operario)
        
        return progreso_por_carro
    
    def eliminar_bono(self, nombre_bono):
        """Eliminar un bono"""
        if 'bonos' not in self.proyectos:
            return False
        
        if nombre_bono in self.proyectos['bonos']:
            del self.proyectos['bonos'][nombre_bono]
            self.guardar_proyectos()
            return True
        
        return False
    
    def actualizar_bono(self, nombre_bono, nuevo_nombre, estado=None):
        """Actualizar información de un bono"""
        if 'bonos' not in self.proyectos:
            return False
        
        if nombre_bono not in self.proyectos['bonos']:
            return False
        
        bono = self.proyectos['bonos'][nombre_bono]
        
        # Si se cambia el nombre, mover el bono
        if nuevo_nombre and nuevo_nombre != nombre_bono:
            self.proyectos['bonos'][nuevo_nombre] = bono
            del self.proyectos['bonos'][nombre_bono]
        
        # Actualizar estado si se proporciona
        if estado:
            bono['estado'] = estado
        
        self.guardar_proyectos()
        return True
    
    def crear_proyecto_y_asignar_carro(self, nombre, archivo, numero_carro):
        """Crear un proyecto temporal y asignarlo directamente a un carro"""
        # Crear proyecto
        proyecto = {
            'id': len(self.proyectos['proyectos']) + 1,
            'nombre': nombre,
            'archivo': archivo,
            'fecha_carga': datetime.now().isoformat(),
            'carro_asignado': numero_carro,
            'progreso': 0,
            'terminales_completados': [],
            'estado': 'activo'
        }
        
        self.proyectos['proyectos'].append(proyecto)
        
        # Asignar a carro
        str_carro = str(numero_carro)
        self.proyectos['carros'][str_carro] = proyecto['id']
        
        self.guardar_proyectos()
        return proyecto
    
    def _imprimir_etiquetas_bono(self, nombre_bono, carros_ocupados):
        """
        Imprimir etiquetas para todos los carros del bono
        Se imprimen LABELS_PER_CARRO etiquetas por cada carro (config: 2)
        """
        try:
            from app.printer_manager import PrinterManager
            from app.zpl_templates import ZPLTemplates
            import logging
            
            logger = logging.getLogger(__name__)
            printer = PrinterManager(Config)
            
            logger.info(f"Iniciando impresión de etiquetas para bono {nombre_bono}")
            
            for carro_info in carros_ocupados:
                carro = carro_info['carro']
                proyecto_nombre = carro_info['proyecto_nombre']
                
                # Parsear número de orden y código de corte del nombre del proyecto
                if ' - ' in proyecto_nombre:
                    partes = proyecto_nombre.split(' - ', 1)
                    numero_orden = partes[0]
                    codigo_corte = partes[1]
                else:
                    numero_orden = "N/A"
                    codigo_corte = proyecto_nombre
                
                # Obtener proyecto completo
                proyecto = self.obtener_proyecto(carro_info['proyecto_id'])
                cantidad_terminales = len(proyecto.get('terminales_completados', [])) if proyecto else 0
                
                # Metadatos para el registro
                metadata = {
                    'tipo': 'asignacion',
                    'bono': nombre_bono,
                    'carro': carro,
                    'orden': numero_orden,
                    'codigo_corte': codigo_corte,
                    'proyecto': proyecto_nombre
                }
                
                # PRIMERA ETIQUETA: Asignación completa
                zpl_asignacion = ZPLTemplates.etiqueta_asignacion_carro(
                    carro=carro,
                    orden=numero_orden,
                    codigo_corte=codigo_corte,
                    proyecto=proyecto_nombre,
                    cantidad_terminales=cantidad_terminales
                )
                
                resultado = printer.print_zpl(zpl_asignacion, metadata)
                logger.info(f"Etiqueta asignación Carro {carro}: {resultado['message']}")
                
                # SEGUNDA ETIQUETA: Duplicado
                if Config.LABELS_PER_CARRO >= 2:
                    metadata_dup = metadata.copy()
                    metadata_dup['tipo'] = 'asignacion_duplicado'
                    
                    zpl_duplicado = ZPLTemplates.etiqueta_duplicada(
                        carro=carro,
                        orden=numero_orden,
                        codigo_corte=codigo_corte
                    )
                    
                    resultado_dup = printer.print_zpl(zpl_duplicado, metadata_dup)
                    logger.info(f"Etiqueta duplicado Carro {carro}: {resultado_dup['message']}")
            
            logger.info(f"Finalizada impresión de etiquetas para bono {nombre_bono}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al imprimir etiquetas del bono: {e}")
    
    def _imprimir_etiqueta_finalizacion(self, nombre_bono, carro, operario, 
                                       terminales_completados, terminales_totales, proyecto_nombre=None):
        """
        Imprimir etiqueta de finalización cuando un carro se completa
        """
        try:
            from app.printer_manager import PrinterManager
            from app.zpl_templates import ZPLTemplates
            import logging
            
            logger = logging.getLogger(__name__)
            printer = PrinterManager(Config)
            
            metadata = {
                'tipo': 'finalizacion',
                'bono': nombre_bono,
                'carro': carro,
                'operario': operario,
                'terminales': f"{terminales_completados}/{terminales_totales}"
            }
            
            zpl = ZPLTemplates.etiqueta_finalizacion_carro(
                carro=carro,
                nombre_bono=nombre_bono,
                operario=operario,
                terminales_completados=terminales_completados,
                terminales_totales=terminales_totales,
                proyecto=proyecto_nombre
            )
            
            resultado = printer.print_zpl(zpl, metadata)
            logger.info(f"Etiqueta finalización Carro {carro}: {resultado['message']}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al imprimir etiqueta de finalización: {e}")
    
    def resetear_progreso_bono(self, nombre_bono):
        """Resetear todo el progreso de un bono (progreso y progreso_por_carro)"""
        if 'bonos' not in self.proyectos:
            return False
        
        bono = self.proyectos['bonos'].get(nombre_bono)
        if not bono:
            return False
        
        # Limpiar progreso
        bono['progreso'] = {}
        bono['progreso_por_carro'] = {}
        
        # Guardar cambios
        self.guardar_proyectos()
        return True

# Instancia global
proyecto_manager = ProyectoManager()