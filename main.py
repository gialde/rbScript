"""
Roblox: непрерывное движение по кругу через WASD.

Установка:
    pip install pyrobloxbot keyboard

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
    SPRINT_ENABLED     — держать ли Shift (бег).
    CLOCKWISE          — True по часовой, False против.
"""

import sys
import time
import threading

try:
    import pyrobloxbot as bot
except ImportError:
    print("Ошибка: не найден 'pyrobloxbot'.")
    print("Выполните: pip install pyrobloxbot")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("Ошибка: не найден 'keyboard'.")
    print("Выполните: pip install keyboard")
    sys.exit(1)


# =====================================================================
# НАСТРОЙКИ
# =====================================================================

LEG_DURATION = 0.5           # длительность одной стороны восьмиугольника (сек)
STEP_SETTLE_DELAY = 0.15     # пауза между сторонами (сек)
CLOCKWISE = True             # True — по часовой, False — против
SPRINT_ENABLED = False       # держать Shift во время движения (бег)
SPRINT_KEY = "shift"

LOOP_DELAY = 0.05

TOGGLE_KEY = "f6"
EXIT_KEY = "esc"

bot.options.force_focus = True
bot.options.action_cooldown = 0
bot.options.key_press_cooldown = 0


# =====================================================================
# ВОСЬМИУГОЛЬНИК
# =====================================================================
WASD_STEPS_CW = (
    ("w",),
    ("w", "d"),
    ("d",),
    ("s", "d"),
    ("s",),
    ("s", "a"),
    ("a",),
    ("w", "a"),
)
WASD_STEPS_CCW = tuple(reversed(WASD_STEPS_CW))


# =====================================================================
# СОСТОЯНИЕ
# =====================================================================

is_active = threading.Event()
shutdown = threading.Event()
toggle_lock = threading.Lock()
sprint_is_down = False


# =====================================================================
# УПРАВЛЕНИЕ
# =====================================================================

def release_all_keys():
    global sprint_is_down
    for k in ("w", "a", "s", "d"):
        try:
            bot.key_up(k)
        except Exception:
            pass
    if sprint_is_down:
        try:
            bot.key_up(SPRINT_KEY)
        except Exception:
            pass
        sprint_is_down = False


def sprint_on():
    global sprint_is_down
    if not SPRINT_ENABLED or sprint_is_down:
        return
    try:
        bot.key_down(SPRINT_KEY)
        sprint_is_down = True
    except Exception as e:
        print(f"Ошибка Shift: {e}")


def interruptible_wait(duration):
    end = time.monotonic() + duration
    while time.monotonic() < end:
        if not is_active.is_set() or shutdown.is_set():
            return False
        step = min(LOOP_DELAY, max(0.0, end - time.monotonic()))
        if step > 0:
            bot.wait(step)
    return True


def do_step(keys, duration):
    try:
        bot.hold_keyboard_action(*keys, duration=duration)
    except Exception as e:
        print(f"Ошибка ввода: {e}")
        return False
    for k in keys:
        try:
            bot.key_up(k)
        except Exception:
            pass
    return True


# =====================================================================
# ОСНОВНОЙ ЦИКЛ
# =====================================================================

def circle_loop():
    steps = WASD_STEPS_CW if CLOCKWISE else WASD_STEPS_CCW
    direction_name = "по часовой" if CLOCKWISE else "против часовой"

    while not shutdown.is_set():
        is_active.wait(timeout=0.1)
        if shutdown.is_set():
            return
        if not is_active.is_set():
            continue

        print(f"Ходьба запущена ({direction_name}). "
              f"Сторона {LEG_DURATION}с, пауза {STEP_SETTLE_DELAY}с.")

        try:
            while is_active.is_set() and not shutdown.is_set():
                for step_keys in steps:
                    if not is_active.is_set() or shutdown.is_set():
                        break

                    sprint_on()

                    if not do_step(step_keys, LEG_DURATION):
                        is_active.clear()
                        break

                    if STEP_SETTLE_DELAY > 0:
                        if not interruptible_wait(STEP_SETTLE_DELAY):
                            break

                if not is_active.is_set() or shutdown.is_set():
                    break

                interruptible_wait(LOOP_DELAY)

        finally:
            release_all_keys()


# =====================================================================
# ХОТКЕИ
# =====================================================================

def on_toggle(event):
    if event.event_type != keyboard.KEY_DOWN:
        return
    with toggle_lock:
        if is_active.is_set():
            is_active.clear()
            release_all_keys()
            print("Ходьба: ВЫКЛ")
        else:
            is_active.set()
            print("Ходьба: ВКЛ")


def on_exit(event):
    if event.event_type != keyboard.KEY_DOWN:
        return
    print("Аварийный выход...")
    is_active.clear()
    release_all_keys()
    shutdown.set()


# =====================================================================
# ТОЧКА ВХОДА
# =====================================================================

def main():
    print("=" * 60)
    print("Roblox: непрерывное движение по кругу через WASD")
    print("F6 — старт/стоп, Esc — выход, Ctrl+M — failsafe")
    print("=" * 60)
    print(f"Направление: {'по часовой' if CLOCKWISE else 'против часовой'}")
    print(f"Сторона: {LEG_DURATION} сек × 8 сторон")
    print(f"Пауза между сторонами: {STEP_SETTLE_DELAY} сек")
    circle_time = 8 * (LEG_DURATION + STEP_SETTLE_DELAY)
    print(f"Полный круг: ~{circle_time:.2f} сек")
    print(f"Спринт (Shift): {'ВКЛ' if SPRINT_ENABLED else 'ВЫКЛ'}")
    print("=" * 60)

    keyboard.hook_key(TOGGLE_KEY, on_toggle, suppress=True)
    keyboard.hook_key(EXIT_KEY, on_exit, suppress=True)

    t = threading.Thread(target=circle_loop, daemon=True)
    t.start()

    try:
        while not shutdown.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nCtrl+C...")
    finally:
        is_active.clear()
        release_all_keys()
        try:
            keyboard.unhook_all()
        except Exception:
            pass

    print("Завершено.")
    sys.exit(0)


if __name__ == "__main__":
    main()