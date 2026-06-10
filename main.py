from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from database import Base, engine
import models

from api.users import router as users_router
from api.rooms import router as rooms_router
from api.reviews import router as reviews_router
from api.bookings import router as bookings_router
from api.pages import router as pages_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Booking API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = exception.detail if exception.detail else "An error occurred."
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exception.status_code, content={"detail": message})
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"status_code": exception.status_code, "message": message}, 
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        errors = exception.errors()
        for err in errors:
            if "ctx" in err and "error" in err["ctx"]:
                err["ctx"]["error"] = str(err["ctx"]["error"])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, 
            content={"detail": errors}
        )
    
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"status_code": status.HTTP_422_UNPROCESSABLE_CONTENT, "message": "Invalid request."}, 
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )

app.include_router(users_router)
app.include_router(rooms_router)
app.include_router(reviews_router)
app.include_router(bookings_router)

app.include_router(pages_router)