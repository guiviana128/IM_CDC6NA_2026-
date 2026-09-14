import pygame
import numpy as np
import math

pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lab 3 - Filtro Sensorial")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

robot_x = 500
robot_y = 400

MAX_DISTANCE = 200.0

angles = np.linspace(-math.pi / 2, math.pi / 2, 7)

real_distances = [
    150,
    80,
    5,
    130,
    210,
    175,
    195
]

raw_values = []
filtered_values = []

timer = 0

def update_sensor():
    raw_values.clear()
    filtered_values.clear()

    for distance in real_distances:
        noisy = distance + np.random.normal(0, 5.0)

        raw_values.append(noisy)

        if noisy < 10.0:
            filtered_values.append(None)
        elif noisy > 200.0:
            filtered_values.append(200.0)
        else:
            filtered_values.append(noisy)

update_sensor()

running = True

while running:
    dt = clock.tick(60) / 1000.0
    timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if timer >= 0.5:
        timer = 0
        update_sensor()

    screen.fill((245, 245, 245))

    pygame.draw.circle(screen, (220, 70, 60), (robot_x, robot_y), 20)

    for i, angle in enumerate(angles):
        filtered = filtered_values[i]

        if filtered is None:
            draw_distance = 10
            color = (220, 60, 60)
        else:
            draw_distance = filtered
            color = (50, 150, 70)

        end_x = robot_x + draw_distance * math.sin(angle)
        end_y = robot_y - draw_distance * math.cos(angle)

        pygame.draw.line(screen, color, (robot_x, robot_y),
                         (end_x, end_y), 3)

        pygame.draw.circle(screen, color, (int(end_x), int(end_y)), 5)

    title = font.render("Sensor | Distancia bruta | Distancia filtrada",
                        True, (0, 0, 0))

    screen.blit(title, (20, 20))

    for i in range(7):
        raw = raw_values[i]
        filtered = filtered_values[i]

        if filtered is None:
            filtered_text = "DESCARTADA"
        else:
            filtered_text = f"{filtered:.2f} px"

        text = f"Feixe {i + 1}: {raw:.2f} px  ->  {filtered_text}"

        rendered = font.render(text, True, (20, 20, 20))
        screen.blit(rendered, (20, 60 + i * 30))

    pygame.display.flip()

pygame.quit()
