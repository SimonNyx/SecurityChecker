FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# Inject the container's DNS resolver into nginx.conf at startup so hostname
# re-resolution works in both Docker (127.0.0.11) and Podman environments.
CMD sh -c "NS=\$(awk '/^nameserver/{print \$2; exit}' /etc/resolv.conf) && \
           sed -i \"s/NAMESERVER/\$NS/g\" /etc/nginx/conf.d/default.conf && \
           nginx -g 'daemon off;'"
