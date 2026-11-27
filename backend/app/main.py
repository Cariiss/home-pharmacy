from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import auth, medicines, packages, settings

app = FastAPI(title="Домашняя аптека API", version="0.1.0")
app.include_router(auth.router)
app.include_router(medicines.router)
app.include_router(packages.router)
app.include_router(settings.router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic пишет ошибки по-английски, поэтому отвечаем своим текстом
    errors = []
    for err in exc.errors():
        field = err["loc"][-1]
        if err["type"] == "missing":
            text = "обязательное поле"
        elif err["type"] == "value_error" and field != "email":
            text = str(err["ctx"]["error"])  # сообщения из наших валидаторов уже на русском
        else:
            text = "некорректное значение"
        errors.append(f"{field}: {text}")
    return JSONResponse(status_code=422, content={"detail": "; ".join(errors)})


@app.get("/health", tags=["Служебное"])
def health():
    return {"status": "ok"}
