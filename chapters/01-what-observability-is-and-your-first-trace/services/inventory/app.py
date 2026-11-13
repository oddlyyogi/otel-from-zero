from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

resource = Resource.create({"service.name": "inventory"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
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

if __name__ == "__main__":
    app.run(port=8082)