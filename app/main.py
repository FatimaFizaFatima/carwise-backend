from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.cors import setup_cors
from app.core.logging import setup_logging
import logging
from app.middleware.logging import request_logging_middleware
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.cars import router as cars_router
from app.core.exceptions import AppException
from app.core.exception_handler import app_exception_handler, general_exception_handler, validation_exception_handler
from fastapi.staticfiles import StaticFiles
from app.api.v1.admin import router as admin_router
from app.api.v1.service_categories import router as service_category_router
from app.api.v1.workshops import router as workshop_router
from app.api.v1.bookings import router as booking_router
from app.api.v1.service_history import router as service_history_router
from app.api.v1.notification import router as notification_router
from app.api.v1.chat import router as chat_router

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
app.include_router(users_router)
app.include_router(cars_router)
app.include_router(admin_router)
app.include_router(service_category_router)
app.include_router(workshop_router)
app.include_router(booking_router)
app.include_router(service_history_router)
app.include_router(notification_router)
app.include_router(chat_router)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

logger.info("CarWise application is started")
