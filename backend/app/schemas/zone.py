from pydantic import BaseModel


class ZoneCreate(BaseModel):
    name: str
    risk_level: str = "medium"
    polygon: list[list[float]]  # [[lat, lng], ...]
    crime_index: float = 30.0
    description: str = ""


class ZoneOut(BaseModel):
    id: int
    name: str
    risk_level: str
    polygon: list[list[float]]
    crime_index: float
    description: str
    source: str

    class Config:
        from_attributes = True
