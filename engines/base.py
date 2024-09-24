from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable
from fastapi_socketio import SocketManager

from core.optionals import BaseDTO, BaseResponse
from pydantic import RootModel


class BaseEngine(ABC):
    _client: SocketManager
    _manager: Any | None = None
    _scope: dict[str, dict[str, Any]] | dict[str, Any]

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def broadcast(self, data: BaseDTO | BaseResponse | RootModel | Any,
                        event_name: str = "broadcast",
                        skip_sid: str | None = None, 
                        exclude_rooms: list[str] = [],
                        namespaces: list[str] = ["/"]):
        """
        ## Broadcast

        Broadcast some event to every single connection.
        Sends to all connected clients the event data you wish.
        """
        ...
    
    @abstractmethod
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
        ...
    
    @abstractmethod
    async def subscribe(self, sid: str, room_name: str, 
                        namespace: str | None = None, 
                        exclude_events: list[str] = []):
        """
        ## Subscribe

        Subscribes current client given in `sid` connection to specific room name given in `room_name` argument.
        """
        ...

    @abstractmethod
    async def unsubscribe(self, sid: str, room_name: str,
                          namespace: str | None = None):
        """
        ## Unsubscribe

        Retracts the subscription of current client given in `sid` from specific room given by `room_name` arguments
        """
        ...
    
    @abstractmethod
    async def disconnect(self, sid: str, namespace: str | None = None):
        """
        ## Disconnect

        Disconnects specific client given in `sid` and terminates it's connection from this socket-io server
        """
        ...