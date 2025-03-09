FROM node:16

WORKDIR /frontend

# Copy package.json
COPY package.json ./

RUN yarn install

COPY . .

EXPOSE 3000


CMD ["yarn", "start"]