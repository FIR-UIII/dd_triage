Структура проекта

```
dd_triage/
├── app.py              # Flask-приложение, маршруты
├── config.py           # Настройки из переменных окружения
├── dd_client.py        # Клиент DefectDojo API
├── requirements.txt
├── .env.example        # Шаблон переменных окружения
├── logs/               # Лог-файл triаge.log
└── templates/
    ├── index.html      # Экран ввода ID
    └── findings.html   # Экран разбора сработок
```

Установка и запуск
```
# При локальном запуске не через контейнер изменить host="0.0.0.0" на host="127.0.0.1"
pip install -r requirements.txt

# установить переменные окружения с данными ДД
set DD_URL=https://defectdojo.your-company.com
set DD_API_KEY=your_token
$env:DD_URL="https://defectdojo.your-company.com"
$env:DD_API_KEY="your_token"

# запуск
python app.py
ИЛИ
docker-compose up -d --build
```