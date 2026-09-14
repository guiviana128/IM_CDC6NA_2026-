import pygame
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lab 1 - Validador de Pose")

clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)

SCALE = 100
ORIGIN_X = 200
ORIGIN_Y = 450

commands = [
    (4.0, 0.5, 0.0),
    (2.0, 0.0, 0.7854),
    (3.0, 0.4, 0.0)
]

x_theory = 0.0
y_theory = 0.0
theta_theory = 0.0

for duration, v, omega in commands:
    if omega == 0:
        x_theory += v * math.cos(theta_theory) * duration
        y_theory += v * math.sin(theta_theory) * duration
    else:
        theta_theory += omega * duration

print("Pose final teorica:")
print(f"x = {x_theory:.4f} m")
print(f"y = {y_theory:.4f} m")
print(f"theta = {theta_theory:.4f} rad")
print(f"theta = {math.degrees(theta_theory):.2f} graus")

x = 0.0
y = 0.0
theta = 0.0

command_index = 0
command_time = 0.0
trajectory = []

running = True
finished = False

while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if command_index < len(commands):
        duration, v, omega = commands[command_index]

        remaining = duration - command_time
        step = min(dt, remaining)

        x += v * math.cos(theta) * step
        y += v * math.sin(theta) * step
        theta += omega * step

        command_time += step
        trajectory.append((x, y))

        if command_time >= duration:
            command_index += 1
            command_time = 0.0

    elif not finished:
        finished = True

        print("\nPose final simulada:")
        print(f"x = {x:.4f} m")
        print(f"y = {y:.4f} m")
        print(f"theta = {theta:.4f} rad")
        print(f"theta = {math.degrees(theta):.2f} graus")

    screen.fill((245, 245, 245))

    pygame.draw.line(screen, (180, 180, 180), (0, ORIGIN_Y), (WIDTH, ORIGIN_Y), 2)
    pygame.draw.line(screen, (180, 180, 180), (ORIGIN_X, 0), (ORIGIN_X, HEIGHT), 2)

    if len(trajectory) > 1:
        points = []
        for px, py in trajectory:
            sx = ORIGIN_X + int(px * SCALE)
            sy = ORIGIN_Y - int(py * SCALE)
            points.append((sx, sy))
        pygame.draw.lines(screen, (50, 100, 220), False, points, 3)

    robot_x = ORIGIN_X + int(x * SCALE)
    robot_y = ORIGIN_Y - int(y * SCALE)

    pygame.draw.circle(screen, (220, 70, 70), (robot_x, robot_y), 15)

    direction_x = robot_x + int(30 * math.cos(theta))
    direction_y = robot_y - int(30 * math.sin(theta))

    pygame.draw.line(screen, (0, 0, 0), (robot_x, robot_y),
                     (direction_x, direction_y), 4)

    text1 = font.render(f"x: {x:.2f} m   y: {y:.2f} m", True, (20, 20, 20))
    text2 = font.render(f"Theta: {math.degrees(theta):.1f} graus", True, (20, 20, 20))

    screen.blit(text1, (20, 20))
    screen.blit(text2, (20, 50))

    pygame.display.flip()

pygame.quit()
