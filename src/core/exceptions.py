"""
src/core/exceptions.py
Global HTTP exception handlers for structured JSON error responses.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validation failed", "details": errors},
    )
