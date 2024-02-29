FROM --platform=$TARGETPLATFORM python:3.12-alpine
LABEL maintainer="Karbob <karbobc@gmail.com>"

ENV PYTHONUNBUFFERED 1
WORKDIR /app

COPY ./src ./
COPY ./requirements.lock ./
RUN sed '/-e/d' requirements.lock > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

ENV FORWARDED_ALLOW_IPS *
CMD ["uvicorn", "workday.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]