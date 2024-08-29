from typing import Any, TypeVar

from pydantic import PydanticUserError, TypeAdapter

T = TypeVar("T")

def isvalid(type_to_check: type, value: T) -> bool:
    try:
        type_adapter = TypeAdapter(type_to_check,
                                config={"arbitrary_types_allowed": True})
    except PydanticUserError:
        type_adapter = TypeAdapter(type_to_check)
    
    try:
        type_adapter.validate_python(value)
        return True
    
    except Exception as e:
        return False

def isvalid_json(type_to_check: type, value: T) -> bool:
    try:
        type_adapter = TypeAdapter(type_to_check,
                                config={"arbitrary_types_allowed": True})
    except PydanticUserError:
        type_adapter = TypeAdapter(type_to_check)
    
    try:
        type_adapter.validate_json(value)
        return True
    
    except Exception as e:
        return False
