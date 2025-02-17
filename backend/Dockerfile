ARG PYTHON_VERSION=3.11-slim-bullseye

FROM python:${PYTHON_VERSION} AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl python3-dev tesseract-ocr ghostscript && \
    pip install --upgrade "pip<24.1" && pip install pipenv && \
    pip install textract && \
    pip install duckduckgo-search && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y curl

COPY Pipfile Pipfile.lock ./

# Development Environment
FROM base AS development

RUN pipenv install --dev --system

COPY chat_with_your_data/ ./chat_with_your_data
COPY entrypoint.dev.sh ./entrypoint.dev.sh

RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu torch && \
    pip install transformers && \
    python -m spacy download de_core_news_lg && \
    python -m spacy download en_core_web_lg

EXPOSE 8000
RUN chmod +x entrypoint.dev.sh
ENTRYPOINT ["/app/entrypoint.dev.sh"]

# Production Environment
FROM base AS production

RUN pipenv install --system

COPY chat_with_your_data/ ./chat_with_your_data
COPY entrypoint.sh ./entrypoint.sh

RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu torch && \
    pip install transformers && \
    python -m spacy download de_core_news_lg && \
    python -m spacy download en_core_web_lg

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]