FROM node:lts-alpine3.19 

WORKDIR /app



COPY /algotest_assignment/frontend /app


RUN npm install

RUN npm run build


RUN cd dist



EXPOSE 8080

CMD ["npx", "serve", "-l", "8080"]
