import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Any
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Manejo de errores específicos para mejor claridad
class PlacementTestError(Exception):
    """Excepción base para errores del placement test."""
    pass

class ModelLoadError(PlacementTestError):
    """Error al cargar los archivos del modelo."""
    pass

class InvalidInputError(PlacementTestError):
    """Error en los datos de entrada."""
    pass

class PredictionError(PlacementTestError):
    """Error durante la predicción."""
    pass

# Cargar modelo y encoders al iniciar el servicio
BASE_DIR = Path(__file__).resolve().parent
model_path = BASE_DIR / "model_assets" / "befit_model_v4.pkl"
encoders_path = BASE_DIR / "model_assets" / "label_encoders_v4.pkl"
target_enc_path = BASE_DIR / "model_assets" / "target_encoder_v4.pkl"

# Intentar cargar los modelos con manejo de errores
try:
    if not model_path.exists():
        raise ModelLoadError(f"Archivo del modelo no encontrado: {model_path}")
    if not encoders_path.exists():
        raise ModelLoadError(f"Archivo de encoders no encontrado: {encoders_path}")
    if not target_enc_path.exists():
        raise ModelLoadError(f"Archivo de target encoder no encontrado: {target_enc_path}")
    
    model = joblib.load(model_path)
    encoders = joblib.load(encoders_path)
    target_encoder = joblib.load(target_enc_path)
    logger.info("Modelos de ML cargados exitosamente")

except Exception as e:
    logger.error(f"Error crítico al cargar modelos: {str(e)}")
    # Los modelos quedarán como None y se manejará en predict_plan
    model = None
    encoders = None
    target_encoder = None

# Campos válidos del test
VALID_TEST_FIELDS = {
    "age",
    "gender",
    "exercise_freq",
    "activity_type",
    "activity_intensity",
    "diet_type",
    "diet_special",
    "supplements",
    "goal_declared",
    "sleep_hours"
}

