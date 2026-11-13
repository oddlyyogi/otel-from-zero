import json
import sys
import time
import urllib.parse
import urllib.request

QUERY = 'service:latency_ms:p95{service_name="inventory"}'
PROM = "http://localhost:9090/api/v1/query?" + urllib.parse.urlencode({"query": QUERY})
RULES = "http://localhost:3000/api/prometheus/grafana/api/v1/rules"

def get(url):
    return json.load(urllib.request.urlopen(url))

for _ in range(int(sys.argv[1])):
    result = get(PROM)["data"]["result"]
    p95 = float(result[0]["value"][1]) if result else 0.0
    state = get(RULES)["data"]["groups"][0]["rules"][0]["state"]
    print(time.strftime("%H:%M:%S"), f"p95 {p95:6.1f} ms", "alert", state, flush=True)
    time.sleep(10)
