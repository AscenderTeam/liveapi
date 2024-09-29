from inspect import isclass
from typing import Any, Awaitable, Callable
from fastapi_socketio import SocketManager
from pydantic import RootModel
import socketio
from core.application import Application
from core.optionals.base.dto import BaseDTO
from core.optionals.base.response import BaseResponse
from plugins.liveapi.engines.base import BaseEngine


class SocketIORedisEngine(BaseEngine):
    def __init__(self, app: Application,
                 redis_connection: str,
                 redis_channel: str = "socketio",
                 redis_options: dict[str, Any] | None = None,
                 location: str = "/ws",
                 cors_allowed_origins: str | list = '*') -> None:
        self._manager = socketio.RedisManager(url=redis_connection, channel=redis_channel,
                                              redis_options=redis_options)
        self._client = SocketManager(app, location, 
                                     cors_allowed_origins=cors_allowed_origins,
                                     client_manager=self._manager)
        self._scope = {} # self._scope[room_name]["excluded_events"]
    
    async def send_event(self, event_name: str, 
                         data: BaseDTO | BaseResponse | RootModel | Any,
                         to: str | None = None, 
                         namespace: str | None = None, **additional_arguments):
        """
        ## Send Event

        Send event into room or specific client

        Args:
            event_name (str): Name of event
            data (BaseDTO | BaseResponse | RootModel | Any): Data which will be body of request
            to (str | None, optional): Client Session ID or name of the room. Defaults to None.
            namespace (str | None, optional): Name of the namespace. Defaults to None.
        """
        if isinstance(data, (BaseDTO, BaseResponse, RootModel)):
            data = data.model_dump()
        return await self._client.emit(event=event_name,
                                       data=data, to=to, 
                                       namespace=namespace, **additional_arguments)
    
    def receive_event(self, event_name: str,
                            handler: Callable[..., None | Awaitable[None]],
                            namespace: str | None):
        """
        ## Receive Event

        Args:
            event_name (str): Name of event
            handler (Callable[..., None  |  Awaitable[None]]): Callback function
            namespace (str | None): Name of a namespace
        """
        return self._client.on(event_name, handler, namespace)
    
    async def send_message(self, data: BaseDTO | BaseResponse | RootModel | Any,
                         to: str | None = None, 
                         namespace: str | None = None, **additional_arguments):
        """
        ## Send Message

        Args:
            data (BaseDTO | BaseResponse | RootModel | Any): _description_
            to (str | None, optional): _description_. Defaults to None.
            namespace (str | None, optional): _description_. Defaults to None.
        """
        if isinstance(data, (BaseDTO, BaseResponse, RootModel)):
            data = data.model_dump()

        return await self._client.send(data=data, to=to, namespace=namespace)
    
    async def broadcast(self, data: BaseDTO | BaseResponse | RootModel | Any,
                        event_name: str = "broadcast",
                        skip_sid: str | None = None, 
                        exclude_rooms: list[str] = [],
                        namespaces: list[str] = ["/"]):
        for namespace in namespaces:
            if not (rooms := self._client._sio.manager.rooms.get(namespace, None)):
                continue

            for room_name in rooms.keys():
                if room_name in exclude_rooms:
                    continue

                await self.send_event(event_name, data, room_name, namespace,
                                      skip_sid=skip_sid)
    
    async def send_r2r(self, event_name: str,
                       data: BaseDTO | BaseResponse | RootModel | Any,
                       to: str | None = None, 
                       namespace: str | None = None, timeout: int = 60, 
                       **additional_arguments):
        """
        ## Send Request-to-Response

        Sends request that should return response just like it made in HTTP but allows to prefore lifetime API request-to-response method.
        Where server or client sends request and awaits response to this request from client, if not provided then timeout works out and raises `TimeoutError`
        """
        if isinstance(data, (BaseDTO, BaseResponse, RootModel)):
            data = data.model_dump()

        return await self._client.call(event=event_name,
                                data=data, to=to,
                                namespace=namespace,
                                timeout=timeout)
    
    async def subscribe(self, sid: str, room_name: str, 
                        namespace: str | None = None, 
                        exclude_events: list[str] = []):
        self._scope[room_name] = {"excluded_events": exclude_events}
        return await self._client.enter_room(sid, room_name, namespace)
    
    async def unsubscribe(self, sid: str, room_name: str,
                          namespace: str | None = None):
        del self._scope[room_name]
        return await self._client.leave_room(sid, room_name, namespace)
    
    async def disconnect(self, sid: str, namespace: str | None = None):
        return await self._client.disconnect(sid, namespace)