from fastapi import FastAPI

app = FastAPI()


# POST, GET, PUT, DELETE
# Implement Middleware
# Use Various HTTP Response Codes
# Use at least two responses each from 2xx, 4xx, and 5xx categories
# Follow the standardized format presented in the lecture slides
#

# Data model:
#

# We will have a Generic base class called APIResponse (Pydantic model) which will wrap responses our API gives adding some fiels:
#   {"status": "<status code>", "data": <the data>}
# We will have a ProblemResponse (Pydantic model) which will wrap error responses our API gives adding some fiels:
#   {"status": "<status code>", "title": "<title>", "detail": "<detail>", "type": "<type>"}


# GET / => 200: {"Hello": "World", "last_motd": "<MOTD>"}
# DELETE / => 405: {"error": "Method not allowed"}
# POST / => 405: {"error": "Method not allowed"}
# PUT / => 405: {"error": "Method not allowed"}
# PUT /motd {"message": "<your message>"}
#   200: {"ok": true}
#   422: {"error": "Message is too long"} [If message > 100]
#   500: {"error": "OOM"}
# DELETE /motd {"message": "<your message>"}
#   200: {"ok": true}
#   404: {"error": "MOTD was not set"}
# POST /motd => 405: {"error": "Method not allowed"}



# GET /my_ip => 200: {"ip": "<your ip address>"}
# DELETE /my_ip => 405: {"error": "Method not allowed"}
# POST /my_ip => 405: {"error": "Method not allowed"}
# PUT /my_ip => 405: {"error": "Method not allowed"}


# POST /special_number {"number": <your number>}
#   201: {"ok": true}
#   409: {"error": "Number is already special"}
#   422: {"error": "Number is not an integer"}
#   500: {"error": "OOM"}
# PUT /special_number {"number": <your number>}
#   200: {"ok": true}
#   201: {"ok": true} [If the number wasn't special yet]
#   422: {"error": "Number is not an integer"}
#   500: {"error": "OOM"}
# DELETE /special_number {"number": <your number>}
#   200: {"ok": true}
#   404: {"error": "Number was not special"}
# GET /special_number {"number": <your number>}
#   200: {"ok": true}
#   404: {"error": "Number was not special"}

# POST /is_prime {"number": <your number>}
#   200: {"is_prime": true / false}
#   402: {"error": "Number is too large for current payment plan. Do you think electricity is free?"} [If number > 1000]
#   422: {"error": "Number is not an integer"}
# GET /is_prime {"number": <your number>} => 405: {"error": "Method not allowed"}
# PUT /is_prime {"number": <your number>} => 501: {"error": "Not implemented, I am sure I can make any number you want a prime number, but this HTTP response body is too small..."}
# DELETE /is_prime {"number": <your number>} => 501: {"error": "Not implemented, I am sure I can stop any number you want from being a prime number, but this HTTP response body is too small..."}






# Middleware 1: Logging - log in the following format:
# [UTC Timestamp] [logger] [level] [request source ip if applicable] - [message]

# Middleware 2: Error handling - catch all exceptions and generate some info
# Create a JSONProblem pydantic model that will be used to generate the error responses
# Create a custom HTTPException class that contains the right status code and message
# Add an abstract .content(request) method that will return a JSONProblem pydantic model
# Implement a custom exception handler that will catch all exceptions and return a JSONProblem pydantic model
# If the exception is part of our HTTPException tree it should return the right exception code and content.
# If the exception is not part of our HTTPException tree it should return 500 and a generic error message. While logging more details to the error log

# Middleware 3: Rate limiting - we admit up to 1 request per 1 seconds per source ip.
# If this is exceeded, we respond with HTTP 429 with an appropriate retry-after and a JSONProblem pydantic model
# If the last request by this IP was less than 0.1 seconds ago we instead send an HTTP 420.
# If the same IP sends more than 100 requests in a second it is blacklisted for 10 seconds.
# All requests to blacklisted IPs are responded to with HTTP 418


if __name__ == "__main__":
    app()
