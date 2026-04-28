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

Запуск

```
pip install -r requirements.txt

set DD_URL=https://defectdojo.your-company.com
set DD_API_KEY=your_token
$env:DD_URL="https://defectdojo.your-company.com"
$env:DD_API_KEY="your_token"

python app.py

ИЛИ
docker-compose up -d --build
```

  Как работает

```
┌──────────┬─────────────────────────────────────────────────────────────────────────┐
│ Действие │                             Что происходит                              │
├──────────┼─────────────────────────────────────────────────────────────────────────┤
│ Accept   │ PATCH /api/v2/findings/{id}/ → false_p=true, active=false, запись в лог │
├──────────┼─────────────────────────────────────────────────────────────────────────┤
│ Reject   │ Только лог: REJECT | finding_id=… | reason=…, ничего в DD               │
├──────────┼─────────────────────────────────────────────────────────────────────────┤
│ Correct  │ PATCH (FP) + POST /api/v2/findings/{id}/notes/ с вашим комментарием     │
└──────────┴─────────────────────────────────────────────────────────────────────────┘

- После любого действия карточка сработки затемняется и блокируется
- В шапке отображается прогресс X / N обработано
- Лог пишется в logs/triage.log с timestamp
```

  Что нужно настроить

  Скопируйте .env.example в .env, укажите реальный DD_URL и DD_API_KEY (токен берётся из профиля DD: User → API v2 Key).