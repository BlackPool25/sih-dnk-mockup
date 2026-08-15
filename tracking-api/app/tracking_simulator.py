from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app import models
from app.cache import invalidate_shipment_cache
from app.providers import get_provider

def advance_shipments():
    provider = get_provider()
    db = SessionLocal()
    try:
        shipments = db.query(models.Shipment).filter(models.Shipment.status != "Delivered").all()
        for shipment in shipments:
            next_step = provider.get_next_status(shipment.status)
            if next_step is None:
                continue
            new_event = models.TrackingEvent(
                shipment_id=shipment.id,
                status=next_step["status"],
                location=next_step["location"]
            )
            db.add(new_event)
            shipment.status = next_step["status"]
            invalidate_shipment_cache(shipment.tracking_number)
            print(f"[SIMULATOR] {shipment.tracking_number} -> {next_step['status']} ({next_step['location']})")
        db.commit()
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(advance_shipments, "interval", seconds=15)
    scheduler.start()
    return scheduler