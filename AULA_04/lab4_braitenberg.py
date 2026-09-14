import pygame
import math

pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lab 4 - Braitenberg")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)

x = 150.0
y = 400.0
theta = 0.0

obstacle_x = 700
obstacle_y = 470
obstacle_radius = 50

v0 = 50.0
alpha = 90.0
d_max = 250.0
wheel_base = 50.0

trajectory = []

def distance_sensor(sensor_angle):
    angle = theta + sensor_angle
    best_distance = d_max

    for distance in range(1, int(d_max)):
        ray_x = x + math.cos(angle) * distance
        ray_y = y + math.sin(angle) * distance

        obstacle_distance = math.hypot(
            ray_x - obstacle_x,
            ray_y - obstacle_y
        )

        if obstacle_distance <= obstacle_radius:
            best_distance = distance
            break

    return best_distance

running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                x = 150
                y = 400
                theta = 0
                trajectory.clear()

    d_esq = distance_sensor(-math.radians(30))
    d_dir = distance_sensor(math.radians(30))

    vL = v0 + alpha * (1.0 - d_esq / d_max)
    vR = v0 + alpha * (1.0 - d_dir / d_max)

    v = (vL + vR) / 2
    omega = (vL - vR) / wheel_base

    theta += omega * dt

    x += v * math.cos(theta) * dt
    y += v * math.sin(theta) * dt

    trajectory.append((int(x), int(y)))

    screen.fill((245, 245, 245))

    pygame.draw.circle(screen, (80, 80, 80),
                       (obstacle_x, obstacle_y), obstacle_radius)

    if len(trajectory) > 1:
        pygame.draw.lines(screen, (80, 130, 220), False, trajectory, 2)

    left_angle = theta - math.radians(30)
    right_angle = theta + math.radians(30)

    left_end = (
        x + d_esq * math.cos(left_angle),
        y + d_esq * math.sin(left_angle)
    )

    right_end = (
        x + d_dir * math.cos(right_angle),
        y + d_dir * math.sin(right_angle)
    )

    pygame.draw.line(screen, (0, 160, 0), (x, y), left_end, 2)
    pygame.draw.line(screen, (200, 80, 30), (x, y), right_end, 2)

    pygame.draw.circle(screen, (220, 60, 60), (int(x), int(y)), 18)

    front = (
        x + math.cos(theta) * 30,
        y + math.sin(theta) * 30
    )

    pygame.draw.line(screen, (0, 0, 0), (x, y), front, 4)

    info = [
        f"d_esq: {d_esq:.1f} px",
        f"d_dir: {d_dir:.1f} px",
        f"vL: {vL:.1f} px/s",
        f"vR: {vR:.1f} px/s",
        "Conexoes diretas: sensor esquerdo -> roda esquerda",
        "sensor direito -> roda direita",
        "R = reiniciar"
    ]

    for i, line in enumerate(info):
        text = font.render(line, True, (20, 20, 20))
        screen.blit(text, (20, 20 + i * 28))

    pygame.display.flip()

pygame.quit()
