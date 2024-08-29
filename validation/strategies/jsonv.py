from inspect import Parameter
import json
from typing import Any

from pydantic import ValidationError
from ..base import ValidationStrategy


class JSONValidationStrategy(ValidationStrategy):
    recursion_limit: int
    recursion: int

    def __init__(self, recursion_limit: int = 1) -> None:
        super().__init__()
        self.recursion_limit = recursion_limit
        self.recursion = 0

    def validate(self, param: Parameter, data: Any) -> Any:
        try:
            return param.annotation.model_validate_json(data)
        except ValidationError as e:
            if self.recursion >= self.recursion_limit:
                raise e
            
            self.recursion += 1
            try:
                return self.validate(param, json.loads(data)[param.name])
            except (json.JSONDecodeError, KeyError):
                raise e