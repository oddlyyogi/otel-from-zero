import logging
from flask import Flask, request
from opentelemetry import trace, baggage, metrics
from opentelemetry.metrics import Observation
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("inventory")
meter = metrics.get_meter("inventory")
log = logging.getLogger("inventory")
log.setLevel(logging.INFO)

app = Flask(__name__)
STOCK = {"mug": 50, "tee": 20, "cap": 0}

def observe_stock(options):
    return [Observation(left, {"shop.sku": sku}) for sku, left in STOCK.items()]

meter.create_observable_gauge("shop.stock.level", callbacks=[observe_stock],
                              unit="{item}", description="Items left in stock")

@app.get("/stock/<sku>")
def stock(sku):
    with tracer.start_as_current_span("check stock") as span:
        span.set_attribute("shop.sku", sku)
        left = STOCK.get(sku, 0)
        span.set_attribute("shop.stock.left", left)
        return {"sku": sku, "left": left}

@app.post("/reserve")
def reserve():
    with tracer.start_as_current_span("reserve") as span:
        order = request.get_json()
        sku, qty = order["sku"], order["qty"]
        span.set_attribute("shop.sku", sku)
        span.set_attribute("shop.qty", qty)
        tier = baggage.get_baggage("shop.customer.tier")
        span.set_attribute("shop.customer.tier", tier or "unknown")
        with tracer.start_as_current_span("check stock") as check:
            left = STOCK.get(sku, 0)
            check.set_attribute("shop.stock.left", left)
        if left < qty:
            span.add_event("rejected", {"shop.stock.left": left})
            log.warning("out of stock: %s (wanted %d, left %d)", sku, qty, left)
            span.set_status(Status(StatusCode.ERROR, "out of stock"))
            return {"error": "out of stock"}, 409
        with tracer.start_as_current_span("write reservation"):
            STOCK[sku] = left - qty
        span.add_event("reserved", {"shop.stock.left": STOCK[sku]})
        log.info("reserved %d x %s, %d left", qty, sku, STOCK[sku])
        return {"sku": sku, "reserved": qty, "left": STOCK[sku]}

if __name__ == "__main__":
    app.run(port=8082)