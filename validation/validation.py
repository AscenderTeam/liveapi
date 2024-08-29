from inspect import Parameter
from typing import Any
from .base import ValidationStrategy


class Validator:
    def __init__(self, validation_strategy: ValidationStrategy) -> None:
        self.validation_strategy = validation_strategy

    def validate(self, param: Parameter, data: Any) -> Any:
        return self.validation_strategy.validate(param, data)