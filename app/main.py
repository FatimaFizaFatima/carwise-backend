from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.cors import setup_cors
from app.core.logging import setup_logging
import logging
from app.middleware.logging import request_logging_middleware
from app.api.v1.auth import router as auth_router
from app.core.exceptions import AppException
from app.core.exception_handler import app_exception_handler, general_exception_handler, validation_exception_handler

setup_logging()

logger = logging.getLogger(__name__)


app = FastAPI(title="CarWise")

app.add_exception_handler(
    AppException,
    app_exception_handler
)


app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)

app.middleware("http")(request_logging_middleware)


setup_cors(app)

app.include_router(auth_router)

logger.info("CarWise application is started")
