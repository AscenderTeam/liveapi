import inspect
from typing import Any, Awaitable, Callable

from pydantic import BaseModel

from core.optionals.base.dto import BaseDTO
from core.optionals.base.response import BaseResponse
from core.registries.service import ServiceRegistry
from plugins.liveapi.context import SIOContext
from fastapi.params import Depends, Header

from plugins.liveapi.engines.base import BaseEngine
from plugins.liveapi.error import ErrorHandler
from plugins.liveapi.types.authorization import SIOAuthorization
from plugins.liveapi.utils.validation import isvalid
from plugins.liveapi.validation.depends import ValidationDepends
from plugins.liveapi.validation.strategies.authorization import AuthorizationValidationStrategy
from plugins.liveapi.validation.strategies.general import GeneralValidationStrategy
from plugins.liveapi.validation.strategies.headers import HeaderValidationStrategy
from plugins.liveapi.validation.strategies.jsonv import JSONValidationStrategy
from plugins.liveapi.validation.validation import Validator


class Listener:
    def __init__(
            self, event_name: str, 
            callback: Callable[..., Awaitable[Any | None]],
            dependencies: list[Depends] = [],
            namespace: str | None = None
        ) -> None:

        self.event_name = event_name
        self.callback = callback
        self.dependencies = dependencies
        self.namespace = namespace
        self.service_registry = ServiceRegistry()
    
    def get_parameters(self, callback: Callable[..., Awaitable[Any | None]]) -> dict[str, inspect.Parameter]:
        parameters = inspect.signature(callback).parameters

        _formated: dict[str, BaseDTO | BaseResponse | Any] = {}

        for name, param in parameters.items():
            _formated[name] = param
        
        return _formated
    
    def process_parameters(
            self, 
            params: dict[str, inspect.Parameter],
            data: Any,
            headers: dict[str, str] | None,
            _ctx: SIOContext
        ):
        payload: dict[str, Any] = {}

        for name, param in params.items():
            payload[name] = self.validate_parameter(name, param,
                                                    data, headers, _ctx)
        
        return payload
    
    def validate_parameter(
            self,
            name: str,
            param: inspect.Parameter,
            data: Any,
            headers: dict[str, str] | None,
            _ctx: SIOContext
        ):
        if isvalid(param.annotation, SIOContext) or name == "ctx":
            return _ctx
        
        if isvalid(Header, param.default):
            validator = Validator(HeaderValidationStrategy())
            return validator.validate(param, headers)
        
        if isvalid(Depends, param.default):
            return ValidationDepends(param, param.default.dependency,
                                     use_cache=param.default.use_cache)
        
        if isinstance(param.annotation, type) and issubclass(param.annotation, SIOAuthorization):
            validator = Validator(AuthorizationValidationStrategy())
            return validator.validate(param, data)
        
        if isvalid(param.annotation, BaseModel):
            validator = Validator(JSONValidationStrategy())
            return validator.validate(param, data)
        
        validator = Validator(GeneralValidationStrategy())
        return validator.validate(param, data)

    async def invoke(
            self, 
            callback: Callable[..., Awaitable[Any | None]], 
            sid: str, data: Any, 
            *args, **kwargs
        ):
        # SocketIO engine - Is the main server engine allows to run SIO
        # NOTE: It also responsible for generation `SIOContext` which is used in SocketIO Context (CTX)
        engine = self.service_registry.get_singletone(BaseEngine)

        # NOTE: Error handler here handles that are same as FastAPI's error handler,
        # It handles FastAPI's HTTPException and during connection it refuses connection and during events it sends error messages
        error_handler = self.service_registry.get_singletone(ErrorHandler)
        
        # NOTE: These parameters are params defined in Listener's callback function or Guard's `handle_access` function.
        # It extracts annotations and default types of function for further *validation* and *assignation* purposes
        params = self.get_parameters(callback)

        # SIO Context (SocketIO Context) - Is context manager for each `event` created new asyncio thread and each of them do have SIOContext
        # NOTE: SIOContext may differ in each event request as because it contains information about current request
        # It also differs if there is different namespace
        # It contains additional `reply` and `streaming_response` methods allowing developers to use them if for quick actions and comfortability
        _ctx = SIOContext(engine, self.namespace,
                          self.event_name, sid)
        
        # NOTE: Headers are presented only during `on_connect` event. After successfully estabilishing connection, headers will be always `None`
        headers: dict[str, str] | None = None
        if isinstance(data, dict) and self.event_name == "connect":
            headers = {k.decode(): v.decode() for k, v in data.get("asgi.scope", {}).get("headers", [])}

        try:
            # Preparing payload with all collected earlier data
            payload = self.process_parameters(params, data, headers, _ctx)
            payload = await self.invoke_paramdeps(payload, data, headers, _ctx)
            # Executing the Listener's callback function and handling errors it may raise
            # The priority exceptions are ValidationError and HTTPException
            _response = await callback(**payload)

        except Exception as e:
            await error_handler(_ctx, self.event_name, e)
            raise e

        error_handler.logger.info(f"([purple]{self.namespace}[/purple]) received [green]{self.event_name}[/green] event message")

        return _response
    
    async def invoke_paramdeps(
            self, 
            payload: dict[str, Any],
            data: Any, 
            headers: dict[str, str] | None,
            _ctx: SIOContext,
            *args, **kwargs
        ):
        """
        Invokes parameter dependnecies.

        In FastAPI there are parameter dependencies, the dependencies that are defined straight in parameter of router endpoint.
        To replicate this we have `invoke_paramdeps` method which will double loop through payload that was outputed invoke itself.
        If it finds parameter which is wrapped by FastAPI's `params.Depends` class, it will call new `invoke` method recursively
        """
        for name, obj in payload.items():
            if isinstance(obj, ValidationDepends):
                response = await self.invoke(obj.dependency, _ctx.session_id, data, *args, **kwargs)
                response = self.validate_parameter(name, inspect.Parameter(obj.param.name, obj.param.kind,
                                                                           annotation=obj.param.annotation), response, headers, _ctx)
                payload[name] = response
        
        return payload
        

    async def __call__(self, sid: str, data: Any, *args, **kwargs):
        for dependency in self.dependencies:
            await self.invoke(dependency.dependency, sid, data, *args, **kwargs)
        
        return await self.invoke(self.callback, sid, data, *args, **kwargs)
        