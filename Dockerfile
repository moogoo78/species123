# --- assets: pull pinned MUSUBii CSS from npm ---
FROM node:22-alpine AS assets
WORKDIR /build
RUN npm install --no-audit --no-fund musubii@9.4.0

# --- app ---
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY scripts scripts
COPY --from=assets /build/node_modules/musubii/dist/musubii.css /code/vendor/musubii.css
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "app:create_app()"]
