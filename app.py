from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"mesaj": " AI Ajani Basariyla Calisiyor"}