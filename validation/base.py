from inspect import Parameter
from typing import Any


class ValidationStrategy:
    def validate(self, param: Parameter, data: Any) -> Any:
        raise NotImplementedError("Subclasses should implement this method.")