from logging import Logger, getLogger
from typing import Any, Awaitable, Callable

from fastapi.params import Depends
from plugins.liveapi.context import SIOContext
from plugins.liveapi.engines.socketio import SocketIOEngine
from plugins.liveapi.listener import Listener


class SIOHandler:
    def __init__(
            self, engine: SocketIOEngine,
            listeners: list[Listener] = [],
            logger: Logger = getLogger("ascender-plugins")
        ) -> None:
        self.engine = engine
        self.listeners = listeners
        self.logger = logger
    
    def add_listener(
            self, 
            listener: Callable[..., Awaitable[Any | None]],
            event_name: str, 
            dependencies: list[Depends] = [],
            namespace: str | None = None
        ) -> None:
        self.logger.debug(f"([purple]{namespace}[/purple]) Successfully initialized [cyan]{event_name}[/cyan] event-listener")
        self.listeners.append(Listener(event_name, listener, dependencies, f"/{namespace}"))
    
    def run_listener(self, listener: Listener):
        self.engine.receive_event(listener.event_name,
                                  listener.__call__, listener.namespace)
    
    def run_listeners(self):
        for listener in self.listeners:
            self.run_listener(listener)