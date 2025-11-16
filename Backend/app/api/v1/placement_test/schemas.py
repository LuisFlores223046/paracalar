from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class PlacementTestInput(BaseModel):
    """Schema para las respuestas del test de posicionamiento."""
    age: int = Field(..., ge=13, le=120, description="Edad del usuario (13-120 años)")
    gender: str = Field(..., min_length=1, max_length=50, description="Género del usuario")
    exercise_freq: int = Field(..., ge=0, le=7, description="Frecuencia de ejercicio (0-7 días por semana)")
    activity_type: str = Field(..., min_length=1, max_length=100, description="Tipo de actividad")
    activity_intensity: str = Field(..., min_length=1, max_length=50, description="Intensidad de actividad")
    diet_type: str = Field(..., min_length=1, max_length=100, description="Tipo de dieta")
    diet_special: str = Field(..., min_length=1, max_length=200, description="Consideraciones dietéticas especiales")
    supplements: str = Field(..., min_length=1, max_length=200, description="Suplementos actuales")
    goal_declared: str = Field(..., min_length=1, max_length=100, description="Objetivo fitness")
    sleep_hours: int = Field(..., ge=0, le=24, description="Horas de sueño (0-24)")
    
    @validator('age')
    def validate_age(cls, v):
        if v < 13:
            raise ValueError('La edad mínima es 13 años')
        if v > 120:
            raise ValueError('Edad inválida')
        return v
    
    @validator('exercise_freq')
    def validate_exercise_freq(cls, v):
        if v < 0 or v > 7:
            raise ValueError('La frecuencia de ejercicio debe estar entre 0 y 7 días')
        return v
    
    @validator('sleep_hours')
    def validate_sleep_hours(cls, v):
        if v < 0 or v > 24:
            raise ValueError('Las horas de sueño deben estar entre 0 y 24')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 25,
                "gender": "M",
                "exercise_freq": 4,
                "activity_type": "Strength",
                "activity_intensity": "High",
                "diet_type": "Balanced",
                "diet_special": "Keto",
                "supplements": "Yes",
                "goal_declared": "Gain Muscle",
                "sleep_hours": 7
            }
        }

class PlacementTestOutput(BaseModel):
    """Schema para el resultado del test de posicionamiento."""
    recommended_plan: str = Field(..., description="Nombre del plan recomendado")
    description: Dict[str, Any] = Field(..., description="Diccionario con la descripción y productos.") #
    attributes: Dict[str, Any] = Field(..., description="Atributos del test (solo respuestas)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recommended_plan": "BeStrong",
                "description": { 
                    "description": "Plan enfocado en el aumento de masa muscular y fuerza.",
                    "recommended_products": ["Proteína aislada", "Creatina", "Pre-entreno"]
                },
                "attributes": {
                    "age": 25,
                    "gender": "M",
                    "exercise_freq": 4,
                    "activity_type": "Strength",
                    "activity_intensity": "High",
                    "diet_type": "Balanced",
                    "diet_special": "Keto",
                    "supplements": "Yes",
                    "goal_declared": "Gain Muscle",
                    "sleep_hours": 7
                }
            }
        }

class ErrorResponse(BaseModel):
    """Schema para respuestas de error."""
    error: str = Field(..., description="Código de error")
    message: str = Field(..., description="Mensaje de error legible")
    type: str = Field(..., description="Tipo de excepción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "invalid_input",
                "message": "Faltan campos requeridos: age, gender",
                "type": "InvalidInputError"
            }
        }