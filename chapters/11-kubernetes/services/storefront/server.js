const express = require('express');
const pino = require('pino');
const { trace, metrics, context, propagation, SpanStatusCode } = require('@opentelemetry/api');

const tracer = trace.getTracer('storefront', '1.0.0');
const meter = metrics.getMeter('storefront', '1.0.0');
const checkoutTime = meter.createHistogram('shop.checkout.duration', {
  unit: 's', description: 'Time to complete a checkout',
});
const inProgress = meter.createUpDownCounter('shop.checkouts.active', {
  unit: '{checkout}', description: 'Checkouts in progress',
});

const log = pino();
const app = express();
app.use(express.json());
const ORDERS = process.env.ORDERS_URL;

app.post('/checkout', async (req, res) => {
  const start = performance.now();
  inProgress.add(1);
  const ok = tracer.startActiveSpan('validate cart', (span) => {
    try {
      const { sku, qty } = req.body;
      span.setAttribute('shop.sku', sku);
      span.setAttribute('shop.qty', qty);
      if (!Number.isInteger(qty) || qty < 1 || qty > 5) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: 'bad quantity' });
        return false;
      }
      return true;
    } finally {
      span.end();
    }
  });
  if (!ok) {
    log.warn({ sku: req.body.sku, qty: req.body.qty }, 'cart refused: bad quantity');
    inProgress.add(-1);
    return res.status(400).json({ error: 'quantity must be 1 to 5' });
  }

  const tier = req.get('x-customer-tier') || 'standard';
  trace.getActiveSpan()?.setAttribute('shop.customer.tier', tier);
  const bag = propagation.createBaggage({ 'shop.customer.tier': { value: tier } });
  const ctx = propagation.setBaggage(context.active(), bag);
  const r = await context.with(ctx, () => fetch(`${ORDERS}/orders`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(req.body),
  }));
  const outcome = r.ok ? 'placed' : 'failed';
  log.info({ status: r.status, tier }, `checkout ${outcome}`);
  checkoutTime.record((performance.now() - start) / 1000, { 'shop.outcome': outcome });
  inProgress.add(-1);
  res.status(r.status).json(await r.json());
});

app.listen(8080, () => console.log('storefront listening on 8080'));