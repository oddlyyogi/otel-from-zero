import logging
import sqlite3
from flask import Flask, request
from opentelemetry import trace, baggage, metrics
from opentelemetry.metrics import Observation
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.utils import suppress_instrumentation

tracer = trace.get_tracer("inventory")
meter = metrics.get_meter("inventory")
log = logging.getLogger("inventory")
log.setLevel(logging.INFO)

app = Flask(__name__)
DB = "stock.db"
TAKE = "UPDATE stock SET qty = qty - ? WHERE sku = ?"
SETUP = """
CREATE TABLE IF NOT EXISTS stock (sku TEXT PRIMARY KEY, qty INTEGER);
INSERT OR REPLACE INTO stock VALUES ('mug', 50), ('tee', 20), ('cap', 0);
"""
with sqlite3.connect(DB) as con:
    con.executescript(SETUP)


def units(con, sku):
    cur = con.cursor()
    cur.execute("SELECT qty FROM stock WHERE sku = ?", (sku,))
    row = cur.fetchone()
    return row[0] if row else 0

def observe_stock(options):
    with suppress_instrumentation(), sqlite3.connect(DB) as con:
        rows = con.cursor().execute("SELECT sku, qty FROM stock").fetchall()
    return [Observation(qty, {"shop.sku": sku}) for sku, qty in rows]

meter.create_observable_gauge("shop.stock.level", callbacks=[observe_stock],
                              unit="{item}", description="Items left in stock")

@app.get("/stock/<sku>")
def stock(sku):
    with tracer.start_as_current_span("check stock") as span:
        span.set_attribute("shop.sku", sku)
        left = units(sqlite3.connect(DB), sku)
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
            left = units(sqlite3.connect(DB), sku)
            check.set_attribute("shop.stock.left", left)
        if left < qty:
            span.add_event("rejected", {"shop.stock.left": left})
            log.warning("out of stock: %s (wanted %d, left %d)", sku, qty, left)
            span.set_status(Status(StatusCode.ERROR, "out of stock"))
            return {"error": "out of stock"}, 409
        with tracer.start_as_current_span("write reservation"):
            with sqlite3.connect(DB) as con:
                con.cursor().execute(TAKE, (qty, sku))
        span.add_event("reserved", {"shop.stock.left": left - qty})
        log.info("reserved %d x %s, %d left", qty, sku, left - qty)
        return {"sku": sku, "reserved": qty, "left": left - qty}

if __name__ == "__main__":
    app.run(port=8082)