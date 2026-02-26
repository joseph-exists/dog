# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:24 AS build-stage

WORKDIR /app

COPY package*.json /app/

RUN npm install

COPY ./ /app/

ARG VITE_API_URL=${VITE_API_URL}
ARG VITE_DEMO_BUILDER_PACKS=internal.plugin.demo-builder.v1,example.runtime-safe.v1,example.ux-enhancer.v1,example.policy-guarded.v1,example.invalid.v1,example.ux-enhancer.v1,typography.fonts.v1,presentation.callouts.v1
ENV VITE_DEMO_BUILDER_PACKS=${VITE_DEMO_BUILDER_PACKS}

RUN npm run build


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1

COPY --from=build-stage /app/dist/ /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
