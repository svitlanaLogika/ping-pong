from pygame import *
import socket
import json
from threading import Thread
import os

# ---PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080)) # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)

# === ЗАВАНТАЖЕННЯ ЗОБРАЖЕНЬ ===
# Функція для безпечного завантаження зображень з обробкою помилок
def load_image_safe(path, size=None):
    try:
        img = image.load(path)
        if size:
            img = transform.scale(img, size)
        return img.convert_alpha()  # convert_alpha() для прозорості та швидкості
    except:
        print(f"⚠️ Не вдалося завантажити {path}")
        return None

print("🎨 Завантажую зображення...")

# === ЗАВАНТАЖЕННЯ ФОНОВИХ ЗОБРАЖЕНЬ ===
# Фон основної гри
game_bg = load_image_safe('images/backgrounds/game_bg.jpg', (WIDTH, HEIGHT))
if game_bg is None:
    # Якщо не вдалося завантажити, використовуємо старий фон
    try:
        game_bg = image.load('images/backgrounds/game_bg.jpg')
        game_bg = transform.scale(game_bg, (WIDTH, HEIGHT))
    except:
        print("⚠️ Фонове зображення не знайдено")
        game_bg = None

# Фон екрану перемоги
win_bg = load_image_safe('images/backgrounds/win_bg.jpg', (800, 600))

# === ЗАВАНТАЖЕННЯ ІГРОВИХ ЕЛЕМЕНТІВ ===
# М'яч - тепер це зображення замість білого кола
ball_img = load_image_safe('images/game_elements/ball.png', (20, 20))

# Ракетка гравця 1 (ліва)
paddle1_img = load_image_safe('images/game_elements/paddle1.png', (20, 100))

# Ракетка гравця 2 (права)
paddle2_img = load_image_safe('images/game_elements/paddle2.png', (20, 100))

print("✅ Завантаження зображень завершено!")

# --- ЗВУКИ ---
# (Тут можна додати завантаження звукових файлів)

# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    # === ВІДОБРАЖЕННЯ ФОНУ ===
    if game_bg:
        screen.blit(game_bg, (0, 0))
    else:
        screen.fill((30, 30, 30))  # Темний фон як резерв

    # === ЕКРАН ВІДЛІКУ ===
    if "countdown" in game_state and game_state["countdown"] > 0:
        countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue  # Не малюємо гру до завершення відліку

    # === ЕКРАН ПЕРЕМОГИ ===
    if "winner" in game_state and game_state["winner"] is not None:
        # Використовуємо спеціальний фон для перемоги або темний фон
        if win_bg:
            screen.blit(win_bg, (0, 0))
        else:
            screen.fill((20, 20, 20))

        if you_winner is None:  # Встановлюємо тільки один раз
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False

        if you_winner:
            text = "Ти переміг!"
        else:
            text = "Пощастить наступним разом!"

        win_text = font_win.render(text, True, (255, 215, 0))
        text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(win_text, text_rect)

        text = font_win.render('К - рестарт', True, (255, 215, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
        screen.blit(text, text_rect)

        display.update()
        continue  # Блокує гру після перемоги

    # === ОСНОВНА ГРА ===
    if game_state:
        # === МАЛЮВАННЯ РАКЕТОК ===
        # Ліва ракетка (гравець 0)
        if paddle1_img:
            screen.blit(paddle1_img, (20, game_state['paddles']['0']))
        else:
            draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))

        # Права ракетка (гравець 1)
        if paddle2_img:
            screen.blit(paddle2_img, (WIDTH - 40, game_state['paddles']['1']))
        else:
            draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))

        # === МАЛЮВАННЯ М'ЯЧА ===
        if ball_img:
            screen.blit(ball_img, (game_state['ball']['x'] - 10, game_state['ball']['y'] - 10))
        else:
            draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)

        # === МАЛЮВАННЯ РАХУНКУ ===
        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 -25, 20))

        # === ЗВУКОВІ ПОДІЇ (БЕЗ ВІЗУАЛЬНИХ ЕФЕКТІВ) ===
        if game_state['sound_event']:
            if game_state['sound_event'] == 'wall_hit':
                # звук відбиття м'ячика від стін
                pass
            if game_state['sound_event'] == 'platform_hit':
                # звук відбиття м'ячика від платформи
                pass

    else:
        # === ЕКРАН ОЧІКУВАННЯ ===
        waiting_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
        screen.blit(waiting_text, (WIDTH // 2 - 125, HEIGHT // 2))

    display.update()
    clock.tick(60)

    # Управління (без змін)
    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")