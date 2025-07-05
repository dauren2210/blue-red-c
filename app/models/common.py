from bson import ObjectId
from pydantic import BaseModel
from pydantic.json_schema import JsonSchemaValue, GetJsonSchemaHandler
from pydantic_core import core_schema

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: core_schema.ValidationInfo):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string"}


class MongoBaseModel(BaseModel):
    id: PyObjectId = None

    class Config:
        json_encoders = {
            ObjectId: str
        }
        arbitrary_types_allowed = True 