# OpenTelemetry from Zero

The code for the **OpenTelemetry** video course: one small shop, three services in three languages, and everything
needed to trace, measure and log it with OpenTelemetry, from a first span to a production-ready Collector.

**Pebble Shop**

- `services/storefront`: Node.js and Express
- `services/orders`: Java and Spring Boot, with the OpenTelemetry Java agent
- `services/inventory`: Python, Flask and SQLite
- `tools/shopper.py`: a client that places orders and starts every trace

The telemetry goes through the **OpenTelemetry Collector** to **Jaeger** (traces), **Prometheus** (metrics) and
**Loki** (logs), with **Grafana** on top. Everything runs locally with Docker Compose, and chapter 11 runs it on a
local Kubernetes cluster with kind.

The root of this repository is the finished project, as it stands at the end of the last chapter. Every chapter's
starting point for the next one is in [`chapters/`](chapters).

| # | Chapter | Folder |
|---|---------|--------|
| 1 | What Observability Is, and Your First Trace | [chapters/01-what-observability-is-and-your-first-trace](chapters/01-what-observability-is-and-your-first-trace) |
| 2 | Traces and Spans in Depth | [chapters/02-traces-and-spans-in-depth](chapters/02-traces-and-spans-in-depth) |
| 3 | Zero-Code Instrumentation | [chapters/03-zero-code-instrumentation](chapters/03-zero-code-instrumentation) |
| 4 | Manual Instrumentation with the SDK | [chapters/04-manual-instrumentation-with-the-sdk](chapters/04-manual-instrumentation-with-the-sdk) |
| 5 | Metrics | [chapters/05-metrics](chapters/05-metrics) |
| 6 | Logs, Correlated with Traces | [chapters/06-logs-correlated-with-traces](chapters/06-logs-correlated-with-traces) |
| 7 | The Collector | [chapters/07-the-collector](chapters/07-the-collector) |
| 8 | Process Data in the Collector | [chapters/08-process-data-in-the-collector](chapters/08-process-data-in-the-collector) |
| 9 | Semantic Conventions and Resources | [chapters/09-semantic-conventions-and-resources](chapters/09-semantic-conventions-and-resources) |
| 10 | Sampling and Cost Control | [chapters/10-sampling-and-cost-control](chapters/10-sampling-and-cost-control) |
| 11 | Kubernetes | [chapters/11-kubernetes](chapters/11-kubernetes) |
| 12 | Debug a Real Incident | [chapters/12-debug-a-real-incident](chapters/12-debug-a-real-incident) |
| 13 | Production | [chapters/13-production](chapters/13-production) |

## Versions

OpenTelemetry Collector Contrib 0.165.0, Java agent 2.33.1, Python SDK 1.45.2 with instrumentation 0.66b2,
Node SDK 0.301.2, Spring Boot 4.1.2 on Java 25, Jaeger 2.23.0, Prometheus 3.16.0, Loki 3.7.10, Grafana 13.3.1,
kind 0.33.0 with Kubernetes 1.37.0, cert-manager 1.21.3, OpenTelemetry Operator 0.163.0.

## Run it

You need Docker with Compose, Java 25 with Maven, Python 3 and OpenSSL.

```bash
# the Java agent is not stored in git: download the pinned release
curl -fsSL -o services/orders/opentelemetry-javaagent.jar \
  https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v2.33.1/opentelemetry-javaagent.jar

# build the orders service
mvn -q -f services/orders/pom.xml package -DskipTests

# certificates, token and queue folder for the Collector (chapter 13)
mkdir -p certs data/queue && chmod 777 data/queue
cd certs
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 30 -subj "/CN=Pebble Shop CA" -addext "keyUsage=critical,keyCertSign,cRLSign"
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=localhost"
printf "subjectAltName=DNS:localhost,DNS:collector\nauthorityKeyIdentifier=keyid,issuer\nextendedKeyUsage=serverAuth\n" > san.ext
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 30 -extfile san.ext
chmod 644 server.key
cd ..
echo "SHOP_TOKEN=$(openssl rand -hex 16)" > .env

# start everything, then place an order
docker compose up -d --build
python3 -m venv .venv && .venv/bin/pip install -r tools/requirements.txt
.venv/bin/python tools/shopper.py mug:1 tee:1
```

Then open Jaeger at http://localhost:16686, Prometheus at http://localhost:9090 and Grafana at http://localhost:3000.
`docker compose down` stops it all.

The chapter folders work the same way; the early ones need fewer steps (for example, no certificates before
chapter 13 and no Collector before chapter 7).

## License

[MIT](LICENSE)
