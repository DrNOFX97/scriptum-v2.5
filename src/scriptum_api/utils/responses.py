"""
Standardized API response utilities.
Ensures consistent response format across all endpoints.
"""

from flask import jsonify
from typing import Any, Optional, Tuple
from ..constants import (
    HTTP_OK,
    HTTP_CREATED,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_UNPROCESSABLE_ENTITY,
    HTTP_INTERNAL_ERROR
)


class ApiResponse:
    """
    Standardized API response wrapper for consistent JSON responses.

    All responses follow the format:
    {
        "success": bool,
        "data": any (optional),
        "error": str (optional),
        "message": str (optional),
        "details": dict (optional)
    }
    """

    @staticmethod
    def success(
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = HTTP_OK
    ) -> Tuple:
        """
        Return success response.

        Args:
            data: Response data
            message: Optional success message
            status_code: HTTP status code (default: 200)

        Returns:
            Tuple of (json_response, status_code)

        Example:
            >>> return ApiResponse.success({"result": "ok"}, "Operation completed")
        """
        response = {'success': True}

        if data is not None:
            response['data'] = data

        if message:
            response['message'] = message

        return jsonify(response), status_code

    @staticmethod
    def created(data: Any = None, message: Optional[str] = None) -> Tuple:
        """
        Return 201 Created response.

        Args:
            data: Created resource data
            message: Optional message

        Returns:
            Tuple of (json_response, 201)
        """
        return ApiResponse.success(data, message, HTTP_CREATED)

    @staticmethod
    def error(
        message: str,
        status_code: int = HTTP_BAD_REQUEST,
        details: Optional[dict] = None
    ) -> Tuple:
        """
        Return error response.

        Args:
            message: Error message
            status_code: HTTP status code (default: 400)
            details: Optional additional error details

        Returns:
            Tuple of (json_response, status_code)

        Example:
            >>> return ApiResponse.error("Invalid input", 400)
        """
        response = {
            'success': False,
            'error': message
        }

        if details:
            response['details'] = details

        return jsonify(response), status_code

    @staticmethod
    def bad_request(message: str = "Bad request", details: Optional[dict] = None) -> Tuple:
        """
        Return 400 Bad Request response.

        Args:
            message: Error message
            details: Optional error details

        Returns:
            Tuple of (json_response, 400)
        """
        return ApiResponse.error(message, HTTP_BAD_REQUEST, details)

    @staticmethod
    def not_found(message: str = "Resource not found") -> Tuple:
        """
        Return 404 Not Found response.

        Args:
            message: Error message

        Returns:
            Tuple of (json_response, 404)
        """
        return ApiResponse.error(message, status_code=HTTP_NOT_FOUND)

    @staticmethod
    def validation_error(errors: dict, message: str = "Validation failed") -> Tuple:
        """
        Return 422 Unprocessable Entity response for validation errors.

        Args:
            errors: Dictionary of field-level validation errors
            message: Error message

        Returns:
            Tuple of (json_response, 422)

        Example:
            >>> errors = {"email": "Invalid format", "password": "Too short"}
            >>> return ApiResponse.validation_error(errors)
        """
        return ApiResponse.error(
            message,
            status_code=HTTP_UNPROCESSABLE_ENTITY,
            details=errors
        )

    @staticmethod
    def internal_error(message: str = "Internal server error") -> Tuple:
        """
        Return 500 Internal Server Error response.

        Args:
            message: Error message

        Returns:
            Tuple of (json_response, 500)
        """
        return ApiResponse.error(message, status_code=HTTP_INTERNAL_ERROR)
