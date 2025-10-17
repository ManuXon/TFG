# 1️⃣ Build React (only used in prod)
FROM node:18 AS react-build
WORKDIR /app
COPY react-components/ ./react-components/
WORKDIR /app/react-components
RUN npm install --legacy-peer-deps && npm run build


# 2️⃣ Dash / Python stage
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# For prod: copy everything
ARG ENV=prod
COPY . .

# Copy built React assets only for prod
COPY --from=react-build /app/react-components/build ./assets/faculty_selector

EXPOSE 8050

# Use CMD override for dev (via compose)
CMD ["python", "app.py"]
