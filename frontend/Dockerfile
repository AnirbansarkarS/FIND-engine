# --- Build Stage ---
FROM node:20-alpine AS build

# Build-time argument for backend URL
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# --- Serve Stage ---
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Expose Nginx port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
