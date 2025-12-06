import json
import os
from datetime import datetime
from config import Config

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
        
        # Actualizar estado de órdenes a "engastando" cuando se empieza a trabajar
        ordenes_bono = bono.get('ordenes', [])
        if ordenes_bono:
            # Buscar si alguna orden está aún en estado "en_bono"
            self._actualizar_estado_ordenes_si_necesario(ordenes_bono, 'en_bono', 'engastando')
        
        # Verificar si el terminal está completo (todos los carros)
        if len(bono['progreso'][terminal]['carros_completados']) >= len(bono['carros']):
            bono['progreso'][terminal]['estado'] = 'completado'
        
        # Verificar si el bono está completamente terminado
        todos_carros_completos = True
        for carro_info in bono['carros']:
            carro_num = str(carro_info['carro'])
            if carro_num not in bono.get('progreso_por_carro', {}):
                todos_carros_completos = False
                break
        
        # Si todos los carros están completos, marcar órdenes como finalizadas
        if todos_carros_completos and ordenes_bono:
            self._actualizar_estado_ordenes(ordenes_bono, 'finalizado')
        
        self.guardar_proyectos()
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

# Instancia global
proyecto_manager = ProyectoManager()