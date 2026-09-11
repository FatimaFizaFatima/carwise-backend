import logging
import time

from fastapi import Request


logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    logger.info(
        "%s %s | %s | %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration * 1000,
    )

    return response