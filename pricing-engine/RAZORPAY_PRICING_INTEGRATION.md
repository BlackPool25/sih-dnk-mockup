# SIH DNK Pricing Engine + Razorpay — Final Integration Workflow

## 1. Final design

This is the single integration document for the pricing-engine Razorpay work.

The intended website flow is:

1. Buyer opens a product/order page.
2. The normal application backend identifies the seller/artisan attached to that product/order.
3. Buyer enters destination/shipment information.
4. Backend/pricing-engine calculates shipping and the landed-cost estimate using the existing pricing logic/data supplied to the pricing engine.
5. Buyer sees product price, shipping, duty/VAT estimate and landed-cost estimate.
6. Buyer accepts the quote/order.
7. Buyer clicks the payment action. The browser calls the backend; the buyer does NOT call Razorpay's API directly.
8. Backend resolves the seller's Razorpay merchant configuration from the seller/order context and creates a Razorpay Payment Link using server-side credentials.
9. Backend returns only the Razorpay `short_url` to the buyer's browser.
10. Buyer opens the hosted Razorpay payment page and pays.
11. Payment is captured into the Razorpay merchant account represented by the seller credentials used to create the link.
12. Razorpay sends the payment event to the backend webhook.
13. Backend verifies the webhook signature and updates payment/order state.
14. Backend/frontend can query payment status and display the high-level money location: seller Razorpay merchant balance after capture, followed by Razorpay's normal settlement process.

The pricing engine does NOT send its duty/tax formulas to Razorpay. Razorpay receives only the payment amount and payment metadata required to create the link.

## 2. What is collected

The Payment Link amount is:

`PRODUCT VALUE + SHIPPING`

Destination duty/VAT remains an estimate and is NOT included in the payment-link amount, matching the project workflow.

## 3. Buyer versus merchant responsibilities

### Buyer/frontend

The buyer initiates the request by clicking the payment button. The frontend calls:

`POST /payment/create-link`

The browser must never contain:

- Razorpay secret key
- webhook secret
- seller merchant secret
- database credentials

### Backend

The backend is the trusted payment initiator. It receives a seller/order context and resolves the correct merchant credentials server-side.

The backend then calls Razorpay's API.

Therefore the buyer does NOT create a Razorpay Payment Link using buyer credentials. The buyer only requests the backend to create the link and then opens the returned hosted URL.

## 4. Seller merchant routing implemented in this branch

`POST /payment/create-link` now requires:

`seller_id`

The backend maps that seller ID to server-side environment variables:

```text
RAZORPAY_SELLER_<SELLER_ID>_KEY_ID
RAZORPAY_SELLER_<SELLER_ID>_KEY_SECRET
```

The seller ID is normalized to uppercase and non-alphanumeric characters become underscores.

Example:

```text
seller_id = demo-seller

RAZORPAY_SELLER_DEMO_SELLER_KEY_ID=rzp_test_...
RAZORPAY_SELLER_DEMO_SELLER_KEY_SECRET=...
```

For backward-compatible single-merchant testing, `RAZORPAY_DEFAULT_SELLER_ID` may point to a seller ID and that seller can fall back to `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`.

For a real multi-seller system, replace this environment-variable mapping with secure server-side merchant-account storage/vaulting and the final Razorpay marketplace/linked-account architecture approved for the project.

The current branch does NOT implement automated multi-artisan onboarding or Razorpay Route/Linked Accounts. It does, however, make the payment-link endpoint seller-aware and keeps merchant credentials entirely server-side.

## 5. Current endpoints

### Pricing

`POST /pricing`

Runs the existing pricing/optimization flow.

### Create Payment Link

`POST /payment/create-link`

Request includes:

```json
{
  "seller_id": "demo-seller",
  "amount_minor": 500920,
  "currency": "INR",
  "reference_id": "ORDER-123",
  "description": "Shipment payment ORDER-123",
  "notes": {
    "destination": "US"
  }
}
```

The frontend should NOT be trusted to decide the final amount in production. The final order backend should load the accepted quote/order and derive the collectible amount server-side before calling the payment-link service. The current temporary test page passes the pricing result amount so the flow can be tested before the order service exists.

Response includes:

- `payment_link_id`
- `short_url`
- `amount`
- `currency`
- `reference_id`
- `seller_id`
- `destination = SELLER_RAZORPAY_MERCHANT_ACCOUNT`

### Payment Link status / money tracking

`GET /payment/link-status/{payment_link_id}?seller_id=demo-seller`

The backend authenticates to the seller's Razorpay merchant account and queries the Payment Link.

It reports:

