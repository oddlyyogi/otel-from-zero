FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY server.js .
CMD ["node", "--require", "@opentelemetry/auto-instrumentations-node/register", "server.js"]