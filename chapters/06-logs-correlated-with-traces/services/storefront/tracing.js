const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-proto');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { AggregationType } = require('@opentelemetry/sdk-metrics');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),
  views: [{
    instrumentName: 'shop.checkout.duration',
    aggregation: {
      type: AggregationType.EXPLICIT_BUCKET_HISTOGRAM,
      options: { boundaries: [0.05, 0.1, 0.25, 0.5, 1, 2.5] },
    },
  }],
  instrumentations: [getNodeAutoInstrumentations({
    '@opentelemetry/instrumentation-net': { enabled: false },
    '@opentelemetry/instrumentation-dns': { enabled: false },
  })],
});
sdk.start();

process.on('SIGTERM', () => sdk.shutdown().finally(() => process.exit(0)));