- status
- amount
- amount paid
- payment ID
- seller ID
- destination
- current high-level money location
- settlement note

After successful payment, the current UI reports:

`SELLER_RAZORPAY_MERCHANT_BALANCE`

This means the payment has been captured/received by the seller's Razorpay merchant account. It does NOT claim that the money has already settled into the seller's bank account.

### Payment verification

`POST /payment/verify`

This verifies the standard Razorpay order/payment signature for order-based Checkout flows. The current Payment Link test flow primarily uses the Payment Link + webhook path.

### Webhook

`POST /payment/webhook`

Verifies `X-Razorpay-Signature` using the backend-only `RAZORPAY_WEBHOOK_SECRET` and extracts payment/payment-link/seller metadata when present.

The final order service should use this event to perform the authoritative payment state transition.

## 6. Webhook is still required

YES.

The Payment Link and webhook perform different jobs.

Payment Link:

`backend -> Razorpay -> hosted payment URL`

Webhook:

`Razorpay -> backend -> verified payment event`

The workflow requires automatic payment state updates and does not want a manual "mark as paid" action.

The target transition is:

`quote_accepted -> paid_held`

The webhook URL is not generated by the frontend.

## 7. Webhook URL

The local application endpoint is:

`POST /payment/webhook`

When the backend is deployed at:

`https://pricing-engine.example.com`

the Razorpay webhook URL is:

`https://pricing-engine.example.com/payment/webhook`

For the team's actual deployment, use:

`https://<public-backend-host>/payment/webhook`

`http://127.0.0.1:8003/payment/webhook` cannot be called by Razorpay's servers.

The frontend does NOT fetch this URL. It is deployment/Razorpay configuration. The frontend only receives the Payment Link `short_url` and later queries a backend order/payment status endpoint.

## 8. Webhook secret

The webhook secret is chosen/configured by the project and must match the secret entered in Razorpay's webhook settings.

Example:

```env
RAZORPAY_WEBHOOK_SECRET=SIH_DNK_TEST_WEBHOOK_2026
```

Do not expose it to the browser.

## 9. Environment variables

For the current test setup:

```env
RAZORPAY_KEY_ID=rzp_test_replace_me
RAZORPAY_KEY_SECRET=replace_me
RAZORPAY_WEBHOOK_SECRET=replace_me
RAZORPAY_CURRENCY=INR
RAZORPAY_DEFAULT_SELLER_ID=demo-seller

RAZORPAY_SELLER_DEMO_SELLER_KEY_ID=rzp_test_replace_me
RAZORPAY_SELLER_DEMO_SELLER_KEY_SECRET=replace_me
```

Use the seller merchant's Test Mode credentials for the seller-specific variables. If the same Test merchant account is being used for the demo, the values can be the same as the base test credentials.

Never commit the real `.env`.

## 10. Existing pricing data and access path

### Shipping/rates

`pricing-engine/app/shipping.py`

Contains ITPS and EMS calculation functions. ITPS uses actual parcel weight/slab configuration supplied to the calculation. EMS can use volumetric weight and a configured divisor.

### Customs value

`pricing-engine/app/customs_value.py`

Calculates customs/CIF value from product value, shipping, insurance and other additions.

### Duty

`pricing-engine/app/duty.py`

Calculates duty from customs value and the supplied duty rate.

### Tax

`pricing-engine/app/tax.py`

Calculates tax using customs value/duty and the supplied tax-base rule.

### Country fees

`pricing-engine/app/fee_rates.py`

Contains the current TEST fee configuration. These values must be replaced/connected to authoritative production data before production use.

### Fees

`pricing-engine/app/fees.py`

Calculates country fee components and totals.

### Platform fees

`pricing-engine/app/platform_fees.py`

Calculates platform percentage/fixed fees. The current test UI sends zero platform fee.

### Landed-cost orchestration

`pricing-engine/app/landed_cost.py`

Orchestrates customs value, preferential rate, duty, tax, country fees, platform fee and final landed cost.

### Optimization

`pricing-engine/app/optimization_service.py`

Validates pricing inputs and invokes the existing shipment optimizer.

### Database

`pricing-engine/app/config.py` reads `DATABASE_URL` and `REDIS_URL`.

`pricing-engine/app/db.py` creates the SQLAlchemy engine/session from `DATABASE_URL`.

The current `/pricing` route does NOT query the database directly. It receives the pricing configuration in the request and passes it into the existing optimizer. The temporary test UI therefore uses embedded TEST values; the real application must replace those with data from the team's product/order/rate data source.

## 11. Final frontend implementation required

The real frontend should:

