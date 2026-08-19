# Landed-cost optimization flow

The pricing engine now uses only values already supplied in the pricing request.

## Inputs

- item weights and dimensions
- package tare weight, dimensions, capacity and cost
- ITPS/EMS slab rates and weight limits
- ITPS/EMS transit range when supplied
- product value
- insurance and customs additions
- duty and tax rates
- preferential-duty eligibility/rate
- destination-country fees
- platform fees

No carrier API, external rate table, live transit lookup or guessed value is used.

## Flow

```text
Request
  -> validate
  -> generate feasible parcel candidates
  -> calculate exact ITPS/EMS shipping from supplied lane data
  -> optimize shipment
  -> calculate canonical landed cost
  -> return shipment + landed-cost breakdown
```

## Modes

### CHEAPEST

Minimizes shipment shipping cost. Under the current landed-cost formula, customs value is product value + shipping + insurance + additions, and duty/tax/platform percentages are non-negative. Therefore a lower shipping cost cannot produce a higher landed cost. The selected shipment is then passed through the canonical landed-cost calculator and the final landed cost is returned.

### FASTEST

Uses only `transit_min_days` / `transit_max_days` already present on the supplied lane. The maximum supplied transit estimate is used conservatively. If transit information is missing, FASTEST cannot invent it and fails rather than guessing.

### BALANCED

Combines the supplied shipping cost with the supplied transit estimate. It does not introduce a made-up delivery-time model.

## Important

`landed_cost.py` remains the canonical calculation path. The optimizer chooses the shipment configuration; the landed-cost module calculates the final monetary result from that chosen shipping cost. This avoids maintaining two independent landed-cost formulas.
