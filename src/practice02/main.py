import logging
import math
import time
from typing import Optional, Set

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory storage
motd: Optional[str] = None
special_numbers: Set[int] = set()

# Rate limiting storage
request_timestamps: dict[str, list[float]] = {}
blacklisted_ips: dict[str, float] = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Custom exceptions
class APIError(Exception):
    status_code: int
    title: str
    detail: str
    
    def __init__(self, status_code: int, title: str, detail: str):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        super().__init__(detail)

class NumberTooLargeError(APIError):
    def __init__(self, detail: str):
        super().__init__(402, "Payment Required", detail)

class NumberNotIntegerError(APIError):
    def __init__(self, detail: str):
        super().__init__(422, "Unprocessable Entity", detail)

class ResourceExistsError(APIError):
    def __init__(self, resource: str):
        super().__init__(409, "Conflict", f"{resource} already exists")

class ResourceNotFoundError(APIError):
    def __init__(self, resource: str):
        super().__init__(404, "Not Found", f"{resource} not found")

class MethodNotAllowedError(APIError):
    def __init__(self, method: str):
        super().__init__(405, "Method Not Allowed", f"{method} method not allowed")

class RateLimitExceededError(APIError):
    def __init__(self, retry_after: int):
        super().__init__(429, "Too Many Requests", "Rate limit exceeded")
        self.retry_after = retry_after

class EnhanceYourCalmError(APIError):
    def __init__(self):
        super().__init__(420, "Enhance Your Calm", "You are being rate limited")

class TeapotError(APIError):
    def __init__(self):
        super().__init__(418, "I'm a teapot", "This IP is temporarily blacklisted")

# Response Models

class APIResponse[T](BaseModel):
    status: str
    data: T

class JSONProblem(BaseModel):
    status: str
    title: str
    detail: str
    type: str
    
    @classmethod
    def from_exception(cls, exc: Exception) -> 'JSONProblem':
        if isinstance(exc, APIError):
            return cls(
                status=str(exc.status_code),
                title=exc.title,
                detail=exc.detail,
                type=f"https://http.cat/{exc.status_code}"
            )
        return cls(
            status="500",
            title="Internal Server Error",
            detail="An unexpected error occurred",
            type="https://http.cat/500"
        )

# Request Models
class MOTDUpdate(BaseModel):
    message: str = Field(..., min_length=1, max_length=100)

class NumberRequest(BaseModel):
    number: int
    
    @field_validator('number')
    @classmethod
    def number_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Number must be positive')
        return v

class PrimeCheckRequest(BaseModel):
    number: int
    
    @field_validator('number')
    @classmethod
    def number_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Number must be positive')
        return v

# Middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"{client_host} - {request.method} {request.url.path}")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(f"{client_host} - {request.method} {request.url.path} - {response.status_code} - {process_time:.2f}ms")
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean up old blacklisted IPs
        expired_ips = [ip for ip, expiry in blacklisted_ips.items() if expiry < current_time]
        for ip in expired_ips:
            del blacklisted_ips[ip]
        
        # Check if IP is blacklisted
        if client_ip in blacklisted_ips:
            return JSONResponse(
                status_code=418,
                content=JSONProblem(
                    status="418",
                    title="I'm a teapot",
                    detail="This IP is temporarily blacklisted",
                    type="https://http.cat/418"
                ).model_dump()
            )
        
        # Initialize request timestamps for this IP
        if client_ip not in request_timestamps:
            request_timestamps[client_ip] = []
        
        # Check rate limits
        timestamps = request_timestamps[client_ip]
        one_second_ago = current_time - 1
        ten_seconds_ago = current_time - 10
        
        # Remove timestamps older than 1 second
        timestamps = [ts for ts in timestamps if ts > one_second_ago]
        
        # Check for too many requests (more than 100 in 1 second)
        if len(timestamps) >= 100:
            blacklisted_ips[client_ip] = current_time + 10  # Blacklist for 10 seconds
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "10"},
                content=JSONProblem(
                    status="429",
                    title="Too Many Requests",
                    detail="Rate limit exceeded. You have been blacklisted for 10 seconds.",
                    type="https://http.cat/429"
                ).model_dump()
            )
        
        # Check for too frequent requests (less than 0.1s between requests)
        if len(timestamps) > 0 and (current_time - timestamps[-1]) < 0.1:
            return JSONResponse(
                status_code=420,
                content=JSONProblem(
                    status="420",
                    title="Enhance Your Calm",
                    detail="You are being rate limited",
                    type="https://http.cat/420"
                ).model_dump()
            )
        
        # Check standard rate limit (1 request per second)
        if len(timestamps) >= 1:
            retry_after = 1 - (current_time - timestamps[0])
            if retry_after > 0:
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": str(int(retry_after) + 1)},
                    content=JSONProblem(
                        status="429",
                        title="Too Many Requests",
                        detail=f"Rate limit exceeded. Try again in {int(retry_after) + 1} seconds.",
                        type="https://http.cat/429"
                    ).model_dump()
                )
        
        # Update timestamps
        timestamps.append(current_time)
        request_timestamps[client_ip] = timestamps[-100:]  # Keep only the last 100 timestamps
        
        # Process the request
        response = await call_next(request)
        return response

