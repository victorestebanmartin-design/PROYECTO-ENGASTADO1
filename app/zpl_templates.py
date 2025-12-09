"""
Plantillas ZPL para impresión de etiquetas en Zebra GK420T
Dimensiones de etiqueta: 55mm x 15mm (432 dots x 118 dots @ 203 DPI)
"""
from datetime import datetime


class ZPLTemplates:
    """Generador de plantillas ZPL para diferentes tipos de etiquetas"""
    
    # Dimensiones de etiqueta en dots (203 DPI)
    # 55mm = 432 dots, 15mm = 118 dots
    LABEL_WIDTH = 432
    LABEL_HEIGHT = 118
    
    @staticmethod
    def etiqueta_asignacion_carro(carro: int, orden: str, codigo_corte: str, 
                                   proyecto: str, cantidad_terminales: int) -> str:
        """
        Generar etiqueta de asignación de carro al generar bono
        Layout optimizado para 55x15mm
        
        Args:
            carro: Número de carro (1-6)
            orden: Número de orden
            codigo_corte: Código de corte asociado
            proyecto: Nombre del proyecto
            cantidad_terminales: Cantidad total de terminales
            
        Returns:
            Código ZPL listo para imprimir
        """
        # Truncar textos largos
        proyecto_truncado = proyecto[:20] if len(proyecto) > 20 else proyecto
        codigo_truncado = codigo_corte[:15] if len(codigo_corte) > 15 else codigo_corte
        
        return f"""^XA
^FO10,5^A0N,25,25^FDCarro: {carro}^FS
^FO10,35^GB410,1,1^FS
^FO10,40^A0N,20,20^FDOrden: {orden}^FS
^FO10,62^A0N,18,18^FD{codigo_truncado}^FS
^FO280,40^A0N,18,18^FDTerm: {cantidad_terminales}^FS
^FO280,62^A0N,15,15^FD{proyecto_truncado}^FS
^XZ"""
    
    @staticmethod
    def etiqueta_duplicada(carro: int, orden: str, codigo_corte: str) -> str:
        """
        Generar etiqueta duplicada (segunda etiqueta por carro)
        Versión simplificada con énfasis en código de barras
        
        Args:
            carro: Número de carro
            orden: Número de orden
            codigo_corte: Código de corte
            
        Returns:
            Código ZPL listo para imprimir
        """
        codigo_truncado = codigo_corte[:18] if len(codigo_corte) > 18 else codigo_corte
        
        return f"""^XA
^FO10,5^A0N,22,22^FDCarro {carro} - DUPLICADO^FS
^FO10,30^GB410,1,1^FS
^FO10,35^A0N,20,20^FDOrden: {orden}^FS
^FO10,58^A0N,18,18^FD{codigo_truncado}^FS
^FO280,35^BY2^BCN,40,N,N,N^FD{orden}^FS
^XZ"""
    
    @staticmethod
    def etiqueta_finalizacion_carro(carro: int, nombre_bono: str, 
                                     operario: str, terminales_completados: int,
                                     terminales_totales: int, proyecto: str = None) -> str:
        """
        Generar etiqueta de finalización de carro (para documentación)
        
        Args:
            carro: Número de carro
            nombre_bono: Nombre/ID del bono
            operario: Terminal o nombre del operario que completó
            terminales_completados: Cantidad de terminales completados
            terminales_totales: Cantidad total de terminales del proyecto
            proyecto: Nombre del proyecto (opcional)
            
        Returns:
            Código ZPL listo para imprimir
        """
        fecha = datetime.now().strftime("%d/%m/%Y")
        hora = datetime.now().strftime("%H:%M")
        progreso = int((terminales_completados / terminales_totales) * 100) if terminales_totales > 0 else 100
        
        # Truncar textos
        bono_truncado = nombre_bono[:18] if len(nombre_bono) > 18 else nombre_bono
        operario_truncado = operario[:12] if len(operario) > 12 else operario
        proyecto_truncado = (proyecto[:15] if proyecto and len(proyecto) > 15 else proyecto) if proyecto else ""
        
        zpl = f"""^XA
^FO10,5^A0N,22,22^FDCARRO {carro} FINALIZADO^FS
^FO10,30^GB410,2,2^FS
^FO10,35^A0N,18,18^FD{bono_truncado}^FS
^FO10,55^A0N,16,16^FD{fecha} {hora}^FS
^FO220,55^A0N,16,16^FDOp: {operario_truncado}^FS
^FO10,73^A0N,16,16^FDTerm: {terminales_completados}/{terminales_totales} ({progreso}%)^FS"""
        
        # Agregar proyecto si está disponible
        if proyecto_truncado:
            zpl += f"\n^FO10,91^A0N,14,14^FD{proyecto_truncado}^FS"
        
        zpl += "\n^XZ"
        
        return zpl
    
    @staticmethod
    def etiqueta_test() -> str:
        """
        Generar etiqueta de prueba para verificar configuración
        
        Returns:
            Código ZPL de prueba
        """
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        return f"""^XA
^FO10,10^A0N,30,30^FDPRUEBA ZEBRA^FS
^FO10,45^GB410,1,1^FS
^FO10,50^A0N,20,20^FDSistema Engastado^FS
^FO10,75^A0N,16,16^FD{fecha}^FS
^FO10,95^A0N,14,14^FD55mm x 15mm @ 203 DPI^FS
^XZ"""
    
    @staticmethod
    def validar_dimensiones() -> str:
        """
        Generar etiqueta con guías de dimensiones para calibración
        
        Returns:
            Código ZPL con guías visuales
        """
        return f"""^XA
^FO0,0^GB{ZPLTemplates.LABEL_WIDTH},1,1^FS
^FO0,{ZPLTemplates.LABEL_HEIGHT-1}^GB{ZPLTemplates.LABEL_WIDTH},1,1^FS
^FO0,0^GB1,{ZPLTemplates.LABEL_HEIGHT},1^FS
^FO{ZPLTemplates.LABEL_WIDTH-1},0^GB1,{ZPLTemplates.LABEL_HEIGHT},1^FS
^FO10,40^A0N,25,25^FD55mm x 15mm^FS
^FO10,70^A0N,20,20^FD432 x 118 dots^FS
^XZ"""
