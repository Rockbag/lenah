import json
from datetime import datetime
from typing import List, Dict, Any, Type, Optional

from pydantic.main import BaseModel
from pynamodb.attributes import MapAttribute
from pynamodb.models import Model

from lenah.models.base import ModelRepository, RequestModel, DbObjectDoesNotExist, PaginatedDatabaseModel


class BasePynamoDbModel(Model):

    def dict(self):
        ret_dict = {}
        for name, attr in self.attribute_values.items():
            ret_dict[name] = self._attr2obj(attr)

        return ret_dict

    def _attr2obj(self, attr):
        if isinstance(attr, list):
            _list = []
            for l in attr:
                _list.append(self._attr2obj(l))
            return _list
        elif isinstance(attr, MapAttribute):
            _dict = {}
            for k, v in attr.attribute_values.items():
                _dict[k] = self._attr2obj(v)
            return _dict
        elif isinstance(attr, datetime):
            return attr.isoformat()
        else:
            return attr


class PynamoDbPaginationResult(PaginatedDatabaseModel):
    class Config:
        arbitrary_types_allowed = True

    models: List[BasePynamoDbModel]
    meta: Optional[Dict[str, Any]]


class PynamoDbModelRepository(ModelRepository):
    db_model: Type[BasePynamoDbModel]

    def db_list(self, pagination_item_count: int, pagination_page: str, *args, **kwargs) -> PynamoDbPaginationResult:
        last_evaluated_key = json.loads(pagination_page) if pagination_page else None
        scan_result = self.db_model.scan(last_evaluated_key=last_evaluated_key, limit=pagination_item_count)

        return PynamoDbPaginationResult(
            models=[model for model in scan_result],
            meta={
                'last_evaluated_key': scan_result.last_evaluated_key
            }
        )

    def db_get(self, id, *args, **kwargs) -> BasePynamoDbModel:
        try:
            return self.db_model.get(hash_key=id, range_key=kwargs.get('range_key'))
        except Model.DoesNotExist as e:
            raise DbObjectDoesNotExist from e

    def db_save(self, input: RequestModel, *args, **kwargs) -> BasePynamoDbModel:
        model = self.db_model(**input.dict())
        model.save()
        return model

    def db_update(self, id, input: RequestModel, *args, **kwargs) -> BasePynamoDbModel:
        model = self.db_get(id, *args, **kwargs)
        actions = [
            attribute.set(input.dict().get(attribute_name))
            for
            attribute_name, attribute
            in
            self.db_model.__dict__['_attributes'].items()
            if not attribute.is_hash_key and not attribute.is_range_key
        ]
        model.update(actions=actions)
        return self.db_model(**input.dict())

    def db_delete(self, id, *args, **kwargs):
        model = self.db_get(id, *args, **kwargs)
        model.delete()
