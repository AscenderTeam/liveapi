from pydantic import BaseModel


class SIOAuthorization(BaseModel):
    credentials: str
    scheme: str