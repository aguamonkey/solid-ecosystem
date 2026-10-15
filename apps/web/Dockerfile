FROM node:22-alpine AS build
WORKDIR /workspace
COPY package*.json ./
COPY apps/web/package.json apps/web/package.json
COPY apps/mobile/package.json apps/mobile/package.json
COPY packages/notebook-client/package.json packages/notebook-client/package.json
RUN npm ci --workspace field-notebook-web
COPY packages/notebook-client packages/notebook-client
COPY apps/web apps/web
RUN npm run build --workspace field-notebook-web
FROM nginx:stable-alpine
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/apps/web/dist /usr/share/nginx/html
EXPOSE 80
