from typing import Generic, TypeVar, List
from pydantic import BaseModel

DataT = TypeVar('DataT')

class ResponseModel(BaseModel, Generic[DataT]):
    data: DataT
    message: str

class ListResponseModel(BaseModel, Generic[DataT]):
    data: List[DataT]
    message: str 