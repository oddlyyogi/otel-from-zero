const express = require('express');
const { trace, context, propagation, SpanStatusCode } = require('@opentelemetry/api');

const tracer = trace.getTracer('storefront', '1.0.0');

const app = express();
app.use(express.json());
const ORDERS = process.env.ORDERS_URL;

app.post('/checkout', async (req, res) => {
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
  if (!ok) return res.status(400).json({ error: 'quantity must be 1 to 5' });

  const tier = req.get('x-customer-tier') || 'standard';
  trace.getActiveSpan()?.setAttribute('shop.customer.tier', tier);
  const bag = propagation.createBaggage({ 'shop.customer.tier': { value: tier } });
  const ctx = propagation.setBaggage(context.active(), bag);
  const r = await context.with(ctx, () => fetch(`${ORDERS}/orders`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(req.body),
  }));
  res.status(r.status).json(await r.json());
});

app.listen(8080, () => console.log('storefront listening on 8080'));