1. Load product and seller information from the normal backend.
2. Keep the seller ID associated with the product/order; do not ask the buyer to type an arbitrary seller ID.
3. Ask the buyer for destination and shipment information.
4. Request a quote from the backend.
5. Display product price, shipping, duty/VAT estimate and landed-cost estimate.
6. Clearly state that destination duty/VAT is an estimate and is not collected by the payment link.
7. Let the buyer accept the quote/order.
8. Call the backend payment-link endpoint for the confirmed order.
9. Receive the `short_url`.
10. Redirect/open the hosted Razorpay URL.
11. After returning to the website, query backend order/payment status.
12. Display payment success based on backend-confirmed state, not browser assumptions.

The frontend never calculates ITPS/EMS, duty/tax, or payment amounts independently in production.

## 12. Final backend implementation required

The final order/backend layer should:

1. Resolve product -> seller/artisan.
2. Resolve shipment/destination information.
3. Call pricing-engine.
4. Store an immutable quote with expiry/version information.
5. Let buyer accept the quote.
6. Store the order and exact seller ID.
7. Derive collectible amount server-side as product + shipping.
8. Resolve the seller's Razorpay merchant account securely.
9. Create the Payment Link.
10. Store `payment_link_id`, reference/order ID, seller ID, amount and currency.
11. Return only `short_url` to the frontend.
12. Receive and verify the webhook.
13. Idempotently process the payment event.
14. Set the payment state to `paid_held` after verified capture.
15. Expose an order/payment-status endpoint for the frontend.
16. Reconcile with Razorpay periodically if required.
17. Keep settlement/refund/dispute state separate from capture.

## 13. Multi-artisan production architecture

The current branch provides a seller-aware boundary but not a full merchant onboarding system.

Production must have a secure mapping such as:

`application seller_id -> Razorpay merchant account`

and the backend must select the correct merchant account without trusting buyer-supplied credentials.

If the project uses Razorpay Route/Linked Accounts, implement the official onboarding, linked-account and transfer/settlement flow separately after confirming the exact cross-border requirements. Do not implement a fake client-side transfer.

## 14. Complete real-website flow

```text
BUYER
  |
  | product/order page
  v
FRONTEND
  |
  | destination + shipment data
  v
BACKEND / PRICING ENGINE
  |
  +--> existing ITPS / EMS optimization
  +--> customs value
  +--> duty estimate
  +--> tax estimate
  +--> country fees
  +--> landed-cost estimate
  |
  v
QUOTE
  |
  | buyer accepts
  v
ORDER BACKEND
  |
  +--> seller_id
  +--> immutable quote
  +--> collectible amount = PRODUCT + SHIPPING
  |
  | POST /payment/create-link
  v
SELLER MERCHANT CONFIGURATION
  |
  | server-side credentials
  v
RAZORPAY
  |
  | Payment Link short_url
  v
FRONTEND / BUYER
  |
  | opens hosted link
  v
RAZORPAY CHECKOUT
  |
  | payment
  v
SELLER RAZORPAY MERCHANT BALANCE
  |
  +------------------------------+
  |                              |
  | webhook                      | status query/reconciliation
  v                              v
BACKEND                       BACKEND
  |                              |
  +--> verify signature          +--> display status
  +--> idempotency               +--> money location
  +--> paid_held
```

## 15. What this branch now provides

- Existing pricing/optimization logic remains unchanged.
- Buyer-facing test page.
- Seller-aware Payment Link creation.
- Seller-specific server-side Razorpay Test Mode credential mapping.
- No seller secret exposed to the browser.
- Payment Link returned to buyer as `short_url`.
- Payment Link status endpoint using the seller merchant credentials.
- High-level money-location tracking.
- Webhook signature verification.
- Payment/payment-link metadata extraction including seller ID where supplied.
- One single integration document.

## 16. What remains outside this small pricing-engine change

- Real seller onboarding/KYC.
- Secure persistent merchant credential storage/vault.
- Automated multi-artisan merchant routing beyond the environment mapping used for this test.
- Razorpay Route/Linked Account onboarding and transfer implementation.
- Persistent order/payment state machine.
- Real product/order database integration.
- Production customs/duty/tax data feeds.
- Production frontend.
- Final settlement/FIRC/e-BRC reconciliation.

## 17. Final rule

The buyer requests the payment link.

The backend creates the payment link.

The backend chooses the seller merchant account.

The buyer only receives the hosted payment URL.

Razorpay collects the money into the seller's configured Razorpay merchant account.

Razorpay's webhook tells the backend that payment happened.

The backend—not the frontend—changes payment state.

Destination duty/VAT remains an estimate and is not collected through this payment link.
