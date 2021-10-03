from typing import Optional, Dict, Any

from pydantic.main import BaseModel

import chalice


class Response(BaseModel):
    success: bool
    status_code: int
    message: Optional[str]
    error_code: Optional[str]
    data: Optional[Dict[str, Any]]

    def as_chalice_response(self, headers: Optional[Dict[str, Any]] = None):
        if not headers:
            headers = {'content-type': 'application/json'}
        return chalice.Response(status_code=self.status_code, body=self.json(), headers=headers)


class Success(Response):
    success = True
    status_code = 200


class Created(Response):
    success = True
    status_code = 201


class HttpMethodNotAllowed(Response):
    success = False
    error_code = "method_not_allowed"
    status_code = 405


class BadRequest(Response):
    success = False
    error_code = "bad_request"
    status_code = 400


class Unauthorized(Response):
    success = False
    error_code = "unauthorised"
    status_code = 401

class NotFound(Response):
    success = False
    error_code = "not_found"
    status_code = 400
