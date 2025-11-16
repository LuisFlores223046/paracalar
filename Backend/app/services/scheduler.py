"""
Scheduler para tareas programadas (Cron Jobs)
Este archivo maneja todas las tareas que se ejecutan automaticamente en intervalos programados
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from app.core.database import SessionLocal
from app.api.v1.loyalty.service import loyalty_service
from app.api.v1.subscriptions.service import subscription_service

# Configurar logging
logger = logging.getLogger(__name__)

def get_db_session() -> Session:
    """
    Crea una nueva sesion de base de datos para usar en los jobs
    """
    return SessionLocal()

# ==================== JOBS ====================

def expire_points_daily_job():
    """
    Job que expira puntos de todos los usuarios diariamente
    Se ejecuta a medianoche (00:00) todos los dias
    """
    logger.info("="*50)
    logger.info(f"[{datetime.now()}] Iniciando job: Expiración de puntos")
    logger.info("="*50)
    
    db = get_db_session()
    try:
        result = loyalty_service.expire_all_points(db)
        
        if result.get("success"):
            logger.info(
                f"Expiración completada exitosamente:\n"
                f"  - Usuarios afectados: {result.get('users_affected', 0)}\n"
                f"  - Total de puntos expirados: {result.get('total_expired_points', 0)}"
            )
        else:
            error_msg = result.get('error', 'Error desconocido')
            logger.error(f"Error en expiración de puntos: {error_msg}")
            
    except Exception as e:
        logger.error(f"Excepción fatal en job de expiración: {str(e)}", exc_info=True)
    finally:
        db.close()
        logger.info("="*50)
        logger.info(f"Job de expiración finalizado\n")


def process_subscriptions_daily_job():
    """
    Job que procesa los cobros de suscripciones diarias
    Se ejecuta a las 00:30 todos los días
    
    Procesa todas las suscripciones activas que tienen fecha de cobro hoy:
    - Realiza cobro con Stripe
    - Crea orden automática con productos seleccionados
    - Actualiza próxima fecha de entrega
    - Maneja fallos de pago (pausa después de 3 intentos)
    """
    logger.info("="*50)
    logger.info(f"[{datetime.now()}] Iniciando job: Procesamiento de suscripciones")
    logger.info("="*50)
    
    db = get_db_session()
    try:
        result = subscription_service.process_due_subscriptions(db)
        
        if result.get("success"):
            results_data = result.get("results", {})
            logger.info(
                f"Procesamiento de suscripciones completado:\n"
                f"  - Total procesadas: {results_data.get('total_processed', 0)}\n"
                f"  - Exitosas: {results_data.get('successful', 0)}\n"
                f"  - Fallidas: {results_data.get('failed', 0)}"
            )
            
            # Registrar errores específicos si los hay
            if results_data.get('errors'):
                logger.warning("Errores en suscripciones:")
                for error in results_data['errors']:
                    logger.warning(
                        f"  - Subscription ID {error.get('subscription_id')} "
                        f"(User {error.get('user_id')}): {error.get('error')}"
                    )
        else:
            error_msg = result.get('error', 'Error desconocido')
            logger.error(f"Error en procesamiento de suscripciones: {error_msg}")
            
    except Exception as e:
        logger.error(f"Excepción fatal en job de suscripciones: {str(e)}", exc_info=True)
    finally:
        db.close()
        logger.info("="*50)
        logger.info(f"Job de suscripciones finalizado\n")


# ==================== SCHEDULER ====================

# Variable global para mantener referencia al scheduler
_scheduler = None

def start_scheduler():
    """
    Inicia el scheduler y registra todos los jobs programados
    Esta funcion es llamada al iniciar la aplicacion
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("El scheduler ya está corriendo")
        return _scheduler
    
    logger.info("Inicializando scheduler de tareas programadas...")
    
    _scheduler = BackgroundScheduler(
        timezone="America/Denver",
        job_defaults={
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 3600
        }
    )
    
    # ==================== REGISTRAR JOBS ====================
    
    # Job 1: Expiracion diaria de puntos (00:00)
    _scheduler.add_job(
        func=expire_points_daily_job,
        trigger=CronTrigger(hour=0, minute=0),
        id='expire_points_daily',
        name='Expiración diaria de puntos',
        replace_existing=True
    )
    
    # Job 2: Procesamiento de suscripciones (00:30)
    _scheduler.add_job(
        func=process_subscriptions_daily_job,
        trigger=CronTrigger(hour=0, minute=30),
        id='process_subscriptions_daily',
        name='Procesamiento diario de suscripciones',
        replace_existing=True
    )
    
    # Iniciar el scheduler
    _scheduler.start()
    logger.info("Scheduler iniciado correctamente")
    
    # Mostrar informacion de los jobs programados
    logger.info("\nJobs programados:")
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
        logger.info(f"   • {job.name} (ID: {job.id})")
        logger.info(f"     Próxima ejecución: {next_run}")
    
    return _scheduler

def stop_scheduler():
    """
    Detiene el scheduler de forma segura
    Esta funcion es llamada al apagar la aplicacion
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.info("Deteniendo scheduler...")
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("Scheduler detenido correctamente")
    else:
        logger.warning("El scheduler no estaba corriendo")

def get_scheduler_status():
    """
    Devuelve el estado actual del scheduler y sus jobs - Para monitoreo
    """
    global _scheduler
    
    if _scheduler is None:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs_info = []
    for job in _scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": _scheduler.running,
        "jobs": jobs_info
    }

# ==================== FUNCIONES DE TESTING ====================

def run_expire_points_now():
    """
    Ejecuta el job de expiracion de puntos inmediatamente
    Para testing y debugging - NO prod
    """
    logger.info("Ejecutando expiración de puntos manualmente (testing)...")
    expire_points_daily_job()

def run_process_subscriptions_now():
    """
    Ejecuta el job de procesamiento de suscripciones inmediatamente
    Para testing y debugging - NO prod
    """
    logger.info("Ejecutando procesamiento de suscripciones manualmente (testing)...")
    process_subscriptions_daily_job()