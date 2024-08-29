from inspect import Parameter
from typing import Any, Callable
from fastapi.params import Depends


class ValidationDepends(Depends):
    def __init__(
            self, 
            param: Parameter, 
            dependency: Callable[..., Any] | None = None, 
            *, use_cache: bool = True
        ):
        super().__init__(dependency, use_cache=use_cache)
        self.param = param