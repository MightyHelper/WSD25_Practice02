# Practice 02 - Web Services Development

A FastAPI-based web service with number management capabilities, featuring rate limiting, request validation, and error handling.

## Features

- **Number Management**
  - Check if a number is prime
  - Add/remove special numbers
  - List all special numbers
  - Get number statistics

- **API Features**
  - RESTful endpoints with proper HTTP status codes
  - Request validation using Pydantic models
  - Comprehensive error handling
  - Rate limiting and IP blacklisting
  - Request logging middleware
  - Support for both JSON and form data

- **Security**
  - Rate limiting (1 request per second by default)
  - IP-based blacklisting for abusive clients
  - Input validation and sanitization
  - Secure defaults and configurations

- **Other Easter eggs**

## Running With Docker
### Prerequisites

Just [docker](https://docs.docker.com/get-started/get-docker/).

### Execution
To pull a pre-built image use
```sh
docker run -p 8000:8000 ghcr.io/mightyhelper/wsd25_practice02:latest
```
Or with docker compose:
```sh
docker-compose up
```

To build the image locally use
```sh
docker-compose up --build
```

The API will be available at `http://localhost:8000`


## Running Locally

### Prerequisites

Just UV or pip/python3.13.

1. Clone the repository:
   ```sh
   git clone git@github.com:MightyHelper/WSD25_Practice02.git
   cd Practice02-Python
   ```

2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already:
   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create a virtual environment with uv, automatically install dependencies from `pyproject.toml`, and then run the application:
   ```sh
   uv run fastapi run src/practice02/main.py
   ```

If you are not using UV, you may optionally create a virtual environment, and install packages with `pip install .`

From inside the environment you may run `fastapi run src/practice02/main.py`


## Documentation Endpoints

Check `/redoc` or `/docs` for a list of endpoints.

## Rate Limiting

The API implements rate limiting with the following rules:
- 1 request per second per IP address
- IPs exceeding the limit are temporarily blacklisted
- Blacklisted IPs receive a 429 Too Many Requests response

## Error Handling

The API returns standardized error responses in the following format:

```json
{
  "status": "error",
  "code": 404,
  "message": "Resource not found",
  "details": "The requested resource was not found"
}
```

## Testing

Run the test suite with tox:

```sh
uv run tox p
```
