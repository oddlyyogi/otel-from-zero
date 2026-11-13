FROM node:24-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tracing.js server.js ./
CMD ["node", "--require", "./tracing.js", "server.js"]