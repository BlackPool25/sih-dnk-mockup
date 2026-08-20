import threading

from apscheduler.schedulers.background import BackgroundScheduler

from app.cache import invalidate_shipment_cache
from app.database import SessionLocal
from app import models
from app.providers import get_provider
from app.providers.mock_provider import STATE_FLOW

TERMINAL_STATUS = STATE_FLOW[-1]

_ADVANCE_LOCK = threading.Lock()


def advance_shipments() -> None:
    # Idempotence on concurrent ticks: skip if another advance is in flight.
    if not _ADVANCE_LOCK.acquire(blocking=False):
        return
    provider = get_provider()
    db = SessionLocal()
    try:
        shipments = db.query(models.Shipment).filter(models.Shipment.status != TERMINAL_STATUS).all()
        for shipment in shipments:
            next_step = provider.get_latest_status(shipment.tracking_number, shipment.status)
            if next_step is None:
                continue
            # monotonic single-step is guaranteed by MockProvider (exactly +1 in STATE_FLOW)
            # guard against duplicate event for same status (defensive)
            exists = (
                db.query(models.TrackingEvent)
                .filter(
                    models.TrackingEvent.shipment_id == shipment.id,
                    models.TrackingEvent.status == next_step["status"],
                )
                .first()
            )
            if exists is not None:
                continue
            new_event = models.TrackingEvent(
                shipment_id=shipment.id,
                status=next_step["status"],
                location=next_step["location"],
            )
            db.add(new_event)
            shipment.status = next_step["status"]
            invalidate_shipment_cache(shipment.tracking_number)
            print(f"[SIMULATOR] {shipment.tracking_number} -> {next_step['status']} ({next_step['location']})")
        db.commit()
    finally:
        try:
            db.close()
        finally:
            _ADVANCE_LOCK.release()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(advance_shipments, "interval", seconds=5)
    scheduler.start()
    return scheduler
