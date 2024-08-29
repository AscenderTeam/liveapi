from inspect import Parameter
from typing import Any

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from plugins.liveapi.types.authorization import SIOAuthorization
from ..base import ValidationStrategy


class AuthorizationValidationStrategy(ValidationStrategy):
    def validate(self, param: Parameter, data: dict[str, Any]) -> HTTPAuthorizationCredentials:
        if not (_authcreds := data.get("HTTP_AUTHORIZATION", None)):
            raise HTTPException(401, "Not authenticated")
        
        scheme, token = _authcreds.split()
        return SIOAuthorization(scheme=scheme, credentials=token)