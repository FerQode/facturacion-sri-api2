# core/tasks/procesar_cortes_task.py
from celery import shared_task
from core.use_cases.servicio.gestionar_corte_servicio import ProcesarCortesBatchUseCase
import logging

logger = logging.getLogger(__name__)

@shared_task(name="procesar_cortes_masivos")
def procesar_cortes_masivos_task():
    """
    Tarea asíncrona para detectar morosos y generar órdenes de corte.
    Puede ser programada (Celery Beat) o disparada por Admin.
    """
    logger.info("Iniciando tarea de cortes masivos...")
    try:
        use_case = ProcesarCortesBatchUseCase()
        resultado = use_case.ejecutar()
        
        mensaje = (
            f"Tarea completada. Servicios analizados: {resultado['procesados']}. "
            f"Cortes generados: {resultado['cortes_generados']}."
        )
        logger.info(mensaje)
        return mensaje
    except Exception as e:
        error_msg = f"Error ejecutando cortes masivos: {str(e)}"
        logger.error(error_msg)
        raise e
