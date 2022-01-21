FROM debian:latest

COPY . /app
WORKDIR app

RUN apt-get update && apt-get install python3-pip curl -y  &&  \
    pip install  --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
