# rbScript
Установка:
    pip install pyrobloxbot keyboard
    pip install mss opencv-python numpy
    и надо накотить питон если нет
Запуск:
    python main.py вписывать в павершел

Управление:
    F6      — старт/стоп
    Esc     — выход
    Ctrl+M  — failsafe pyrobloxbot

ЧТО ДЕЛАЕТ:
    Персонаж идёт по восьмиугольнику: W → W+D → D → S+D → S → S+A → A → W+A
    и так по кругу, непрерывно. Каждая сторона держится LEG_DURATION секунд,
    после каждой — пауза STEP_SETTLE_DELAY, чтобы персонаж успел остановиться
    и не накапливал снос из-за инерции разворота.

НАСТРОЙКА:
    LEG_DURATION       — длина одной стороны (сек). Больше = крупнее круг.
    STEP_SETTLE_DELAY  — пауза между сторонами (сек). Больше = меньше дрейфа.
    CLOCKWISE          — True по часовой, False против.