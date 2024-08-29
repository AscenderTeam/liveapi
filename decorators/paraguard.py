from functools import wraps
from typing import Callable

from core.registries.service import ServiceRegistry


class ParaGuard:
    def __init__(self, name: str | None = None) -> None:
        self.name = name
    
    def _define_singletones(self, instance: object):
        """
        NOTE: This is an internal method, don't call it if you are using this class
        """
        service_registry = ServiceRegistry()
        singletones = service_registry.get_parameters(instance)
        
        if not singletones: 
            return
        
        for name, obj in singletones.items():
            setattr(instance, name, obj)

    def __call__(self, executable: Callable[..., None]):
        if not self.name:
            executable._name = executable.__name__
        else:
            executable._name = self.name

        @wraps(executable)
        async def wrapper(*args, **kwargs):
            # NOTE: `args[0]` is always `self` parameter of the method or parent class of the method
            self._define_singletones(args[0])
            return await executable(*args, **kwargs)

        return wrapper