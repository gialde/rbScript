"""
Скрипт автоматического движения по кругу для Roblox (ПК/Windows).

ВНИМАНИЕ: pydirectinput на Windows может требовать запуска скрипта
от имени администратора для корректной инъекции ввода в некоторые процессы.
Если ввод не доходит до игры — запустите терминал с правами администратора.

Не используйте pyautogui в качестве замены — он не работает с Roblox,
так как игра игнорирует стандартный SendInput без скан-кодов DirectInput.
"""

import sys
import time
import threading

# --- Проверка и импорт зависимостей ---
try:
    import pydirectinput
except ImportError:
    print("Ошибка: не найден модуль 'pydirectinput'.")
    print("Выполните команду: pip install pydirectinput keyboard pygetwindow")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("Ошибка: не найден модуль 'keyboard'.")
    print("Выполните команду: pip install pydirectinput keyboard pygetwindow")
    sys.exit(1)

try:
    import pygetwindow as gw
except ImportError:
    print("Ошибка: не найден модуль 'pygetwindow'.")
    print("Выполните команду: pip install pydirectinput keyboard pygetwindow")
    sys.exit(1)

# =====================================================================
# НАСТРОЙКИ (все значения можно менять вручную перед запуском скрипта)
# =====================================================================

LEG_DURATION = 1.5          # секунд идти прямо за один отрезок
TURN_DEGREES = 90           # угол поворота
TURN_METHOD = "mouse"       # "mouse" | "strafe"
                            # "mouse" — физический поворот камеры мышью (персонаж вращается)
                            # "strafe" — обход квадрата клавишами W→A→S→D без мыши
                            #   (это НЕ поворот персонажа, а движение по квадратной траектории
                            #    относительно текущей ориентации камеры)
MOUSE_SENSITIVITY = 5.0     # пикселей мыши на 1 градус поворота (подбирается пользователем)
FORWARD_KEY = "w"           # клавиша движения вперёд
TOGGLE_KEY = "f6"           # горячая клавиша старт/стоп
EXIT_KEY = "esc"            # горячая клавиша аварийного выхода
ROBLOX_WINDOW_TITLE = "Roblox"  # подстрока в заголовке окна игры
FOCUS_CHECK = True          # не отправлять ввод, если окно Roblox не в фокусе
LOOP_DELAY = 0.05           # пауза между итерациями цикла (секунды)

# Количество шагов для плавного поворота мыши (чем больше, тем плавнее)
MOUSE_TURN_STEPS = 20

# Клавиши, которые скрипт использует и должен отпускать при очистке
MANAGED_KEYS = ["w", "a", "s", "d"]

# =====================================================================
# ГЛОБАЛЬНОЕ СОСТОЯНИЕ
# =====================================================================

is_active = threading.Event()
toggle_lock = threading.Lock()


def is_roblox_focused():
    """Проверяет, находится ли окно Roblox в фокусе."""
    if not FOCUS_CHECK:
        return True
    try:
        active_window = gw.getActiveWindow()
        if active_window is None:
            return False
        return ROBLOX_WINDOW_TITLE.lower() in active_window.title.lower()
    except Exception:
        return False


def release_all_keys():
    """Безусловно отпускает все управляемые клавиши."""
    for key in MANAGED_KEYS:
        try:
            pydirectinput.keyUp(key)
        except Exception:
            pass


def interruptible_sleep(duration):
    """
    Спит заданное время, но прерывается, если флаг is_active снят.
    Возвращает True, если сон завершился полностью, False — если прерван.
    """
    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        if not is_active.is_set():
            return False
        time.sleep(min(LOOP_DELAY, max(0.0, end_time - time.monotonic())))
    return True


