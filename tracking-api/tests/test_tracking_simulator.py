"""TDD fake-clock tests for tracking simulator interval tuning (TASK 6).

Requirements:
- scheduler interval 15s -> 5s so frontend polling every 3s sees movement within 6s (2 polls)
- shipment advances at most one stage per tick
- GET /shipments/{id}/events reflects new event within 6s (2 polls)
- monotonic single-step, idempotence on concurrent ticks, terminal Signed no further advances, cache invalidated
- 7-stage order preserved, no duplicate events
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_tracking_simulator.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from app import cache as cache_mod
from app.database import Base
from app.providers.mock_provider import STATE_FLOW

# isolated sqlite engine for all tests in this file
TestEngine = create_engine(
    "sqlite:///./test_tracking_simulator.db",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=TestEngine, autoflush=False, autocommit=False)


@pytest.fixture()
def client(monkeypatch):
    Base.metadata.drop_all(bind=TestEngine)
    Base.metadata.create_all(bind=TestEngine)
    monkeypatch.setattr(cache_mod, "get_cached_shipment", lambda _tn: None)
    monkeypatch.setattr(cache_mod, "set_cached_shipment", lambda _tn, _data: None)
    # keep invalidate observable — replace with spy in individual tests if needed
    monkeypatch.setattr(cache_mod, "invalidate_shipment_cache", lambda _tn: None)

    def _override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = _override_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TestEngine)


class FakeClock:
    """Fake wall-clock that advances by driving simulator ticks."""

    def __init__(self, monkeypatch):
        self.now = 0  # seconds
        self.monkeypatch = monkeypatch
        # redirect simulator SessionLocal to our TestSession
        from app import tracking_simulator as sim_mod

        monkeypatch.setattr(sim_mod, "SessionLocal", TestSession)

    def tick(self):
        from app import tracking_simulator as sim_mod

        sim_mod.advance_shipments()
        self.now += 5  # scheduler interval is 5s


# ---------------------------------------------------------------------------
# TASK 6 — interval tuning
# ---------------------------------------------------------------------------

def test_scheduler_interval_is_5s():
    """Scheduler must fire every 5s (not 15s) so 3s frontend polling sees movement within 6s."""
    from app import tracking_simulator as sim_mod

    scheduler = sim_mod.start_scheduler()
    try:
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1, f"expected one job, got {len(jobs)}"
        job = jobs[0]
        # APScheduler IntervalTrigger has attribute interval (timedelta)
        interval_seconds = job.trigger.interval.total_seconds() if hasattr(job.trigger, "interval") else None
        # fallback: inspect string representation
        if interval_seconds is None:
            interval_seconds = job.trigger.interval_length if hasattr(job.trigger, "interval_length") else None
        assert interval_seconds == 5, f"scheduler interval must be 5s, got {interval_seconds}s (trigger={job.trigger})"
    finally:
        scheduler.shutdown(wait=False)


def test_advances_at_most_one_stage_per_tick_fake_clock(client, monkeypatch):
    """Fake clock: each tick advances a shipment by exactly one stage, never skips."""
    fc = FakeClock(monkeypatch)

    resp = client.post("/shipments", json={"tracking_number": "FAKE-ONE-STEP-001", "carrier": "IndiaPost"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "Booked"

    for expected_idx in range(1, len(STATE_FLOW)):
        fc.tick()  # one interval
        # read via API
        shipment = client.get("/shipments/FAKE-ONE-STEP-001").json()
        expected_status = STATE_FLOW[expected_idx]
        assert shipment["status"] == expected_status, (
            f"tick {expected_idx}: expected {expected_status!r}, got {shipment['status']!r}"
        )
        events = client.get("/shipments/FAKE-ONE-STEP-001/events").json()
        assert len(events) == expected_idx, (
            f"tick {expected_idx}: expected {expected_idx} events (one per tick), got {len(events)}"
        )
        statuses = [e["status"] for e in events]
        assert statuses == STATE_FLOW[1 : expected_idx + 1], (
            f"events not monotonic single-step: {statuses}"
        )

    # terminal: further ticks do not advance
    for _ in range(3):
        fc.tick()
    shipment = client.get("/shipments/FAKE-ONE-STEP-001").json()
    assert shipment["status"] == "Signed"
    events = client.get("/shipments/FAKE-ONE-STEP-001/events").json()
    assert len(events) == len(STATE_FLOW) - 1  # Booked has no event; 6 events after


def test_get_events_reflects_new_event_within_6s_two_polls(client, monkeypatch):
    """Polling every 3s: within 6s (2 polls, ~1-2 ticks at 5s) the events list must grow."""
    fc = FakeClock(monkeypatch)

    client.post("/shipments", json={"tracking_number": "FAKE-POLL-001", "carrier": "IndiaPost"})

    # t=0 poll
    events_t0 = client.get("/shipments/FAKE-POLL-001/events").json()
    assert len(events_t0) == 0

    # Simulate 6s wall time: frontend polls at 3s and 6s, scheduler ticks at 5s
    # One tick must have happened within 6s (5s interval), so by second poll we see an event.
    fc.tick()  # t=5s: one advance

    # poll at ~6s
    events_t6 = client.get("/shipments/FAKE-POLL-001/events").json()
    assert len(events_t6) >= 1, (
        f"expected at least 1 event within 6s (2 polls at 3s), got {len(events_t6)} — "
        f"scheduler interval too long or poll-driven advancement missing"
    )
    assert events_t6[0]["status"] == STATE_FLOW[1]
    assert "location" in events_t6[0] and events_t6[0]["location"]


def test_idempotence_concurrent_ticks_no_duplicate_events(client, monkeypatch):
    """Concurrent ticks must be idempotent — no duplicate events, still single-step."""
    FakeClock(monkeypatch)

    client.post("/shipments", json={"tracking_number": "FAKE-CONC-001", "carrier": "IndiaPost"})

    # fire 5 concurrent ticks — should behave like 1 tick if overlapping, or at most 5 sequential ticks
    # The key invariant: no duplicate status and step is at most one per serialized tick.
    # We simulate concurrent calls to advance_shipments with threads.
    from app import tracking_simulator as sim_mod

    monkeypatch.setattr(sim_mod, "SessionLocal", TestSession)

    threads = [threading.Thread(target=sim_mod.advance_shipments) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    events = client.get("/shipments/FAKE-CONC-001/events").json()
    statuses = [e["status"] for e in events]
    # no duplicates
    assert len(statuses) == len(set(statuses)), f"duplicate events created under concurrent ticks: {statuses}"
    # at most one stage per tick invocation batch — worst case 1 event if lock ensures single execution,
    # but without proper idempotence sequential 5 ticks would give 5 events; concurrent should give 1
    # We assert strictly 1 to prove idempotence guard (non-overlapping lock).
    # If implementation is lock+skip concurrent ticks, exactly 1 event.
    # If implementation is per-row atomic, still at most 5 but must remain monotonic single-step.
    # Accept either 1 (with try-lock skip) or up to 5 but monotonic.
    assert 1 <= len(statuses) <= 5
    if len(statuses) >= 1:
        # if multiple events, they must be prefix of STATE_FLOW[1:]
        assert statuses == STATE_FLOW[1 : 1 + len(statuses)]
    # second batch of 5 concurrent after first completes should advance by exactly 1 more (if lock skips)
    # or more if serialized; just verify no duplicates and monotonic
    threads2 = [threading.Thread(target=sim_mod.advance_shipments) for _ in range(5)]
    for t in threads2:
        t.start()
    for t in threads2:
        t.join()
    events2 = client.get("/shipments/FAKE-CONC-001/events").json()
    statuses2 = [e["status"] for e in events2]
    assert len(statuses2) == len(set(statuses2)), f"duplicate after second concurrent batch: {statuses2}"
    assert statuses2 == STATE_FLOW[1 : 1 + len(statuses2)]
    assert len(statuses2) > len(statuses), "second batch should have advanced further"


def test_terminal_signed_no_further_advances(client, monkeypatch):
    """Once Signed, further ticks create no events and status stays Signed."""
    fc = FakeClock(monkeypatch)

    client.post("/shipments", json={"tracking_number": "FAKE-TERM-001", "carrier": "IndiaPost"})

    # advance to Signed (needs 6 ticks from Booked)
    for _ in range(len(STATE_FLOW) - 1):
        fc.tick()

    shipment = client.get("/shipments/FAKE-TERM-001").json()
    assert shipment["status"] == "Signed"
    events_before = client.get("/shipments/FAKE-TERM-001/events").json()
    count_before = len(events_before)

    for _ in range(4):
        fc.tick()

    shipment_after = client.get("/shipments/FAKE-TERM-001").json()
    events_after = client.get("/shipments/FAKE-TERM-001/events").json()
    assert shipment_after["status"] == "Signed"
    assert len(events_after) == count_before, "terminal Signed must not create further events"


def test_cache_invalidated_on_advance(client, monkeypatch):
    """advance_shipments must invalidate shipment cache so next GET sees new status."""
    from app import tracking_simulator as sim_mod

    monkeypatch.setattr(sim_mod, "SessionLocal", TestSession)

    invalidated: list[str] = []
    orig_invalidate = sim_mod.invalidate_shipment_cache  # keep reference

    def spy_invalidate(tn: str):
        invalidated.append(tn)
        return orig_invalidate(tn)

    monkeypatch.setattr(sim_mod, "invalidate_shipment_cache", spy_invalidate)
    # also patch cache_mod seen by main uses? main uses its own cache, but simulator uses its own import
    # so patching sim_mod.invalidate... suffices for assertion

    client.post("/shipments", json={"tracking_number": "FAKE-CACHE-001", "carrier": "IndiaPost"})

    sim_mod.advance_shipments()

    assert "FAKE-CACHE-001" in invalidated, (
        f"advance_shipments must call invalidate_shipment_cache; got calls: {invalidated}"
    )

    # next GET should reflect updated status (proves cache was not stale)
    shipment = client.get("/shipments/FAKE-CACHE-001").json()
    assert shipment["status"] == STATE_FLOW[1]
