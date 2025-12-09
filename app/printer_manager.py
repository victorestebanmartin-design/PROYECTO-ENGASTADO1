"""
Gestor de impresión para Zebra GK420T
Soporta modo producción (CUPS) y modo simulación (archivos .txt)
"""
import os
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class PrinterManager:
    """Gestor de impresión para etiquetas Zebra con soporte para simulación"""
    
    def __init__(self, config=None):
        """
        Inicializar gestor de impresión
        
        Args:
            config: Objeto de configuración (Config class) o None para usar defaults
        """
        if config:
            self.printer_name = getattr(config, 'PRINTER_NAME', 'ZebraGK420T')
            self.simulation_mode = getattr(config, 'PRINTER_SIMULATION_MODE', True)
            self.enabled = getattr(config, 'PRINTER_ENABLED', True)
            self.simulation_dir = getattr(config, 'PRINTER_SIMULATION_DIR', 'data/etiquetas_simuladas')
            self.pending_file = getattr(config, 'PRINTER_PENDING_FILE', 'data/etiquetas_pendientes.json')
        else:
            self.printer_name = 'ZebraGK420T'
            self.simulation_mode = True
            self.enabled = True
            self.simulation_dir = 'data/etiquetas_simuladas'
            self.pending_file = 'data/etiquetas_pendientes.json'
        
        # Crear directorio de simulación si no existe
        if self.simulation_mode:
            os.makedirs(self.simulation_dir, exist_ok=True)
        
        # Verificar disponibilidad real solo si no está en modo simulación
        if not self.simulation_mode and self.enabled:
            self.available = self._check_printer_available()
        else:
            self.available = True  # En simulación siempre está "disponible"
    
    def _check_printer_available(self) -> bool:
        """
        Verificar si la impresora está disponible en el sistema
        
        Returns:
            True si la impresora está disponible, False en caso contrario
        """
        try:
            result = subprocess.run(
                ['lpstat', '-p', self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
            
            if available:
                logger.info(f"Impresora {self.printer_name} detectada y disponible")
            else:
                logger.warning(f"Impresora {self.printer_name} no disponible")
            
            return available
            
        except FileNotFoundError:
            logger.warning("CUPS no está instalado (lpstat no encontrado)")
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Timeout al verificar impresora")
            return False
        except Exception as e:
            logger.warning(f"Error verificando impresora: {e}")
            return False
    
    def print_zpl(self, zpl_code: str, metadata: Dict = None) -> Dict[str, any]:
        """
        Enviar código ZPL a la impresora (o simular impresión)
        
        Args:
            zpl_code: Código ZPL a imprimir
            metadata: Información adicional sobre la etiqueta (tipo, carro, bono, etc.)
        
        Returns:
            Dict con keys: success (bool), message (str), file_path (str, solo simulación)
        """
        if not self.enabled:
            return {
                'success': False,
                'message': 'Impresión deshabilitada en configuración',
                'file_path': None
            }
        
        # Modo simulación: guardar en archivo
        if self.simulation_mode:
            return self._simulate_print(zpl_code, metadata)
        
        # Modo producción: imprimir via CUPS
        return self._real_print(zpl_code, metadata)
    
    def _simulate_print(self, zpl_code: str, metadata: Dict = None) -> Dict[str, any]:
        """
        Simular impresión guardando ZPL en archivo de texto
        
        Args:
            zpl_code: Código ZPL
            metadata: Metadatos de la etiqueta
            
        Returns:
            Resultado de la simulación
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Generar nombre de archivo descriptivo
            if metadata:
                tipo = metadata.get('tipo', 'unknown')
                carro = metadata.get('carro', 'X')
                filename = f"{timestamp}_{tipo}_carro{carro}.zpl"
            else:
                filename = f"{timestamp}_etiqueta.zpl"
            
            file_path = os.path.join(self.simulation_dir, filename)
            
            # Guardar código ZPL
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# SIMULACIÓN DE IMPRESIÓN ZEBRA GK420T\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                if metadata:
                    f.write(f"# Metadatos:\n")
                    for key, value in metadata.items():
                        f.write(f"#   {key}: {value}\n")
                
                f.write(f"# Visualizar en: https://labelary.com/viewer.html\n")
                f.write(f"# Dimensiones: 55mm x 15mm (2.17\" x 0.59\")\n")
                f.write(f"# DPI: 203 (8 dpmm)\n")
                f.write(f"\n{'='*60}\n\n")
                f.write(zpl_code)
            
            logger.info(f"Etiqueta simulada guardada en: {file_path}")
            
            return {
                'success': True,
                'message': f'Etiqueta simulada guardada: {filename}',
                'file_path': file_path,
                'simulation': True
            }
            
        except Exception as e:
            logger.error(f"Error simulando impresión: {e}")
            return {
                'success': False,
                'message': f'Error en simulación: {str(e)}',
                'file_path': None,
                'simulation': True
            }
    
    def _real_print(self, zpl_code: str, metadata: Dict = None) -> Dict[str, any]:
        """
        Imprimir realmente via CUPS
        
        Args:
            zpl_code: Código ZPL
            metadata: Metadatos
            
        Returns:
            Resultado de la impresión
        """
        if not self.available:
            # Guardar en cola de pendientes
            self._save_pending_label(zpl_code, metadata, "Impresora no disponible")
            
            return {
                'success': False,
                'message': 'Impresora no disponible - guardado en cola de pendientes',
                'pending': True
            }
        
        try:
            # Crear archivo temporal con el código ZPL
            timestamp = datetime.now().timestamp()
            temp_file = f'/tmp/zpl_{timestamp}.zpl'
            
            with open(temp_file, 'w') as f:
                f.write(zpl_code)
            
            # Imprimir usando lpr con opción raw (sin procesamiento)
            result = subprocess.run(
                ['lpr', '-P', self.printer_name, '-o', 'raw', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Limpiar archivo temporal
            try:
                os.remove(temp_file)
            except:
                pass
            
            if result.returncode == 0:
                job_id = self._get_last_job_id()
                logger.info(f"Etiqueta enviada a impresora - Job ID: {job_id}")
                
                return {
                    'success': True,
                    'message': f'Etiqueta enviada a impresión (Job #{job_id})',
                    'job_id': job_id
                }
            else:
                error_msg = result.stderr or "Error desconocido"
                logger.error(f"Error imprimiendo: {error_msg}")
                
                # Guardar en pendientes
                self._save_pending_label(zpl_code, metadata, error_msg)
                
                return {
                    'success': False,
                    'message': f'Error de impresión: {error_msg}',
                    'pending': True
                }
                
        except subprocess.TimeoutExpired:
            error_msg = "Timeout al imprimir (impresora no responde)"
            logger.error(error_msg)
            self._save_pending_label(zpl_code, metadata, error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'pending': True
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error inesperado al imprimir: {error_msg}")
            self._save_pending_label(zpl_code, metadata, error_msg)
            
            return {
                'success': False,
                'message': f'Error: {error_msg}',
                'pending': True
            }
    
    def _get_last_job_id(self) -> Optional[int]:
        """
        Obtener ID del último trabajo de impresión
        
        Returns:
            Job ID o None
        """
        try:
            result = subprocess.run(
                ['lpstat', '-W', 'completed', '-o', self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            if lines and lines[0]:
                # Formato: "ZebraGK420T-123 user ... "
                last_line = lines[-1]
                job_id_str = last_line.split()[0].split('-')[-1]
                return int(job_id_str)
        except:
            pass
        
        return None
    
    def _save_pending_label(self, zpl_code: str, metadata: Dict, error: str):
        """
        Guardar etiqueta que no se pudo imprimir para reintentar después
        
        Args:
            zpl_code: Código ZPL
            metadata: Metadatos
            error: Mensaje de error
        """
        try:
            # Leer pendientes existentes
            if os.path.exists(self.pending_file):
                with open(self.pending_file, 'r') as f:
                    pendientes = json.load(f)
            else:
                pendientes = []
            
            # Agregar nueva etiqueta pendiente
            pendientes.append({
                'zpl': zpl_code,
                'metadata': metadata or {},
                'error': error,
                'fecha': datetime.now().isoformat(),
                'intentos': 0
            })
            
            # Guardar
            os.makedirs(os.path.dirname(self.pending_file), exist_ok=True)
            with open(self.pending_file, 'w') as f:
                json.dump(pendientes, f, indent=2)
            
            logger.info(f"Etiqueta guardada en cola de pendientes ({len(pendientes)} total)")
            
        except Exception as e:
            logger.error(f"Error guardando etiqueta pendiente: {e}")
    
    def get_printer_status(self) -> Dict[str, any]:
        """
        Obtener estado de la impresora
        
        Returns:
            Dict con información de estado
        """
        if self.simulation_mode:
            return {
                'available': True,
                'status': 'simulation',
                'mode': 'Modo Simulación',
                'message': f'Etiquetas se guardan en {self.simulation_dir}',
                'has_paper': True,
                'simulation_dir': self.simulation_dir,
                'simulated_labels': self._count_simulated_labels()
            }
        
        if not self.enabled:
            return {
                'available': False,
                'status': 'disabled',
                'mode': 'Deshabilitado',
                'message': 'Impresión deshabilitada en configuración'
            }
        
        try:
            # Verificar estado con lpstat
            result = subprocess.run(
                ['lpstat', '-p', self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {
                    'available': False,
                    'status': 'offline',
                    'mode': 'Producción',
                    'message': f'Impresora {self.printer_name} no detectada',
                    'has_paper': False
                }
            
            # Parsear estado
            status_text = result.stdout.lower()
            
            if 'idle' in status_text:
                status = 'idle'
                message = 'Impresora lista'
            elif 'printing' in status_text:
                status = 'printing'
                message = 'Imprimiendo...'
            elif 'disabled' in status_text:
                status = 'disabled'
                message = 'Impresora deshabilitada'
            else:
                status = 'unknown'
                message = 'Estado desconocido'
            
            # Verificar papel (lpstat detallado)
            result_detail = subprocess.run(
                ['lpstat', '-l', '-p', self.printer_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            has_paper = 'media-empty' not in result_detail.stdout.lower()
            
            return {
                'available': True,
                'status': status,
                'mode': 'Producción',
                'message': message,
                'has_paper': has_paper,
                'printer_name': self.printer_name
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return {
                'available': False,
                'status': 'error',
                'mode': 'Producción',
                'message': f'Error: {str(e)}',
                'has_paper': False
            }
    
    def _count_simulated_labels(self) -> int:
        """Contar etiquetas simuladas guardadas"""
        try:
            if os.path.exists(self.simulation_dir):
                files = [f for f in os.listdir(self.simulation_dir) if f.endswith('.zpl')]
                return len(files)
        except:
            pass
        return 0
    
    def get_pending_labels(self) -> List[Dict]:
        """
        Obtener lista de etiquetas pendientes de impresión
        
        Returns:
            Lista de etiquetas pendientes
        """
        try:
            if os.path.exists(self.pending_file):
                with open(self.pending_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo etiquetas pendientes: {e}")
        
        return []
    
    def retry_pending_labels(self) -> Dict[str, any]:
        """
        Reintentar imprimir todas las etiquetas pendientes
        
        Returns:
            Resumen de resultados
        """
        pendientes = self.get_pending_labels()
        
        if not pendientes:
            return {
                'success': True,
                'message': 'No hay etiquetas pendientes',
                'processed': 0,
                'successful': 0,
                'failed': 0
            }
        
        successful = 0
        failed = 0
        still_pending = []
        
        for etiqueta in pendientes:
            result = self.print_zpl(etiqueta['zpl'], etiqueta.get('metadata'))
            
            if result['success']:
                successful += 1
            else:
                failed += 1
                etiqueta['intentos'] += 1
                still_pending.append(etiqueta)
        
        # Actualizar archivo de pendientes
        try:
            with open(self.pending_file, 'w') as f:
                json.dump(still_pending, f, indent=2)
        except Exception as e:
            logger.error(f"Error actualizando pendientes: {e}")
        
        return {
            'success': True,
            'message': f'Procesadas {len(pendientes)} etiquetas',
            'processed': len(pendientes),
            'successful': successful,
            'failed': failed,
            'remaining': len(still_pending)
        }
    
    def clear_simulated_labels(self) -> Dict[str, any]:
        """
        Limpiar todas las etiquetas simuladas
        
        Returns:
            Resultado de la operación
        """
        try:
            if not os.path.exists(self.simulation_dir):
                return {
                    'success': True,
                    'message': 'No hay etiquetas simuladas',
                    'deleted': 0
                }
            
            files = [f for f in os.listdir(self.simulation_dir) if f.endswith('.zpl')]
            
            for file in files:
                os.remove(os.path.join(self.simulation_dir, file))
            
            return {
                'success': True,
                'message': f'Eliminadas {len(files)} etiquetas simuladas',
                'deleted': len(files)
            }
            
        except Exception as e:
            logger.error(f"Error limpiando etiquetas simuladas: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'deleted': 0
            }
