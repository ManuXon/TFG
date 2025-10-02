# 1️⃣ Build React
#FROM node:18 as react-build
#WORKDIR /app
#COPY react-components/ ./react-components/
#WORKDIR /app/react-components
#RUN npm install --legacy-peer-deps && npm run build

# 2️⃣ Build Python/Dash
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Dash app code
COPY . .

# Copy built React files into assets
#COPY --from=react-build /app/react-components/build ./assets/faculty_selector

EXPOSE 8050
CMD ["python", "app.py"]
