FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
COPY src ./src
COPY index.html ./
COPY vite.config.js ./
RUN npm ci
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_BASE=/
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_BASE=${VITE_BASE}
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --retries=3 CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1
