import pygame
import math

pygame.init()

WIDTH, HEIGHT = 1100, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Exercicio 5 - Centralizacao em Corredor")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

TOP_WALL = 150
BOTTOM_WALL = 500

x = 100.0
y = 250.0
theta = 0.0

v = 40.0
Kp = 0.01

trajectory = []

running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                x = 100
                y = 250
                theta = 0
                trajectory.clear()

    d_esq = y - TOP_WALL
    d_dir = BOTTOM_WALL - y

    erro = d_esq - d_dir
    omega = Kp * erro

    theta -= omega * dt

    x += v * math.cos(theta) * dt
    y += v * math.sin(theta) * dt

    if y < TOP_WALL + 10:
        y = TOP_WALL + 10

    if y > BOTTOM_WALL - 10:
        y = BOTTOM_WALL - 10

    if x > WIDTH:
        x = 0
        trajectory.clear()

    trajectory.append((int(x), int(y)))

    screen.fill((245, 245, 245))

    pygame.draw.line(screen, (40, 40, 40),
                     (0, TOP_WALL), (WIDTH, TOP_WALL), 8)

    pygame.draw.line(screen, (40, 40, 40),
                     (0, BOTTOM_WALL), (WIDTH, BOTTOM_WALL), 8)

    center_y = (TOP_WALL + BOTTOM_WALL) // 2

    pygame.draw.line(screen, (180, 180, 180),
                     (0, center_y), (WIDTH, center_y), 1)

    if len(trajectory) > 1:
        pygame.draw.lines(screen, (60, 120, 220), False, trajectory, 2)

    pygame.draw.line(screen, (0, 160, 0), (x, y), (x, TOP_WALL), 2)
    pygame.draw.line(screen, (200, 80, 30), (x, y), (x, BOTTOM_WALL), 2)

    pygame.draw.circle(screen, (220, 60, 60), (int(x), int(y)), 17)

    front = (
        x + math.cos(theta) * 30,
        y + math.sin(theta) * 30
    )

    pygame.draw.line(screen, (0, 0, 0), (x, y), front, 4)

    info = [
        f"d_esq: {d_esq:.2f} px",
        f"d_dir: {d_dir:.2f} px",
        f"Erro: {erro:.2f}",
        f"Omega: {omega:.3f}",
        f"Kp: {Kp}",
        f"v: {v:.1f} px/s",
        "R = reiniciar"
    ]

    for i, line in enumerate(info):
        text = font.render(line, True, (20, 20, 20))
        screen.blit(text, (20, 20 + i * 27))

    pygame.display.flip()

pygame.quit()
