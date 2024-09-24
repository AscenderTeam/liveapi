from functools import wraps
import os
from typing import Any

from fastapi import Depends

from core.registries.service import ServiceRegistry


class LiveEvent:
    def __init__(self, event_name: str) -> None:
        self.event_name = event_name
        self.service_registry = ServiceRegistry()
    
    def get_namespace(self, executable):
        # Unwrapping function if it was wrapped by multiple decorators
        original_func = executable
        while hasattr(original_func, '__wrapped__'):
            original_func = original_func.__wrapped__

        # NOTE: The name of each controller is tied to the first parent folder where three (endpoints.py, service.py and repository.py) are located in
        # So in LiveAPI Plugin, we use name of controller as a name of namespace and to get the name of controller, we get the name of first parent folder
        file_path = original_func.__code__.co_filename

        folder_name = os.path.basename(os.path.dirname(os.path.abspath(file_path)))
        
        return folder_name

    def __call__(self, executable) -> Any:
        
        dependencies: list[Depends] = getattr(executable, "_dependencies", [])
        executable._listener_metadata = {"event_name": self.event_name,
                                         "namespace": self.get_namespace(executable),
                                         "dependencies": dependencies}

        @wraps(executable)
        async def wrapper(*args, **kwargs):
            return await executable(*args, **kwargs)
        
        return wrapper