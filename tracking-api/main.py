from collections.abc import Iterator
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.cache import (
    get_cached_shipment,
    invalidate_shipment_cache,
    set_cached_shipment,
)
from app.database import SessionLocal
from app.providers import get_provider
from app.tracking_simulator import start_scheduler

app = FastAPI(title="tracking-api", version="0.1.0")

start_scheduler()


def get_db() -> Iterator[Session]:
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
    order_id: Optional[str] = None
    parcel_id: Optional[str] = None


class EventRequest(BaseModel):
    status: str
    location: Optional[str] = None


@app.post("/shipments")
def register_shipment(shipment: ShipmentRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    existing = db.query(models.Shipment).filter_by(tracking_number=shipment.tracking_number).first()
    if existing:
        has_linkage = (
            shipment.order_id is not None
            or shipment.parcel_id is not None
            or existing.order_id is not None
            or existing.parcel_id is not None
        )
        if has_linkage and existing.order_id == shipment.order_id and existing.parcel_id == shipment.parcel_id:
            return jsonable_encoder(existing)
        raise HTTPException(status_code=400, detail="Shipment already registered")

    provider = get_provider()
    provider.register(shipment.tracking_number, shipment.carrier)

    new_shipment = models.Shipment(
        tracking_number=shipment.tracking_number,
        carrier=shipment.carrier,
        order_id=shipment.order_id,
        parcel_id=shipment.parcel_id,
    )
    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)
    return jsonable_encoder(new_shipment)


@app.get("/shipments")
def list_shipments(
    order_id: Optional[str] = Query(None),
    parcel_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    q = db.query(models.Shipment)
    if order_id is not None:
        q = q.filter(models.Shipment.order_id == order_id)
    if parcel_id is not None:
        q = q.filter(models.Shipment.parcel_id == parcel_id)
    shipments = q.order_by(models.Shipment.id).all()
    return jsonable_encoder(shipments)


@app.get("/orders/{order_id}/shipments")
def list_order_shipments(order_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    shipments = (
        db.query(models.Shipment).filter(models.Shipment.order_id == order_id).order_by(models.Shipment.id).all()
    )
    return {"order_id": order_id, "shipments": jsonable_encoder(shipments)}


@app.get("/shipments/{tracking_number}")
def get_shipment(tracking_number: str, db: Session = Depends(get_db)) -> dict[str, object]:
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
def add_event(tracking_number: str, event: EventRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    shipment = db.query(models.Shipment).filter_by(tracking_number=tracking_number).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    new_event = models.TrackingEvent(
        shipment_id=shipment.id,
        status=event.status,
        location=event.location,
    )
    db.add(new_event)
    shipment.status = event.status
    db.commit()
    db.refresh(new_event)
    invalidate_shipment_cache(tracking_number)
    return jsonable_encoder(new_event)


@app.get("/shipments/{tracking_number}/events")
def get_events(tracking_number: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    shipment = db.query(models.Shipment).filter_by(tracking_number=tracking_number).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return jsonable_encoder(shipment.events)