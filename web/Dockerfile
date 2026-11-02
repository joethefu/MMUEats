# --- Build stage ---
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Relative API base means the browser calls the SAME origin nginx is serving
# from, which nginx then reverse-proxies to the backend service — this avoids
# needing CORS configuration in production entirely. Override at build time
# with --build-arg if the frontend is ever deployed on a different origin
# than the API.
ARG VITE_API_BASE_URL=/api
ARG VITE_GOOGLE_MAPS_API_KEY=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY

RUN npm run build

# --- Serve stage ---
FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
