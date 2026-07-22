FROM node:22-alpine AS build

WORKDIR /app

RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend ./

ARG VITE_API_BASE_URL=http://127.0.0.1:8000
ARG VITE_HERMES_WEB_URL=http://127.0.0.1:9119
ARG VITE_USE_MOCK=false
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_HERMES_WEB_URL=${VITE_HERMES_WEB_URL}
ENV VITE_USE_MOCK=${VITE_USE_MOCK}

RUN pnpm exec vite build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
