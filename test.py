from fastapi import FastAPI, HTTPException, Request, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

flights_db = [
    {"id": 1, "flight_number": "VN-213", "destination": "Da Nang", "available_seats": 45, "status": "scheduled", "created_at": "2026-07-01T06:00:00Z"},
    {"id": 2, "flight_number": "VJ-122", "destination": "Phu Quoc", "available_seats": 12, "status": "scheduled", "created_at": "2026-07-01T07:30:00Z"}
]

app = FastAPI()

class err(BaseModel): 
    statusCode: int
    message: str
    data: Optional[Any]
    error: Optional[Any]
    timestamp: datetime
    path: str
    
def make_response(status_code: int, message: str, data: Any, error: Optional[str], path: str):
    body = err(
        statusCode=status_code,
        message=message,
        data=data,
        error=error,
        timestamp=datetime.utcnow(),          
        path=path
    )
    return JSONResponse(status_code=status_code, content=body.dict())

  
class flight(BaseModel):
    id:int
    flight_number: str
    destination: str 
    available_seats: int
    status: str
    created_at: datetime    

class FlightCreate(BaseModel):
    flight_number: str = Field(min_length=5, max_length=10)
    destination: str = Field(min_length=1)
    available_seats: int = Field(ge=1)
    
    
@app.get("/flights", response_model=err)
def get_flights(request: Request, status: Optional[str] = Query(default=None)):
    data = [f for f in flights_db] if status is None else [f for f in flights_db if f["status"] == status]
    return make_response(200, "Lấy danh sách chuyến bay thành công!", data, None, request.url.path)


@app.post("/flights", response_model=err, status_code=201)
def create_flight(request: Request, payload: FlightCreate):
    for f in flights_db:
        if f["flight_number"] == payload.flight_number:
            raise HTTPException( status_code=400,
                detail={
                    "message": "Lỗi: Số hiệu chuyến bay này đã tồn tại trên hệ thống điều hành!",
                    "error": "ERR-AIR-01: Flight number conflict in current active schedule database."
                }
            )
    new_id = max(f["id"] for f in flights_db) + 1 if flights_db else 1
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    new_flight = {
        "id": new_id,
        "flight_number": payload.flight_number,
        "destination": payload.destination,
        "available_seats": payload.available_seats,
        "status": "scheduled",
        "created_at": now
    }
    flights_db.append(new_flight)   
    return make_response(201, "Khởi tạo chuyến bay mới thành công!", new_flight, None, request.url.path)


@app.delete("/flights/{flight_id}", response_model=err)
async def delete_flight(request: Request, flight_id: int = Path(..., ge=1)):
    idx = next((i for i, f in enumerate(flights_db) if f["id"] == flight_id), None)
    if idx is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Lỗi: Không tìm thấy mã chuyến bay yêu cầu để hủy!",
                "error": "ERR-AIR-02: Target flight ID is missing from system scope."
            }
        )
    flights_db.pop(idx)
    return make_response(200, "Hủy chuyến bay thành công!", None, None, request.url.path)





    