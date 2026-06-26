from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import models 
from database import Base, engine

from api.users import router as users_router
from api.rooms import router as rooms_router
from api.reviews import router as reviews_router
from api.bookings import router as bookings_router
from api.pages import router as pages_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield 
    await engine.dispose()    

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = exception.detail if exception.detail else "An error occurred."
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exception.status_code, content={"detail": message})

    from api.pages import templates
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"status_code": exception.status_code, "message": message}, 
        status_code=exception.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        errors = exception.errors()
        for err in errors:
            if "ctx" in err and "error" in err["ctx"]:
                err["ctx"]["error"] = str(err["ctx"]["error"])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, 
            content={"detail": errors}
        )
    
    from api.pages import templates
    return templates.TemplateResponse(
        request, 
        "error.html", 
        {"status_code": status.HTTP_422_UNPROCESSABLE_CONTENT, "message": "Invalid request."}, 
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )

@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    from api.pages import templates
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    from api.pages import templates
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )

app.include_router(users_router)
app.include_router(rooms_router)
app.include_router(reviews_router)
app.include_router(bookings_router)
app.include_router(pages_router)