def filter_test_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra el diccionario de attributes para incluir solo los campos válidos del test.
    Esto permite que attributes del FitnessProfile contenga otros datos sin causar errores.
    
    Argumentos:
        attributes: Diccionario completo que puede contener campos extra
    
    Retorna:
        Diccionario con solo los campos necesarios para el modelo
        
    Excepciones:
        InvalidInputError: Si faltan campos requeridos
    """
    if not attributes:
        raise InvalidInputError("El diccionario de atributos está vacío")
    
    filtered = {key: value for key, value in attributes.items() if key in VALID_TEST_FIELDS}
    
    # Verificar que todos los campos requeridos estén presentes
    missing_fields = VALID_TEST_FIELDS - set(filtered.keys())
    if missing_fields:
        raise InvalidInputError(f"Faltan campos requeridos: {', '.join(missing_fields)}")
    
    return filtered

def predict_plan(input_data: dict) -> dict:
    """
    Recibe un diccionario con las respuestas del test y devuelve la recomendación.
    
    Argumentos:
        input_data: Diccionario que puede contener más campos de los necesarios.
                    Se filtrarán automáticamente para usar solo los válidos.
    
    Retorna:
        dict con:
            - recommended_plan: Nombre del plan asignado
            - description: Descripción del plan
            - attributes: Dict con solo las respuestas del test
            
    Para guardar en FitnessProfile.attributes, hay que combinar:
            profile.attributes = {**result["attributes"], 
            "recommended_plan": result["recommended_plan"],
            "description": result["description"]}
            
    Excepciones:
        ModelLoadError: Si los modelos no están cargados
        InvalidInputError: Si los datos de entrada son inválidos
        PredictionError: Si falla la predicción
    """
    try:
        # Verificar que los modelos estén cargados
        if model is None or encoders is None or target_encoder is None:
            raise ModelLoadError("Los modelos de ML no están disponibles. Contacte al administrador.")
        
        # Validar entrada
        if not isinstance(input_data, dict):
            raise InvalidInputError("Los datos de entrada deben ser un diccionario")
        
        # Filtrar solo los campos válidos para el modelo
        filtered_data = filter_test_attributes(input_data)
        
        # Crear DataFrame con los datos filtrados
        try:
            df = pd.DataFrame([filtered_data])
        except Exception as e:
            raise InvalidInputError(f"Error al crear DataFrame: {str(e)}")

        # Aplicar los encoders a cada columna categórica
        try:
            for col, encoder in encoders.items():
                if col in df.columns:
                    try:
                        df[col] = encoder.transform(df[col])
                    except ValueError as e:
                        raise InvalidInputError(
                            f"Valor inválido para el campo '{col}': {df[col].iloc[0]}. "
                            f"Valores permitidos: {list(encoder.classes_)}"
                        )

        except Exception as e:
            raise PredictionError(f"Error al codificar datos: {str(e)}")

        # Hacer predicción
        try:
            pred = model.predict(df)[0]
            plan = target_encoder.inverse_transform([pred])[0]
        except Exception as e:
            logger.error(f"Error en la predicción del modelo: {str(e)}")
            raise PredictionError(f"Error al predecir el plan: {str(e)}")

        # Diccionario de Plan y Descripción respectivamente
        plan_descriptions = {
            "BeStrong": {
                "description": "Plan enfocado en el aumento de masa muscular y fuerza.",
                "recommended_products": ["Proteína aislada", "Creatina", "Pre-entreno"]
            },
            "BeLean": {
                "description": "Plan centrado en la pérdida de grasa y tonificación.",
                "recommended_products": ["Proteína ligera", "Termogénicos", "Omega 3"]
            },
            "BeBalance": {
                "description": "Plan equilibrado para mantener un estado físico estable.",
                "recommended_products": ["Multivitamínico", "Colágeno", "Proteína media"]
            },
            "BeDefine": {
                "description": "Plan de definición muscular con enfoque en detalle y tono.",
                "recommended_products": ["L-Carnitina", "BCAA", "Proteína ligera"]
            },
            "BeNutri": {
                "description": "Plan basado en nutrición integral y balance alimenticio.",
                "recommended_products": ["Batidos meal replacement", "Fibra", "Omega 3"]
            },
        }

        plan_data = plan_descriptions.get(plan)
        if plan_data is None:
            plan_data = {
                "description": "Plan personalizado: No se encontró una recomendación específica.",
                "recommended_products": []
            }
       # description = plan_descriptions.get(plan, "Plan personalizado")
#        recommended_products = plan_data.get("recommended_products", [])

        description = plan_data
        logger.info(f"Predicción exitosa: {plan}")
        
        return {
            "recommended_plan": plan,
            "description": description,
            "attributes": filtered_data,
            #"recommended_products": recommended_products
        }
        
    except (ModelLoadError, InvalidInputError, PredictionError):
        raise
    except Exception as e:
        # Capturar cualquier error inesperado
        logger.error(f"Error inesperado en predict_plan: {str(e)}", exc_info=True)
        raise PredictionError(f"Error inesperado al procesar el test: {str(e)}")


def get_plan_description_string(result: dict) -> str:
    """
    Extrae la cadena de texto de la descripción del plan del resultado.
    
    Argumentos:
        result: El diccionario devuelto por predict_plan.
    
    Retorna:
        La cadena de texto de la descripción.
    """
    plan_description_dict = result.get("description", {})
    return plan_description_dict.get("description", "Descripción no disponible")

def get_recommended_products_list(result: dict) -> list:
    """
    Extrae la lista de productos recomendados del plan del resultado.
    
    Argumentos:
        result: El diccionario devuelto por predict_plan.
    
    Retorna:
        Una lista de strings con los productos recomendados.
    """
    plan_description_dict = result.get("description", {})
    products = plan_description_dict.get("recommended_products", [])
    
    # Asegurarse de que el retorno es una lista
    if isinstance(products, list):
        return products
    return []

def prepare_profile_attributes(prediction_result: dict) -> dict:
    """
    Combina las respuestas del test con los datos del plan (desanidados) 
    para guardarlos en la columna JSON 'attributes' de FitnessProfile.
    
    Argumentos:
        prediction_result: El diccionario devuelto por predict_plan.
    
    Retorna:
        Un diccionario JSON plano listo para la columna FitnessProfile.attributes.
    """
    
    # 1. Extrae los datos principales
    test_attributes = prediction_result.get("attributes", {})
    plan_name = prediction_result.get("recommended_plan")
    
    # 2. Extrae el diccionario de descripción/productos (es el valor del campo 'description' en el output)
    plan_data_dict = prediction_result.get("description", {})
    
    # 3. Combina todo en un solo diccionario plano (flat dictionary)
    profile_attributes = {
        **test_attributes,
        "recommended_plan": plan_name,
        # Desanidar el diccionario "description" en sus componentes:
        "description": plan_data_dict.get("description"), # Descripción como string
        "recommended_products": plan_data_dict.get("recommended_products", []), # Productos como lista
    }
    
    return profile_attributes