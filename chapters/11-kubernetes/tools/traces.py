import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FMT = "%Y-%m-%dT%H:%M:%SZ"
since = datetime.fromtimestamp(int(sys.argv[1]), timezone.utc)
query = {
    "query.service_name": "shopper",
    "query.start_time_min": since.strftime(FMT),
    "query.start_time_max": datetime.now(timezone.utc).strftime(FMT),
    "query.search_depth": "1000",
}
url = "http://localhost:16686/api/v3/traces?" + urllib.parse.urlencode(query)
try:
    data = json.load(urllib.request.urlopen(url))
except urllib.error.HTTPError:
    data = {"result": {"resourceSpans": []}}
traces, errors = set(), set()
spans = 0
for rs in data["result"]["resourceSpans"]:
    for ss in rs["scopeSpans"]:
        for span in ss["spans"]:
            spans += 1
            traces.add(span["traceId"])
            if span.get("status", {}).get("code") in (2, "STATUS_CODE_ERROR"):
                errors.add(span["traceId"])
print(len(traces), "traces,", spans, "spans,", len(errors), "with errors")
