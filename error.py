from json import JSONDecodeError
from logging import Logger, getLogger
from fastapi import HTTPException
from pydantic import ValidationError
from plugins.liveapi.context import SIOContext


class ErrorHandler:
    def __init__(self, logger: Logger = getLogger("ascender-plugins"),
                 event_name: str = "error") -> None:
        self.logger = logger
        self.event_name = event_name

    async def __call__(self, ctx: SIOContext,
                       current_event: str,
                       exception: HTTPException | ValidationError | JSONDecodeError | Exception):
        if current_event == "connect":
            await ctx.reject_client()

        self.logger.error(f"([purple]{ctx.namespace}[/purple]) failed to process event message {exception}")
        if isinstance(exception, HTTPException):
            await ctx.reply(self.event_name,
                            {"status_code": exception.status_code, "detail": exception.detail})
        
        elif isinstance(exception, ValidationError):
            await ctx.reply(self.event_name, {"status_code": 422, "detail": exception.errors()})
        
        elif isinstance(exception, JSONDecodeError):
            await ctx.reply(self.event_name,
                            {"status_code": 422, "detail": f"JSON Serializer Error: {exception}"})
        
        else:
            await ctx.reply(self.event_name,
                            {"status_code": 500, "detail": "Internal Server Error"})