from app.core.exceptions import AppException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Request
from fastapi.exceptions import RequestValidationError

async def app_exception_handler(request : Request, exc:AppException):
    return JSONResponse(
        status_code= exc.status_code,
        content={
            "success" : False,
            "message" : exc.message,
            "data" : None
        }
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            # exc.errors() can contain raw exception objects (e.g. inside
            # "ctx" when a Pydantic field_validator raises ValueError),
            # which plain json.dumps() can't serialize. jsonable_encoder
            # converts those into plain, JSON-safe values (e.g. strings).
            "data": jsonable_encoder(exc.errors()),
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None,
        },
    )