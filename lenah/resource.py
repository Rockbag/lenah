from copy import deepcopy
from typing import Optional, Set, Type

from pydantic.error_wrappers import ValidationError

from lenah.models.base import RestfulModelConfiguration, RequestModel, DbObjectDoesNotExist, RestfulActions
from lenah.responses import HttpMethodNotAllowed, BadRequest, Success, Unauthorized, NotFound, Created

_action_url_mappings = {
    RestfulActions.LIST: ('', 'GET'),
    RestfulActions.GET: ('/{id}', 'GET'),
    RestfulActions.CREATE: ('', 'POST'),
    RestfulActions.UPDATE: ('/{id}', 'PUT'),
    RestfulActions.PATCH: ('/{id}', 'PATCH'),
    RestfulActions.DELETE: ('/{id}', 'DELETE'),
}


class RestfulResource:
    """
    Creates a RESTful resource based on the configuration provided. It's an opinionated class that
    by default generates the following routes:
    - GET /{version}/{resource_name} to list objects of the resource type. Pagination is controlled through the pagination_item_count and pagination_page params. Number of items returned equals to max(object.count(), pagination_item_count). Items are returned from page `pagination_page`
    - GET /{version}/{resource_name}/{id} to fetch a specific object of the resource type
    - POST /{version}/{resource_name} to create a new object of the resource type. Input data must be the `json` representation of the specified RequestModel type
    - PUT /{version}/{resource_name}/{id} to do a full update on a specific object of the resource type. Input data must be the `json` representation of the specified ResourceModel type.
    - PATCH /{version}/{resource_name}/{id} to do a json merge patch update of a specific object of the resource type. Input data must be the `json` dict describing the changes to the specified resource.
    - DELETE /{version}/{resource_name}/{id} to delete a specific object of the resource type
    - GET /{version}/{resource_name}/swagger.json to get the swagger specification for this API
    """

    def list(self, request):
        request_params = request.query_params or {}
        pagination_item_count_param = int(request_params.get('pagination_item_count',
                                                             self._config.pagination_item_count))
        if pagination_item_count_param < 1:
            return BadRequest(message="pagination_item_count cannot be less than 1").as_chalice_response()

        pagination_page = request_params.get('pagination_page', None)
        data = self._config.db_model_repository.db_list(pagination_item_count_param, pagination_page)
        return Success(data={'models': [self._config.output_model(**model.dict()) for model in data.models],
                             'meta': data.meta}).dict()

    def fetch(self, request, id):
        request_params = request.query_params or {}
        try:
            data = self._config.db_model_repository.db_get(id, **request_params).dict()
        except DbObjectDoesNotExist:
            return NotFound(data={'id': id}, message=f"Object with id {id} cannot be found.").as_chalice_response()
        return Success(data=self._config.output_model(**data)).dict()

    def update(self, request, id, input_model: RequestModel):
        try:
            request_params = request.query_params or {}
            data = self._config.db_model_repository.db_update(id, input_model, **request_params).dict()
        except DbObjectDoesNotExist:
            return NotFound(data={'id': id}, message=f"Object with id {id} cannot be found.").as_chalice_response()

        return Success(data=self._config.output_model(**data)).dict()

    def patch(self, request, id):
        import json_merge_patch
        db_model = self._config.db_model_repository
        updated = json_merge_patch.merge(deepcopy(db_model.db_get(id).dict()), deepcopy(request.json_body))
        try:
            updated_model = db_model.db_update(id, RequestModel(**updated)).dict()
        except DbObjectDoesNotExist:
            return NotFound(data={'id': id}, message=f"Object with id {id} cannot be found.").as_chalice_response()

        return Success(data=self._config.output_model(**updated_model)).dict()

    def delete(self, request, id):
        request_params = request.query_params or {}
        self._config.db_model_repository.db_delete(id, **request_params)
        return Success(data={'id': id}).dict()

    def create(self, request, input_model: RequestModel):
        saved_model = self._config.db_model_repository.db_save(input_model).dict()
        return Created(data=self._config.output_model(**saved_model)).as_chalice_response()

    def api_docs(self):
        pass

    def __init__(self, chalice_app, config: RestfulModelConfiguration,
                 enabled_actions: Optional[Set[RestfulActions]] = None, generate_api_docs: Optional[bool] = True):
        action_function_mapping = {
            RestfulActions.LIST: self.list,
            RestfulActions.GET: self.fetch,
            RestfulActions.CREATE: self.create,
            RestfulActions.DELETE: self.delete,
            RestfulActions.UPDATE: self.update,
            RestfulActions.PATCH: self.patch
        }

        self.enabled_actions = enabled_actions or set(action_function_mapping.keys())
        self._config = config
        self._chalice_app = chalice_app
        self._authorizers = self._config.extra_authorizers or dict()

        for action in self.enabled_actions:
            url, method = _action_url_mappings[action]
            view_func = action_function_mapping[action]
            request_validator = self._validate_request(action)
            route = f"/{config.version}/{config.resource_name}{url}"
            chalice_app.route(route, methods=[method], authorizer=self._config.authorizer)(request_validator(view_func))

        if generate_api_docs:
            chalice_app.route(f"/{config.version}/{config.resource_name}/swagger.json", methods=['GET'])(
                self.api_docs
            )

    def _validate_request(self, restful_action: RestfulActions):
        """
        Puts the request through a set of validators:
        1. Checks if the http method on this resource is enabled. Returns method_not_allowed response if it's not.
        2. Parses and validates the input into a `RequestModel` instance. Returns bad_request if the input is invalid.
        """

        def _parse_input(request, input_model_class: Type[RequestModel]) -> Optional[RequestModel]:
            """
            Parses the request body into a type of RequestModel supplied on the resource. Parsing
            also validates the model.
            If the model is invalid the method returns a bad_request response.
            """
            if restful_action not in {RestfulActions.UPDATE, RestfulActions.CREATE, RestfulActions.PATCH}:
                return None

            input_model = input_model_class(**request.json_body)
            return input_model

        def decorator(func):
            def wrapper(*args, **kwargs):
                if restful_action not in self.enabled_actions:
                    return HttpMethodNotAllowed(
                        message=f"{restful_action.name} is not allowed on this resource.").as_chalice_response()

                request = self._chalice_app.current_request
                try:
                    input_model_instance = _parse_input(request, self._config.input_model)
                    if input_model_instance:
                        kwargs['input_model'] = input_model_instance
                except ValidationError as e:
                    return BadRequest(message=str(e)).as_chalice_response()

                kwargs['request'] = request
                authorizers = self._authorizers.get(restful_action)
                if authorizers:
                    for authorizer in authorizers:
                        auth_result = authorizer.check(*args, **kwargs)
                        if not auth_result.success:
                            return Unauthorized(message=auth_result.message).as_chalice_response()

                return func(*args, **kwargs)

            return wrapper

        return decorator
