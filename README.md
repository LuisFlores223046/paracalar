# T1- MFDS 2025 - Backend
MFDS 2025 T1

## Instrucciones de uso
Para instalar las dependencias requeridas ubicadas en "requirements.txt", es necesario realizar los siguientes pasos:

1. Para crear el ambiente virtual: python -m venv venv
2. Para activar el ambiente virtual: ./venv/Scripts/activate
3. Para desactivar el ambiente virtual: deactivate
4. Para instalar las dependencias: pip install -r requirements.txt 

## Levantar el server de FastAPI
Para leventar el server de fastapi mediante la uvicorn, es necesario crealizar lo siguiente:

cd Backend 
uvicorn app.main:app --reload

Para cerrar el server una vez que se este ejecutando: ctrl + c