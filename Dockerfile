FROM python:3.9.17-slim-bullseye

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libpq-dev gcc

COPY ./ ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
