from flask import Flask, request
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("inventory")

app = Flask(__name__)
STOCK = {"mug": 5, "tee": 2, "cap": 0}

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
        with tracer.start_as_current_span("check stock") as check:
            left = STOCK.get(sku, 0)
            check.set_attribute("shop.stock.left", left)
        if left < qty:
            span.add_event("rejected", {"shop.stock.left": left})
            span.set_status(Status(StatusCode.ERROR, "out of stock"))
            return {"error": "out of stock"}, 409
        with tracer.start_as_current_span("write reservation"):
            STOCK[sku] = left - qty
        span.add_event("reserved", {"shop.stock.left": STOCK[sku]})
        return {"sku": sku, "reserved": qty, "left": STOCK[sku]}

if __name__ == "__main__":
    app.run(port=8082)