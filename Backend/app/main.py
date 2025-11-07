from fastapi import FastAPI

app = FastAPI()

# Esto es una prueba para probar el comando de uvicorn
@app.get("/")
def root():
    return {"message": "Welcome to the T1-MFDS 2025 Backend!"}