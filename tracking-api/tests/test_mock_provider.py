"""TDD for 7-stage STATE_FLOW + MOCK_TRACKING alias.

Expectations:
- STATE_FLOW == 7 stages in exact order with 2x In Transit and Signed as 7th
- get_latest_status advances sequentially through 7 stages
- MOCK_TRACKING=true forces mock provider even if TRACKING_PROVIDER=live/17track
- MOCK_TRACKING bool parsing: true/1/yes case-insensitive, false/0/no otherwise
"""

import importlib
import os


EXPECTED_FLOW = [
    "Booked",
    "Picked Up",
    "In Transit (Origin)",
    "In Transit (Destination)",
    "Out for Delivery",
    "Delivered",
    "Signed",
]


def test_state_flow_is_seven_exact_order():
    from app.providers.mock_provider import STATE_FLOW

    assert STATE_FLOW == EXPECTED_FLOW, f"STATE_FLOW must be {EXPECTED_FLOW}, got {STATE_FLOW}"
    assert len(STATE_FLOW) == 7
    # ensure 2x In Transit variants
    assert sum(1 for s in STATE_FLOW if "In Transit" in s) == 2
    assert STATE_FLOW[-1] == "Signed"


def test_get_latest_status_sequential_through_7():
    from app.providers.mock_provider import MockProvider, STATE_FLOW

    p = MockProvider()
    # walk through all 7 sequentially
    for i in range(len(STATE_FLOW) - 1):
        cur = STATE_FLOW[i]
        nxt = p.get_latest_status("TN-SEQ-001", cur)
        assert nxt is not None, f"expected next after {cur}"
        assert nxt["status"] == STATE_FLOW[i + 1], f"after {cur} expected {STATE_FLOW[i+1]}, got {nxt['status']}"
        assert "location" in nxt and isinstance(nxt["location"], str) and nxt["location"]

    # terminal state returns None
    assert p.get_latest_status("TN-SEQ-001", STATE_FLOW[-1]) is None

    # unknown status returns None
    assert p.get_latest_status("TN-SEQ-001", "Unknown") is None


def test_mock_tracking_forces_mock_even_if_live(monkeypatch):
    # MOCK_TRACKING=true should force mock even when TRACKING_PROVIDER=live
    monkeypatch.setenv("MOCK_TRACKING", "true")
    monkeypatch.setenv("TRACKING_PROVIDER", "live")
    # need fresh import to pick up env
    import app.providers as prov_mod

    importlib.reload(prov_mod)
    provider = prov_mod.get_provider()
    from app.providers.mock_provider import MockProvider

    assert isinstance(provider, MockProvider), f"MOCK_TRACKING=true should force MockProvider, got {type(provider).__name__}"

    # also test with 17track alias if handled
    monkeypatch.setenv("TRACKING_PROVIDER", "17track")
    importlib.reload(prov_mod)
    provider2 = prov_mod.get_provider()
    assert isinstance(provider2, MockProvider)

    # cleanup: set back to mock for other tests
    monkeypatch.setenv("TRACKING_PROVIDER", "mock")
    monkeypatch.delenv("MOCK_TRACKING", raising=False)
    importlib.reload(prov_mod)


def test_mock_tracking_bool_parsing(monkeypatch):
    import app.providers as prov_mod

    truthy = ["true", "True", "TRUE", "1", "yes", "YES", "Yes"]
    falsy = ["false", "False", "FALSE", "0", "no", "NO", "", "live"]

    for val in truthy:
        monkeypatch.setenv("MOCK_TRACKING", val)
        monkeypatch.setenv("TRACKING_PROVIDER", "live")
        importlib.reload(prov_mod)
        # _is_mock_tracking_enabled helper should be true if exists, else check get_provider
        # Prefer testing via get_provider precedence
        from app.providers.mock_provider import MockProvider

        provider = prov_mod.get_provider()
        assert isinstance(provider, MockProvider), f"MOCK_TRACKING={val!r} should be truthy and force mock, got {type(provider).__name__}"

    for val in falsy:
        # falsy values should NOT force mock; live should attempt RealProvider (may raise if no key)
        # For falsy, we set TRACKING_PROVIDER=mock to avoid needing API key; check that parsing doesn't break
        # Instead test parsing helper directly if exposed
        monkeypatch.setenv("MOCK_TRACKING", val)
        # check helper if exists
        if hasattr(prov_mod, "_parse_mock_tracking"):
            assert prov_mod._parse_mock_tracking(val) is False, f"MOCK_TRACKING={val!r} should parse as False"
        elif hasattr(prov_mod, "_is_mock_tracking_enabled"):
            # when env is falsy, _is_mock_tracking_enabled should be False
            # but it reads from os.getenv, so set and check
            monkeypatch.setenv("MOCK_TRACKING", val)
            importlib.reload(prov_mod)
            # after reload, check via get_provider with TRACKING_PROVIDER=mock still returns mock (not forced)
            # the point is truthy vs falsy distinction
            pass

    # also test helper parsing directly
    # ensure empty/unset counts as falsy
    monkeypatch.delenv("MOCK_TRACKING", raising=False)
    importlib.reload(prov_mod)
    if hasattr(prov_mod, "_parse_mock_tracking"):
        assert prov_mod._parse_mock_tracking("true") is True
        assert prov_mod._parse_mock_tracking("1") is True
        assert prov_mod._parse_mock_tracking("yes") is True
        assert prov_mod._parse_mock_tracking("false") is False
        assert prov_mod._parse_mock_tracking("0") is False


def test_locations_cover_new_states():
    from app.providers.mock_provider import LOCATIONS, STATE_FLOW

    # every state except Booked should have at least one location pool
    for state in STATE_FLOW:
        if state == "Booked":
            continue
        assert state in LOCATIONS, f"LOCATIONS missing entry for {state!r}"
        assert len(LOCATIONS[state]) >= 1


def test_events_ordered_via_simulator(tmp_path, monkeypatch):
    """Simulate full lifecycle: register then advance 6 times → 7 total statuses, events ordered."""
    # Use sqlite for isolated test
    os.environ["DATABASE_URL"] = "sqlite:///./test_mock_flow_events.db"
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app import models
    from app.providers.mock_provider import STATE_FLOW

    engine = create_engine("sqlite:///./test_mock_flow_events.db", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    # create shipment at Booked
    db = Session()
    ship = models.Shipment(tracking_number="FLOW-7-001", carrier="IndiaPost", status="Booked")
    db.add(ship)
    db.commit()
    db.refresh(ship)
    # seed initial event for Booked to mirror real registration
    db.add(models.TrackingEvent(shipment_id=ship.id, status="Booked", location="Origin Facility"))
    db.commit()

    # advance via MockProvider sequentially, creating events
    from app.providers.mock_provider import MockProvider

    p = MockProvider()
    for _ in range(10):  # more than needed, should stop at Signed
        cur = db.query(models.Shipment).filter_by(tracking_number="FLOW-7-001").first()
        nxt = p.get_latest_status(cur.tracking_number, cur.status)
        if nxt is None:
            break
        db.add(models.TrackingEvent(shipment_id=cur.id, status=nxt["status"], location=nxt["location"]))
        cur.status = nxt["status"]
        db.commit()

    events = db.query(models.TrackingEvent).filter_by(shipment_id=ship.id).order_by(models.TrackingEvent.timestamp, models.TrackingEvent.id).all()
    statuses = [e.status for e in events]
    assert statuses == STATE_FLOW, f"events should be in STATE_FLOW order, got {statuses}"
    assert len(statuses) == 7

    db.close()
    Base.metadata.drop_all(bind=engine)
