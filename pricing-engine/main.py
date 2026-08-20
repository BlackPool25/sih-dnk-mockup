from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.api_schemas import CostBreakdownResponse, LandedCostResponse, LegacyPricingRequest, ParcelResponse, PricingRequest, PricingResponse, ShipmentBreakdownResponse, TransitResponse
from app.optimization_models import LaneOption, OptimizationItem
from app.optimization_objectives import OptimizationMode
from app.optimization_service import OptimizationServiceError, optimize_order
from app.packaging import Package
from app.razorpay import PaymentCreateOrderRequest, PaymentCreateOrderResponse, PaymentLinkCreateRequest, PaymentLinkCreateResponse, PaymentLinkStatusResponse, PaymentVerifyRequest, PaymentVerifyResponse, RazorpayWebhookResponse, create_order, create_payment_link, get_payment_link_status, verify_payment, verify_webhook

app = FastAPI(title="SIH DNK Pricing Engine", version="0.1.0", description="Pricing and shipment optimization engine for ITPS and EMS.")


@app.get("/healthz", tags=["health"])
@app.get("/health", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"service": "pricing-engine", "status": "ok"}


@app.get("/payment-test", include_in_schema=False)
async def payment_test_page():
    return FileResponse(Path(__file__).with_name("payment_test.html"), media_type="text/html")


@app.post("/pricing", response_model=PricingResponse, status_code=status.HTTP_200_OK, tags=["pricing"])
async def calculate_pricing(request: PricingRequest) -> PricingResponse:
    try:
        if request.landed_cost is None:
            raise OptimizationServiceError("landed_cost inputs are required for POST /pricing")
        items = [OptimizationItem(item_id=i.item_id, quantity=i.quantity, unit_weight_g=i.unit_weight_g, splittable=i.splittable, length_cm=i.length_cm, width_cm=i.width_cm, height_cm=i.height_cm) for i in request.items]
        packages = [Package(package_id=p.package_id, name=p.name, tare_weight_g=p.tare_weight_g, length_cm=p.length_cm, width_cm=p.width_cm, height_cm=p.height_cm, cost_minor=p.cost_minor, max_product_weight_g=p.max_product_weight_g) for p in request.packages]
        lanes = [LaneOption(name=l.name, lane_data={"lane": l.lane, "first_slab_g": l.first_slab_g, "first_slab_rate_minor": l.first_slab_rate_minor, "addl_slab_g": l.addl_slab_g, "addl_slab_rate_minor": l.addl_slab_rate_minor, "weight_cap_g": l.weight_cap_g, "volume_free": l.volume_free, "divisor": l.divisor, "transit_min_days": l.transit_min_days, "transit_max_days": l.transit_max_days, "provenance": l.provenance}) for l in request.lanes]
        result = optimize_order(items=items, packages=packages, lanes=lanes, optimization_mode=OptimizationMode(request.optimization_mode), max_parcels=request.max_parcels, landed_cost=request.landed_cost.model_dump())
        return PricingResponse(status=result["status"], optimization_mode=result["optimization_mode"], shipment=ShipmentBreakdownResponse(**result["shipment"]), cost=CostBreakdownResponse(**result["cost"]), lane_breakdown=result["lane_breakdown"], estimated_transit=TransitResponse(**result["estimated_transit"]), parcels=[ParcelResponse(**p) for p in result["parcels"]], landed_cost=LandedCostResponse(**result["landed_cost"]))
    except OptimizationServiceError as exc:
        raise HTTPException(status_code=422, detail={"error": "OPTIMIZATION_ERROR", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "INVALID_CONFIGURATION", "message": str(exc)}) from exc


@app.post("/pricing/calculate", status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["pricing"])
async def calculate_pricing_legacy(request: LegacyPricingRequest) -> dict:
    return {"status": "not_implemented", "message": "Use POST /pricing for the implemented pricing and shipment optimization engine.", "accepted_request": request.model_dump(mode="json")}


@app.post("/payment/create-order", response_model=PaymentCreateOrderResponse, status_code=status.HTTP_201_CREATED, tags=["payment"])
async def payment_create_order(request: PaymentCreateOrderRequest) -> PaymentCreateOrderResponse:
    return PaymentCreateOrderResponse(**create_order(request))


@app.post("/payment/create-link", response_model=PaymentLinkCreateResponse, status_code=status.HTTP_201_CREATED, tags=["payment"])
async def payment_create_link(request: PaymentLinkCreateRequest) -> PaymentLinkCreateResponse:
    return PaymentLinkCreateResponse(**create_payment_link(request))


@app.get("/payment/link-status/{payment_link_id}", response_model=PaymentLinkStatusResponse, status_code=status.HTTP_200_OK, tags=["payment"])
async def payment_link_status(payment_link_id: str) -> PaymentLinkStatusResponse:
    return PaymentLinkStatusResponse(**get_payment_link_status(payment_link_id))


@app.post("/payment/verify", response_model=PaymentVerifyResponse, status_code=status.HTTP_200_OK, tags=["payment"])
async def payment_verify(request: PaymentVerifyRequest) -> PaymentVerifyResponse:
    return PaymentVerifyResponse(**verify_payment(request))


@app.post("/payment/webhook", response_model=RazorpayWebhookResponse, status_code=status.HTTP_200_OK, tags=["payment"])
async def payment_webhook(request: Request) -> RazorpayWebhookResponse:
    signature = request.headers.get("X-Razorpay-Signature", "")
    event_id = request.headers.get("x-razorpay-event-id")
    raw_body = await request.body()
    verify_webhook(raw_body, signature)
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "INVALID_WEBHOOK_BODY", "message": "Webhook body must be valid JSON"}) from exc
    payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
    payment_link = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
    return RazorpayWebhookResponse(status="accepted", event=payload.get("event"), event_id=event_id, payment_id=payment.get("id"), payment_link_id=payment_link.get("id"), money_location="RAZORPAY_MERCHANT_BALANCE" if payload.get("event") in {"payment.captured", "payment_link.paid"} else None)
