from typing import Any, Dict

from asyncprawcore.exceptions import ResponseException as RedditAPIError
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database-related errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "message": str(exc)
        }
    )

async def reddit_api_error_handler(request: Request, exc: RedditAPIError) -> JSONResponse:
    """Handle Reddit API-related errors."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Reddit API error occurred",
            "message": str(exc)
        }
    )

async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "message": str(exc)
        }
    )

async def not_found_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "Resource not found",
            "message": str(exc)
        }
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc)
        }
    ) 