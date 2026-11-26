from fastapi import FastAPI

from .database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Домашняя аптека API", version="0.1.0")


@app.get("/health", tags=["Служебное"])
def health():
    return {"status": "ok"}
