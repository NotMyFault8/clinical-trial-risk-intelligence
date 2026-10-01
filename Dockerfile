FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
WORKDIR /app
ENV CTR_PROJECT_ROOT=/app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements-linux.lock ./
RUN pip install --no-cache-dir -r requirements-linux.lock
COPY pyproject.toml ./
COPY src ./src
COPY sql ./sql
COPY configs ./configs
COPY prompts ./prompts
RUN pip install --no-deps . && useradd --create-home researcher
USER researcher
EXPOSE 8000
CMD ["uvicorn", "clinical_trial_risk.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
