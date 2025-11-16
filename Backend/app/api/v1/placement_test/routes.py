from fastapi import APIRouter, HTTPException, status, Depends
from .schemas import PlacementTestInput, PlacementTestOutput, ErrorResponse
from .service import predict_plan, ModelLoadError, InvalidInputError, PredictionError
import logging
from app.api.deps import get_current_user
from datetime import date
from app.models.fitness_profile import FitnessProfile
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.api.v1.placement_test.service import prepare_profile_attributes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/placement-test", tags=["Placement Test"])

@router.post(
    "/",
    response_model=PlacementTestOutput,
    responses={
        400: {"model": ErrorResponse, "description": "Datos de entrada inválidos"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"},
        503: {"model": ErrorResponse, "description": "Servicio no disponible (modelos no cargados)"},
    },
    summary="Calcular plan de fitness personalizado",
    description="""Recibe las respuestas del test de posicionamiento y devuelve 
    el plan recomendado basado en machine learning."""
)
def placement_test_endpoint(data: PlacementTestInput, db: Session = Depends(get_db), current_user: User=Depends(get_current_user)):
    """
    Endpoint para calcular el plan de fitness personalizado.
    
    - **age**: Edad del usuario (años)
    - **gender**: Género del usuario
    - **exercise_freq**: Frecuencia de ejercicio (días por semana)
    - **activity_type**: Tipo de actividad preferida
    - **activity_intensity**: Intensidad de la actividad
    - **diet_type**: Tipo de dieta
    - **diet_special**: Consideraciones dietéticas especiales
    - **supplements**: Suplementos actuales
    - **goal_declared**: Objetivo fitness declarado
    - **sleep_hours**: Horas de sueño promedio
    
    Retorna el plan recomendado, descripción y los atributos del test.
    """
    try:
        result = predict_plan(data.dict())
        profile_data = prepare_profile_attributes(result)
        user_id_to_insert = current_user.user_id

        new_profile = FitnessProfile(
            user_id=user_id_to_insert,
            test_date=date.today(),
            attributes=profile_data
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        return result
        
    except InvalidInputError as e:
        logger.warning(f"Datos inválidos en placement test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_input",
                "message": str(e),
                "type": "InvalidInputError"
            }
        )
        
    except ModelLoadError as e:
        logger.error(f"Error de carga de modelos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "service_unavailable",
                "message": "El servicio de predicción no está disponible temporalmente. Por favor, intente más tarde.",
                "type": "ModelLoadError"
            }
        )
        
    except PredictionError as e:
        logger.error(f"Error en predicción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "prediction_error",
                "message": "Error al procesar la predicción. Por favor, verifique los datos e intente nuevamente.",
                "type": "PredictionError"
            }
        )
        
    except Exception as e:
        logger.error(f"Error inesperado en placement test endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "Error interno del servidor. Por favor, contacte al administrador.",
                "type": "UnexpectedError"
            }
        )