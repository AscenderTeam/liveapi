from functools import wraps
from typing import Any, Callable

from fastapi import Depends


class ParamGuards:

    def _define_dependencies(self, executable: Callable[..., None]):
        """
        NOTE: This is an internal method, don't call it if you are using this class in your code.
        Using it outside of it's purpose is prohibited
        """
        from inspect import signature, Parameter
        
        # NOTE: Currently, decorator fetches and recognizes as param dependency only methods which will end on `_guard` suffix
        methods = [getattr(getattr(self, method), "_name", method) for method in dir(self) if callable(getattr(self, method)) and method.endswith('_guard')]

        # WARN: Signature of executable being changed
        sig = signature(executable)
        new_parameters = []

        for name, param in sig.parameters.items():
            if name + "_guard" in methods and param.default == Parameter.empty:
                new_parameters.append(
                    Parameter(name, param.kind, annotation=param.annotation, default=Depends(getattr(self, f"{name}_guard"))))
            else:
                new_parameters.append(param)


        new_sig = sig.replace(parameters=new_parameters)
        executable.__signature__ = new_sig

        return executable

    def __call__(self, executable: Callable[..., None]) -> Any:
        # NOTE: This function allows dependency injection on the guard only when it will be called
        _updatedfunc = self._define_dependencies(executable)
        
        @wraps(executable)
        async def wrapper(*args, **kwargs):
            return await _updatedfunc(*args, **kwargs)

        return wrapper