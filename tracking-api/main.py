from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

from app.database import engine, SessionLocal, Base
from app import models
from app.cache import get_cached_shipment, set_cached_shipment, invalidate_shipment_cache
from app.tracking_simulator import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="tracking-api", version="0.1.0")

start_scheduler()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

class ShipmentRequest(BaseModel):
    tracking_number: str
    carrier: str

class EventRequest(BaseModel):
    status: str
    location: Optional[str] = None

@app.post("/shipments")
def register_shipment(shipment: ShipmentRequest, db: Session = Depends(get_db)):
    existing = db.query(models.Shipment).filter_by(tracking_number=shipment.tracking_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Shipment already registered")
    new_shipment = models.Shipment(tracking_number=shipment.tracking_number, carrier=shipment.carrier)
    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)
    return new_shipment

@app.get("/shipments/{tracking_number}")
def get_shipment(tracking_number: str, db: Session = Depends(get_db)):
    cached = get_cached_shipment(tracking_number)
    if cached:
        return cached
    shipment = db.query(models.Shipment).filter_by(tracking_number=tracking_number).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    result = jsonable_encoder(shipment)
    set_cached_shipment(tracking_number, result)
    return result

@app.post("/shipments/{tracking_number}/events")
def add_event(tracking_number: str, event: EventRequest, db: Session = Depends(get_db)):
    shipment = db.query(models.Shipment).filter_by(tracking_number=tracking_number).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_event = models.TrackingEvent(
        shipment_id=shipment.id,
        status=event.status,
        location=event.location
    )
    db.add(new_event)
    shipment.status = event.status
    db.commit()
    db.refresh(new_event)
    invalidate_shipment_cache(tracking_number)
    return new_event

@app.get("/shipments/{tracking_number}/events")
def get_events(tracking_number: str, db: Session = Depends(get_db)):
    shipment = db.query(models.Shipment).filter_by(tracking_number=tracking_number).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment.events