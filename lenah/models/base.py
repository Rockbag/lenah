import enum
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, List, Optional

from pydantic.main import BaseModel

from lenah.authorizers import RequestAuthorizer


class RequestModel(BaseModel):
    pass


class ResponseModel(BaseModel):
    pass


class DatabaseModel(BaseModel):
    pass


class DbObjectDoesNotExist(Exception):
    pass


class PaginatedDatabaseModel(BaseModel):
    models: List[BaseModel]
    meta: Dict[str, Any]


class ModelRepository(BaseModel, ABC):

    @abstractmethod
    def db_list(self, pagination_item_count: int, pagination_page: str, *args, **kwargs) -> PaginatedDatabaseModel:
        pass

    @abstractmethod
    def db_get(self, id, *args, **kwargs) -> DatabaseModel:
        pass

    @abstractmethod
    def db_save(self, input: RequestModel, *args, **kwargs) -> DatabaseModel:
        pass

    @abstractmethod
    def db_update(self, id, input: RequestModel, *args, **kwargs) -> DatabaseModel:
        pass

    @abstractmethod
    def db_delete(self, id, *args, **kwargs):
        pass


class RestfulActions(enum.Enum):
    LIST = 'list'
    GET = 'get'
    CREATE = 'create'
    UPDATE = 'update'
    PATCH = 'patch'
    DELETE = 'delete'


class RestfulModelConfiguration(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    resource_name: str
    input_model: Type[RequestModel]
    output_model: Type[ResponseModel]
    db_model_repository: ModelRepository
    version: str = 'v1'
    pagination_item_count: int = 10
    authorizer: Any
    extra_authorizers: Optional[Dict[RestfulActions, List[RequestAuthorizer]]] = None
