FROM --platform=$TARGETPLATFORM python:3.12-alpine
LABEL maintainer="Karbob <karbobc@gmail.com>"

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    workday

# Switch to the non-privileged user
USER workday
WORKDIR /app

COPY ./src ./src/
COPY ./requirements.lock ./requirements.txt
RUN sed -i '/-e/d' requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /app/.cache

EXPOSE 8080

ENV FORWARDED_ALLOW_IPS *
CMD ["/app/.local/bin/uvicorn", "workday.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]