import dataclasses
from typing import Optional


@dataclasses.dataclass
class AuthorizationResult:
    success: bool
    message: Optional[str] = None


class RequestAuthorizer:
    """
    A request authorizer is a custom rule matcher to further restrict access to an endpoint.
    An authorizer works with the same params as the view function. The available params depend on the action itself.
    The following parameters allowed per action:
      - LIST: request(ChaliceRequest), pagination_item_count(int), pagination_page(int)
      - GET: request(ChaliceRequest), id
      - UPDATE: request(ChaliceRequest), id, input_model(RequestModel)
      - PATCH: request(ChaliceRequest), id
      - DELETE: request(ChaliceRequest), id
      - CREATE: request(ChaliceRequest), input_model(RequestModel)
    """

    def check(self, *args, **kwargs) -> AuthorizationResult:
        pass
