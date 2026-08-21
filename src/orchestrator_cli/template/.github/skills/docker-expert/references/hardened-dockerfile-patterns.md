# Hardened Dockerfile patterns

## Laravel (PHP-FPM + nginx or Octane)

```dockerfile
# syntax=docker/dockerfile:1
FROM composer:2 AS vendor
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --prefer-dist --no-interaction

FROM node:22-alpine AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY resources/ resources/
COPY vite.config.js tailwind.config.js ./
RUN npm run build

FROM php:8.3-fpm-alpine AS production
RUN addgroup -g 10001 app && adduser -u 10001 -G app -D app
WORKDIR /var/www/html
COPY --from=vendor /app/vendor ./vendor
COPY --from=assets /app/public/build ./public/build
COPY app bootstrap config database public routes artisan ./
USER 10001:10001
EXPOSE 9000
```

## Go static binary (distroless)

```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/api

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

## Anti-patterns (reject in review)

- `FROM ubuntu` runtime with apt upgrade in prod
- Single-stage `COPY . .` with dev dependencies
- Running as `root`
- Including `.git`, tests, or docs in final `COPY`
- `curl | bash` in production stage