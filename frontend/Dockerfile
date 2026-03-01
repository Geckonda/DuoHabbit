FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

#Собираем проект
RUN npm run build

#Устанавливаем простой http сервер для статики
RUN npm install -g serve

EXPOSE 3000

#Запускаем собранные файлы
CMD ["serve", "-s", "dist", "-l", "3000"]