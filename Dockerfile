FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаём тестовую SQLite-базу внутри образа.
RUN python database/init_db.py

EXPOSE 5000

CMD ["python", "app.py"]
