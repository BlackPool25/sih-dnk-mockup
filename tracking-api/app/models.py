from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True)
    carrier = Column(String)
    status = Column(String, default="Booked")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    events = relationship("TrackingEvent", back_populates="shipment", order_by="TrackingEvent.timestamp")


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    status = Column(String)
    location = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    shipment = relationship("Shipment", back_populates="events")