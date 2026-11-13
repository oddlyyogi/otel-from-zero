from concurrent.futures import ThreadPoolExecutor
import contextvars
import sys
import requests
from opentelemetry import trace, propagate
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind

provider = TracerProvider(resource=Resource.create({"service.name": "shopper"}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("shopper")

def reserve(sku, qty):
    with tracer.start_as_current_span("POST", kind=SpanKind.CLIENT) as span:
        headers = {}
        propagate.inject(headers)
        print(headers)
        url = "http://localhost:8080/checkout"
        r = requests.post(url, json={"sku": sku, "qty": qty}, headers=headers)
        span.set_attribute("http.response.status_code", r.status_code)
        print(r.status_code, r.json())

items = [arg.split(":") for arg in sys.argv[1:]]
with tracer.start_as_current_span("checkout") as root:
    root.set_attribute("shop.items", [sku for sku, _ in items])
    print("trace", format(root.get_span_context().trace_id, "032x"))
    with ThreadPoolExecutor() as pool:
        for sku, qty in items:
            pool.submit(contextvars.copy_context().run, reserve, sku, int(qty))
provider.shutdown()