def turn_mouse():
    """Поворот камеры мышью влево на TURN_DEGREES."""
    total_pixels = int(TURN_DEGREES * MOUSE_SENSITIVITY)
    step_pixels = max(1, total_pixels // MOUSE_TURN_STEPS)
    remaining = total_pixels

    for _ in range(MOUSE_TURN_STEPS):
        if not is_active.is_set():
            return
        move = min(step_pixels, remaining)
        if move <= 0:
            break
        if is_roblox_focused():
            pydirectinput.moveRel(-move, 0)
        remaining -= move
        time.sleep(0.01)

    # Остаток, если деление было неточным
    if remaining > 0 and is_active.is_set() and is_roblox_focused():
        pydirectinput.moveRel(-remaining, 0)


def turn_strafe():
    """Обход квадрата через стрейф: A -> S -> D (W уже отработала в основном цикле)."""
    strafe_sequence = ["a", "s", "d"]
    for key in strafe_sequence:
        if not is_active.is_set():
            return
        if is_roblox_focused():
            pydirectinput.keyDown(key)
        completed = interruptible_sleep(LEG_DURATION)
        if is_roblox_focused() or not completed:
            pydirectinput.keyUp(key)
        if not is_active.is_set():
            return


def movement_loop():
    """Основной цикл движения персонажа."""
    while True:
        # Ждём активации через F6
        is_active.wait()

        try:
            while is_active.is_set():
                # --- Шаг 1: Идём прямо ---
                if is_roblox_focused():
                    pydirectinput.keyDown(FORWARD_KEY)

                completed = interruptible_sleep(LEG_DURATION)

                if is_roblox_focused() or not completed:
                    pydirectinput.keyUp(FORWARD_KEY)

                if not is_active.is_set():
                    break

                # --- Шаг 2: Поворот ---
                if TURN_METHOD == "mouse":
                    turn_mouse()
                elif TURN_METHOD == "strafe":
                    turn_strafe()
                else:
                    # Неизвестный метод — останавливаемся
                    print(f"Ошибка: неизвестный TURN_METHOD '{TURN_METHOD}'. Допустимые значения: 'mouse', 'strafe'.")
                    is_active.clear()
                    break

                if not is_active.is_set():
                    break

                # Короткая пауза между итерациями
                interruptible_sleep(LOOP_DELAY)

        finally:
            # Гарантированно отпускаем все клавиши при остановке или ошибке
            release_all_keys()


def on_toggle(event):
    """Обработчик нажатия F6 — переключение старт/стоп."""
    # Защита от дребезга: обрабатываем только нажатие (не отпускание)
    if event.event_type == keyboard.KEY_DOWN:
        with toggle_lock:
            if is_active.is_set():
                is_active.clear()
                print("Ходьба: ВЫКЛ")
            else:
                is_active.set()
                print("Ходьба: ВКЛ")


def on_exit(event):
    """Обработчик нажатия Esc — аварийный выход."""
    if event.event_type == keyboard.KEY_DOWN:
        print("Аварийный выход...")
        is_active.clear()
        release_all_keys()
        keyboard.unhook_all()
        sys.exit(0)


def validate_config():
    """Проверка корректности конфигурации при старте."""
    if TURN_METHOD not in ("mouse", "strafe"):
        print(f"Ошибка: недопустимое значение TURN_METHOD = '{TURN_METHOD}'.")
        print("Допустимые значения: 'mouse' или 'strafe'. Исправьте константу в начале файла.")
        sys.exit(1)


def main():
    """Точка входа."""
    validate_config()

    print("=" * 45)
    print("Скрипт движения по кругу для Roblox запущен.")
    print("F6 — старт/стоп, Esc — выход")
    print(f"Режим поворота: {TURN_METHOD}")
    if TURN_METHOD == "mouse":
        print(f"Чувствительность мыши: {MOUSE_SENSITIVITY} px/градус")
    print("=" * 45)

    # Регистрируем глобальные хоткеи
    keyboard.hook_key(TOGGLE_KEY, on_toggle, suppress=True)
    keyboard.hook_key(EXIT_KEY, on_exit, suppress=True)

    # Запускаем поток движения
    loop_thread = threading.Thread(target=movement_loop, daemon=True)
    loop_thread.start()

    # Основной поток ждёт, чтобы хуки keyboard продолжали работать
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nПринудительное завершение (Ctrl+C)...")
        is_active.clear()
        release_all_keys()
        keyboard.unhook_all()
        sys.exit(0)


if __name__ == "__main__":
    main()
