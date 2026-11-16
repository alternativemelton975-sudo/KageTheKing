FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

CMD ["sh", "-c", "if [ -f KageTheKing/main.py ]; then python KageTheKing/main.py --log-level INFO; else python main.py --log-level INFO; fi"]
