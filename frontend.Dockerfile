FROM node:alpine as builder
WORKDIR /app
COPY /algotest_assignment/frontend/package*.json /app/
RUN npm ci --no-audit
COPY /algotest_assignment/frontend /app
RUN npm run build 
EXPOSE 8080
FROM nginx:alpine AS nginx
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80  
CMD ["nginx", "-g", "daemon off;"]