import pygame
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lab 2 - Ackermann")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)

L = 2.0
MAX_PHI = math.radians(30)
SCALE = 30

x = WIDTH / 2
y = HEIGHT / 2
theta = 0.0

v = 0.0
phi = 0.0

trajectory = []

running = True

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                phi = 0.0

            if event.key == pygame.K_r:
                x = WIDTH / 2
                y = HEIGHT / 2
                theta = 0.0
                v = 0.0
                phi = 0.0
                trajectory.clear()

    keys = pygame.key.get_pressed()

    if keys[pygame.K_UP]:
        v += 0.8 * dt

    if keys[pygame.K_DOWN]:
        v -= 0.8 * dt

    if keys[pygame.K_LEFT]:
        phi += math.radians(40) * dt

    if keys[pygame.K_RIGHT]:
        phi -= math.radians(40) * dt

    v = max(-5.0, min(5.0, v))
    phi = max(-MAX_PHI, min(MAX_PHI, phi))

    omega = (v / L) * math.tan(phi)

    theta += omega * dt

    x += v * SCALE * math.cos(theta) * dt
    y -= v * SCALE * math.sin(theta) * dt

    trajectory.append((int(x), int(y)))

    if abs(phi) > 0.0001:
        radius = L / math.tan(phi)
    else:
        radius = float("inf")

    screen.fill((245, 245, 245))

    if len(trajectory) > 1:
        pygame.draw.lines(screen, (70, 120, 220), False, trajectory, 3)

    car_length = 50
    car_width = 30

    surface = pygame.Surface((car_length, car_width), pygame.SRCALPHA)

    pygame.draw.rect(surface, (220, 80, 60),
                     (0, 0, car_length, car_width), border_radius=5)

    rotated = pygame.transform.rotate(surface, math.degrees(theta))
    rect = rotated.get_rect(center=(x, y))
    screen.blit(rotated, rect)

    lines = [
        f"Velocidade v: {v:.2f} m/s",
        f"Esterco phi: {math.degrees(phi):.2f} graus",
        f"Velocidade angular: {omega:.3f} rad/s",
        f"Entre-eixos L: {L:.1f} m",
        f"Raio R: {'infinito' if math.isinf(radius) else f'{abs(radius):.2f} m'}",
        "Setas: velocidade e esterco | ESPACO: centralizar | R: reiniciar"
    ]

    for i, text in enumerate(lines):
        surface_text = font.render(text, True, (20, 20, 20))
        screen.blit(surface_text, (20, 20 + i * 30))

    pygame.display.flip()

pygame.quit()
