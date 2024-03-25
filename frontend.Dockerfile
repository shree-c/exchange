FROM node:alpine as build-step
WORKDIR /app
COPY /algotest_assignment/frontend /app
RUN npm install
RUN npm run build 
FROM nginx
COPY --from=build-step /app/dist /usr/share/nginx/html
EXPOSE 80
STOPSIGNAL SIGTERM
RUN ["echo", "frontend available at http://localhost:8080"]
CMD ["nginx", "-g", "daemon off;"]