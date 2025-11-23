import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from .middleware.logging_middleware import LoggingMiddleware
from .middleware.rate_limit_middleware import RateLimitMiddleware
from .request.motd_request import MOTDUpdate
from .request.number_request import NumberRequest
from .request.prime_check_request import PrimeCheckRequest
from .response.api_response import APIResponse
from .response.json_response import JSONProblem
from .utils import is_prime
from .state import State
from . import constants as const

# Custom exceptions
from .errors import (
    APIError,
    ResourceExistsError,
    ResourceNotFoundError,
    MethodNotAllowedError,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)

def create_app(enable_rate_limiting: bool = True) -> FastAPI:
    """
    Create and configure the FastAPI application.

    We need to wrap this so we can configure how the app is built for testing.
    """
    logger.info(f"Creating app, rate_limiting = {enable_rate_limiting}")
    app = FastAPI(
        title=const.API_TITLE,
        description=const.API_DESCRIPTION,
        version=const.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    app.add_middleware(LoggingMiddleware)
    if enable_rate_limiting:
        app.add_middleware(RateLimitMiddleware)

    # Exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle API errors."""
        problem = JSONProblem.from_exception(exc)
        return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        problem = JSONProblem(
            status=str(exc.status_code),
            title=exc.detail,
            detail=str(exc.detail),
            detail_obj=exc.detail,
            type=f"https://http.cat/{exc.status_code}",
        )
        return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        problem = JSONProblem(
            status=str(HTTPStatus.UNPROCESSABLE_ENTITY),
            title="Unprocessable Entity",
            detail=str(exc.errors()),
            detail_obj=exc.errors(),
            type=f"https://http.cat/{HTTPStatus.UNPROCESSABLE_ENTITY}",
        )
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=problem.model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle all other exceptions."""
        logger.error("Unhandled exception: %s", str(exc), exc_info=True)
        problem = JSONProblem(
            status=str(HTTPStatus.INTERNAL_SERVER_ERROR),
            title="Internal Server Error",
            detail=HTTPStatus.INTERNAL_SERVER_ERROR.description,
            detail_obj=HTTPStatus.INTERNAL_SERVER_ERROR.description,
            type=f"https://http.cat/{HTTPStatus.INTERNAL_SERVER_ERROR}",
        )
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content=problem.model_dump()
        )

    # Root endpoint
    @app.get("/", response_model=APIResponse[dict[str, Any]])
    async def motd_get() -> dict[str, Any]:
        """Root endpoint that returns a welcome message and the current MOTD.

        Returns:
            Dict containing a welcome message and the current MOTD.
        """
        return (
            APIResponse[dict[str, Any]]
            .success(data={"Hello": "World", "last_motd": State.motd})
            .model_dump()
        )

    # Block other HTTP methods on root
    @app.delete(
        "/", response_model=APIResponse[dict[str, str]], include_in_schema=False
    )
    @app.post("/", response_model=APIResponse[dict[str, str]], include_in_schema=False)
    @app.put("/", response_model=APIResponse[dict[str, str]], include_in_schema=False)
    async def method_not_allowed() -> dict[str, Any]:
        """Handle unsupported HTTP methods on the root endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error for unsupported methods.
        """
        raise MethodNotAllowedError(const.ERROR_METHOD_NOT_ALLOWED)

    # MOTD endpoints
    @app.put(
        "/motd",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
    )
    async def motd_put(update: MOTDUpdate) -> dict[str, Any]:
        """Update the Message of the Day.

        Args:
            update: The new MOTD message.

        Returns:
            A success response if the MOTD was updated.
        """
        State.motd = update.message
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    @app.delete(
        "/motd",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
    )
    async def motd_delete() -> dict[str, Any]:
        """Delete the current Message of the Day.

        Returns:
            A success response if the MOTD was deleted.

        Raises:
            ResourceNotFoundError: If there is no MOTD to delete.
        """
        if State.motd is None:
            raise ResourceNotFoundError("MOTD")
        State.motd = None
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    @app.post(
        "/motd",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False,
    )
    async def post_motd_not_allowed() -> None:
        """Handle POST requests to the MOTD endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error as POST is not allowed.
        """
        raise MethodNotAllowedError("POST")

    # IP endpoint
    @app.get(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_200_OK,
    )
    async def ip_get(request: Request) -> dict[str, Any]:
        """Get the IP address of the client making the request.

        Args:
            request: The incoming request.

        Returns:
            A response containing the client's IP address.
        """
        client_host: str = request.client.host if request.client else "unknown"
        return (
            APIResponse[dict[str, str]]
            .success(data={"ip": client_host}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    # Block other HTTP methods on /my_ip
    @app.delete(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
    @app.post(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
    @app.put(
        "/my_ip",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False,
    )
    async def my_ip_method_not_allowed() -> None:
        """Handle unsupported HTTP methods on the /my_ip endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error for unsupported methods.
        """
        raise MethodNotAllowedError(HTTPStatus.METHOD_NOT_ALLOWED.description)

    # Special number endpoints
    @app.post(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_201_CREATED,
    )
    async def special_number_create(
        number_req: NumberRequest, response: Response
    ) -> dict[str, Any]:
        """Add a new special number.

        Args:
            number_req: The number to add.

        Returns:
            A success response if the number was added.

        Raises:
            ResourceExistsError: If the number is already special.
        """
        if number_req.number in State.special_numbers:
            raise ResourceExistsError("Number")
        State.special_numbers.add(number_req.number)
        # Kinda sucks to have to do this and if the project was serious would probably have some better way to do this...
        response.status_code = status.HTTP_201_CREATED
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_201_CREATED)
            .model_dump()
        )

    @app.put(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        responses={
            status.HTTP_200_OK: {"description": "Number was already special"},
            status.HTTP_201_CREATED: {
                "description": "Number was added to special numbers"
            },
        },
    )
    async def special_number_update(
        number_req: NumberRequest, response: Response
    ) -> dict[str, Any]:
        """Add or update a special number.

        Args:
            number_req: The number to add or update.

        Returns:
            A success response with status 200 if the number was already special,
            or 201 if it was newly added.
        """
        if number_req.number in State.special_numbers:
            return (
                APIResponse[dict[str, bool]]
                .success(data={"ok": True}, status_code=status.HTTP_200_OK)
                .model_dump()
            )

        State.special_numbers.add(number_req.number)
        # Kinda sucks to have to do this and if the project was serious would probably have some better way to do this...
        response.status_code = status.HTTP_201_CREATED
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_201_CREATED)
            .model_dump()
        )

    @app.delete(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
    )
    async def special_number_delete(number_req: NumberRequest) -> dict[str, Any]:
        """Remove a number from the special numbers set.

        Args:
            number_req: The number to remove.

        Returns:
            A success response if the number was removed.

        Raises:
            ResourceNotFoundError: If the number was not special.
        """
        if number_req.number not in State.special_numbers:
            raise ResourceNotFoundError("Number")
        State.special_numbers.remove(number_req.number)
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    @app.get(
        "/special_number",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
    )
    async def special_number_get(number: int) -> dict[str, Any]:
        """Check if a number is special.

        Args:
            number: The number to check.

        Returns:
            A success response if the number is special.

        Raises:
            ResourceNotFoundError: If the number is not special.
        """
        if number not in State.special_numbers:
            raise ResourceNotFoundError("Number")
        return (
            APIResponse[dict[str, bool]]
            .success(data={"ok": True}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    # Prime number endpoints
    @app.post(
        "/is_prime",
        response_model=APIResponse[dict[str, bool]],
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_402_PAYMENT_REQUIRED: {
                "description": "Number is too large for current payment plan"
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Invalid number provided"
            },
        },
    )
    async def check_prime(prime_req: PrimeCheckRequest) -> dict[str, Any]:
        """Check if a number is prime.

        Args:
            prime_req: The number to check.

        Returns:
            A response indicating if the number is prime.

        Raises:
            NumberTooLargeError: If the number is too large to check.
        """
        return (
            APIResponse[dict[str, bool]]
            .success(
                data={"is_prime": is_prime(prime_req.number)},
                status_code=status.HTTP_200_OK,
            )
            .model_dump()
        )

    # Block other HTTP methods on /is_prime
    @app.get(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False,
    )
    async def get_prime_not_allowed() -> None:
        """Handle GET requests to the /is_prime endpoint.

        Raises:
            MethodNotAllowedError: Always raises this error as GET is not allowed.
        """
        raise MethodNotAllowedError("GET")

    @app.put(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        include_in_schema=False,
    )
    async def put_prime_not_implemented() -> dict[str, Any]:
        """Handle PUT requests to the /is_prime endpoint.

        Returns:
            A response indicating that the operation is not implemented.
        """
        return APIResponse[dict[str, str]](
            status=str(status.HTTP_501_NOT_IMPLEMENTED),
            data={
                "error": (
                    "Not implemented, I am sure I can make any number you want a prime number, "
                    "but this HTTP response body is too small..."
                )
            },
        ).model_dump()

    @app.delete(
        "/is_prime",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        include_in_schema=False,
    )
    async def delete_prime_not_implemented() -> dict[str, Any]:
        """Handle DELETE requests to the /is_prime endpoint.

        Returns:
            A response indicating that the operation is not implemented.
        """
        return APIResponse[dict[str, str]](
            status=str(status.HTTP_501_NOT_IMPLEMENTED),
            data={
                "error": (
                    "Not implemented, I am sure I can stop any number you want from being a prime number, "
                    "but this HTTP response body is too small..."
                )
            },
        ).model_dump()

    # Health check endpoint
    @app.get(
        "/health",
        response_model=APIResponse[dict[str, str]],
        status_code=status.HTTP_200_OK,
    )
    async def health_check() -> dict[str, Any]:
        """Health check endpoint.

        Returns:
            A response indicating the service is healthy.
        """
        return (
            APIResponse[dict[str, str]]
            .success(data={"status": "healthy"}, status_code=status.HTTP_200_OK)
            .model_dump()
        )

    return app


real_app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.practice02.main:real_app",
        reload=True,
    )
