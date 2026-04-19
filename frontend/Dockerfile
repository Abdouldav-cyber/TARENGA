FROM node:20-alpine

WORKDIR /app

# On installe seulement les dépendances système de base
RUN apk add --no-cache libc6-compat

# Copier les fichiers package.json et package-lock.json s'ils existent
COPY package*.json ./

# S'assurer que Next.js a l'autorisation d'écrire en local lors du dev
RUN npm install

# Copier le reste du code de l'application
COPY . .

# On expose le port 3000
EXPOSE 3000

# Démarrer le serveur en mode dev
CMD ["npm", "run", "dev"]
