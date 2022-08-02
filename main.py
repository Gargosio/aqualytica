import uvicorn   #####comment when deployed
from fastapi import Depends, FastAPI, HTTPException, status,Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import motor.motor_asyncio
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import date, datetime, time, timedelta

# import os
# from fastapi import FastAPI, Body, HTTPException, status
# from fastapi.responses import JSONResponse
# from fastapi.encoders import jsonable_encoder
# from pydantic import BaseModel, Field, EmailStrcd
# from bson import ObjectId
# from typing import Optional, List
# import motor.motor_asyncio

app = FastAPI()
security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "IOTuser")
    correct_password = secrets.compare_digest(credentials.password, "iot_user@20220406")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

CONNECTION_STRING = "mongodb+srv://toloo:Godocholoo@cluster0.idj1r.mongodb.net/test"
client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING)
dbname = client.iotdatadb
# collection_name = dbname.get_collection("iotdatacoll")
# db = client.college


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class SensorModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    device: str = Field(...)
    timestamp: datetime = Field(...)
    Messagetype: float = Field(...)
    Level: float = Field(...)
    Battery: int = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "device": "devicea",
                "timestamp": "2032-04-23T10:20:30.400+02:30",
                "Messagetype": "56.3",
                "Level": "32.0",
                "Battery": "34.9",
            }
        }


class UpdateSensorModel(BaseModel):
    device: Optional[str]
    timestamp: Optional[datetime]
    Messagetype: Optional[float]
    Level: Optional[float]
    Battery: Optional[int]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "device": "devicea",
                "timestamp": "2032-04-23T10:20:30.400+02:30",
                "Messagetype": "56.3",
                "Level": "32.0",
                "Battery": "34.9",
            }
        }


@app.get(
    "/getsensordata", response_description="List all data", response_model=List[SensorModel]
)
async def RetrieveAll(username= Depends(get_current_username)):
    data = await dbname["iotwaterapi"].find().to_list(1000)
    return data

@app.post("/postsensordata", response_description="Add new data", response_model=SensorModel
          )
async def PostData(data: SensorModel = Body(...),username= Depends(get_current_username)):
    data = jsonable_encoder(data)
    new_data = await dbname["iotwaterapi"].insert_one(data)
    created_data = await dbname["iotwaterapi"].find_one({"_id": new_data.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_data)

# if __name__ == "__main__":
#     uvicorn.run("mongoapi:app", host="127.0.0.1", port=8000, reload=True)
