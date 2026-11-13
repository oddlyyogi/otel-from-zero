const express = require('express');

const app = express();
app.use(express.json());
const ORDERS = process.env.ORDERS_URL;

app.post('/checkout', async (req, res) => {
  const r = await fetch(`${ORDERS}/orders`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(req.body),
  });
  res.status(r.status).json(await r.json());
});

app.listen(8080, () => console.log('storefront listening on 8080'));