from inspect import Parameter
import json
from typing import Any

from pydantic import PydanticUserError, RootModel, TypeAdapter, ValidationError
from plugins.liveapi.utils.validation import isvalid, isvalid_json
from plugins.liveapi.validation.base import ValidationStrategy


class GeneralValidationStrategy(ValidationStrategy):
    recursion: int = 0

    def is_json(self, data: str | bytes | bytearray):
        try:
            json.loads(data)
            return True
        except:
            return False

    def validate(self, param: Parameter, data: Any) -> Any:
        try:
            try:
                type_adapter = TypeAdapter(param.annotation,
                            config={"arbitrary_types_allowed": True})
            except PydanticUserError:
                type_adapter = TypeAdapter(param.annotation)
            
            if self.is_json(data):
                return type_adapter.validate_json(data)
            else:
                return type_adapter.validate_python(data)

        except ValidationError as e:
            raise e
