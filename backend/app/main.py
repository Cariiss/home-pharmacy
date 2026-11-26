from fastapi import FastAPI

from .routers import auth, medicines, packages, settings

app = FastAPI(title="Домашняя аптека API", version="0.1.0")
app.include_router(auth.router)
app.include_router(medicines.router)
app.include_router(packages.router)
app.include_router(settings.router)


@app.get("/health", tags=["Служебное"])
def health():
    return {"status": "ok"}
