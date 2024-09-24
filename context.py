from typing import Any, Iterable
from pydantic import RootModel
from core.optionals.base.dto import BaseDTO
from core.optionals.base.response import BaseResponse
from plugins.liveapi.engines.base import BaseEngine


class SIOContext:
    def __init__(self, engine: BaseEngine, namespace: str,
                 event_name: str, sid: str) -> None:
        self.engine = engine
        self.namespace = namespace
        self.event_name = event_name
        self.session_id = sid
    
    async def reply(self, event_name: str | None, 
                    data: BaseDTO | BaseResponse | RootModel | Any,
                    to: str | None = None, **additional_arguments):
        if to is None:
            to = self.session_id
        if event_name is None:
            event_name = self.event_name

        return await self.send_event(event_name,
                                        data, to, self.namespace, **additional_arguments)
    
    async def streaming_response(self, contents: Iterable[BaseDTO | BaseResponse | RootModel | Any],
                                 to: str | None = None, **additional_arguments):
        for content in contents:
            await self.reply(content, to, **additional_arguments)
    
    async def disconnect_client(self, sid: str, namespace: str | None = None):
        if namespace is None:
            namespace = self.namespace
        
        await self.engine.disconnect(sid, namespace)

    async def reject_client(self):
        return await self.disconnect_client(self.session_id, self.namespace)
    
    def session(
            self, 
            sid: int | None = None,
            namespace: str | None = None,
        ):
        if sid is None:
            sid = self.session_id
        
        if namespace is None:
            namespace = self.namespace

        return self.engine._client._sio.session(sid, namespace)

    @property
    def send_event(self):
        return self.engine.send_event
    
    @property
    def send_message(self):
        return self.engine.send_message
    
    @property
    def broadcast(self):
        return self.engine.broadcast
    
    @property
    def send_r2r(self):
        return self.engine.send_r2r
    
    async def subscribe(
            self, 
            room_name: str,
            sid: str | None = None,
            namespace: str | None = None,
            exclude_events: list[str] = []):
        if sid is None:
            sid = self.session_id
        if namespace is None:
            namespace = self.namespace

        return await self.engine.subscribe(
            room_name=room_name,
            sid=sid, namespace=namespace,
            exclude_events=exclude_events
        )
    
    @property
    def unsubscribe(self,
                    room_name: str,
                    sid: str | None = None,
                    namespace: str | None = None,):
        if sid is None:
            sid = self.session_id
        if namespace is None:
            namespace = self.namespace

        return self.engine.unsubscribe(
            room_name=room_name,
            sid=sid, namespace=namespace
        )