# Initialize FastAPI app
app = FastAPI()

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    problem = JSONProblem.from_exception(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    problem = JSONProblem(
        status=str(exc.status_code),
        title=exc.detail,
        detail=str(exc.detail),
        type=f"https://http.cat/{exc.status_code}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump()
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    problem = JSONProblem(
        status="500",
        title="Internal Server Error",
        detail="An unexpected error occurred",
        type="https://http.cat/500"
    )
    return JSONResponse(
        status_code=500,
        content=problem.model_dump()
    )

# Helper functions
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

# Root endpoint
@app.get("/")
async def read_root():
    return {
        "status": "200",
        "data": {
            "Hello": "World",
            "last_motd": motd
        }
    }

# Block other HTTP methods on root
@app.delete("/")
@app.post("/")
@app.put("/")
async def method_not_allowed():
    raise MethodNotAllowedError("Method not allowed")

# MOTD endpoints
@app.put("/motd")
async def update_motd(update: MOTDUpdate):
    global motd
    motd = update.message
    return {
        "status": "200",
        "data": {"ok": True}
    }

@app.delete("/motd")
async def delete_motd():
    global motd
    if motd is None:
        raise ResourceNotFoundError("MOTD")
    motd = None
    return {
        "status": "200",
        "data": {"ok": True}
    }

@app.post("/motd")
async def post_motd_not_allowed():
    raise MethodNotAllowedError("POST")

# IP endpoint
@app.get("/my_ip")
async def get_my_ip(request: Request):
    client_host = request.client.host if request.client else "unknown"
    return {
        "status": "200",
        "data": {"ip": client_host}
    }

# Block other HTTP methods on /my_ip
@app.delete("/my_ip")
@app.post("/my_ip")
@app.put("/my_ip")
async def my_ip_method_not_allowed():
    raise MethodNotAllowedError("Method not allowed")

# Special number endpoints
@app.post("/special_number")
async def create_special_number(number_req: NumberRequest):
    if number_req.number in special_numbers:
        raise ResourceExistsError("Number")
    special_numbers.add(number_req.number)
    return {
        "status": "201",
        "data": {"ok": True}
    }

@app.put("/special_number")
async def update_special_number(number_req: NumberRequest):
    if number_req.number in special_numbers:
        return {
            "status": "200",
            "data": {"ok": True}
        }
    special_numbers.add(number_req.number)
    return {
        "status": "201",
        "data": {"ok": True}
    }

@app.delete("/special_number")
async def delete_special_number(number_req: NumberRequest):
    if number_req.number not in special_numbers:
        raise ResourceNotFoundError("Number")
    special_numbers.remove(number_req.number)
    return {
        "status": "200",
        "data": {"ok": True}
    }

@app.get("/special_number")
async def check_special_number(number: int):
    if number not in special_numbers:
        raise ResourceNotFoundError("Number")
    return {
        "status": "200",
        "data": {"ok": True}
    }

# Prime number endpoints
@app.post("/is_prime")
async def check_prime(prime_req: PrimeCheckRequest):
    if prime_req.number > 1000:
        raise NumberTooLargeError("Number is too large for current payment plan. Do you think electricity is free?")
    
    return {
        "status": "200",
        "data": {"is_prime": is_prime(prime_req.number)}
    }

# Block other HTTP methods on /is_prime
@app.get("/is_prime")
async def get_prime_not_allowed():
    raise MethodNotAllowedError("GET")

@app.put("/is_prime")
async def put_prime_not_implemented():
    return JSONResponse(
        status_code=501,
        content={
            "status": "501",
            "title": "Not Implemented",
            "detail": "Not implemented, I am sure I can make any number you want a prime number, but this HTTP response body is too small...",
            "type": "https://http.cat/501"
        }
    )

@app.delete("/is_prime")
async def delete_prime_not_implemented():
    return JSONResponse(
        status_code=501,
        content={
            "status": "501",
            "title": "Not Implemented",
            "detail": "Not implemented, I am sure I can stop any number you want from being a prime number, but this HTTP response body is too small...",
            "type": "https://http.cat/501"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "200", "data": {"status": "healthy"}}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.practice02.main:app", host="0.0.0.0", port=3500, reload=True)
