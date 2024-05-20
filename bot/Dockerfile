# Установка базового образа
FROM python:3.10

# Установка рабочей директории
WORKDIR /bot

# Копирование файлов приложения в контейнер
COPY requirements.txt requirements.txt

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Что то копируем
COPY . /bot

# Команда для запуска бота
CMD ["python", "./bot.py"]