from inspect import Parameter
from typing import Any

from fastapi import HTTPException
from ..base import ValidationStrategy


class HeaderValidationStrategy(ValidationStrategy):
    def validate(self, param: Parameter, data: dict[str, str]) -> Any:
        if not (data := data.get(param.default.alias.lower())):
            if param.default.is_required():
                raise HTTPException(422, "Header is not present")
            else:
                data = param.default.default
        return data
