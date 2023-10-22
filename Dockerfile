FROM python:3.12-alpine
LABEL maintainer="Karbob <karbobc@gmail.com>"

ENV PYTHONUNBUFFERED 1

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]