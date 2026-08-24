import pygame
import math
import numpy as np

# =========================
# Configurações
# =========================
LARGURA_TELA = 800
ALTURA_TELA = 600
FPS = 60

COR_FUNDO = (30, 30, 30)
COR_ROBO = (0, 180, 255)
COR_DIRECAO = (255, 50, 50)
COR_TRAJETORIA = (100, 200, 100)

VELOCIDADE = 100.0
VELOCIDADE_ANGULAR = math.pi / 2

TEMPO_RETA = 2.0
TEMPO_GIRO = 1.0


class DiffDriveRobot:
    def __init__(self, x, y, theta=0.0, wheelbase=30.0):
        self.x = float(x)
        self.y = float(y)
        self.theta = float(theta)

        self.L = float(wheelbase)

        self.v = 0.0
        self.omega = 0.0

        self.history = []

    def set_direct_velocity(self, v, omega):
        self.v = v
        self.omega = omega

    def update(self, dt):
        # Integração da cinemática diferencial
        self.theta += self.omega * dt

        self.theta = (
            self.theta + math.pi
        ) % (2 * math.pi) - math.pi

        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt

        if (
            len(self.history) == 0
            or np.hypot(
                self.x - self.history[-1][0],
                self.y - self.history[-1][1]
            ) > 5
        ):
            self.history.append(
                (self.x, self.y)
            )

    def draw(self, surface):
        if len(self.history) > 1:
            pygame.draw.lines(
                surface,
                COR_TRAJETORIA,
                False,
                self.history,
                2
            )

        pos = (int(self.x), int(self.y))

        pygame.draw.circle(
            surface,
            COR_ROBO,
            pos,
            15
        )

        frente_x = self.x + 25 * math.cos(self.theta)
        frente_y = self.y + 25 * math.sin(self.theta)

        pygame.draw.line(
            surface,
            COR_DIRECAO,
            pos,
            (int(frente_x), int(frente_y)),
            3
        )


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (LARGURA_TELA, ALTURA_TELA)
    )

    pygame.display.set_caption(
        "Aula 02 - Quadrado em Malha Aberta"
    )

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)

    robot = DiffDriveRobot(
        LARGURA_TELA // 2,
        ALTURA_TELA // 2
    )

    # Máquina de estados
    estado = "RETA"
    contador_lados = 0
    tempo_estado = 0.0

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        tempo_estado += dt

        # =========================
        # Máquina de estados
        # =========================
        if estado == "RETA":

            robot.set_direct_velocity(
                VELOCIDADE,
                0.0
            )

            if tempo_estado >= TEMPO_RETA:
                estado = "GIRO"
                tempo_estado = 0.0

        elif estado == "GIRO":

            robot.set_direct_velocity(
                0.0,
                VELOCIDADE_ANGULAR
            )

            if tempo_estado >= TEMPO_GIRO:
                contador_lados += 1
                tempo_estado = 0.0

                if contador_lados >= 4:
                    estado = "FINAL"

                else:
                    estado = "RETA"

        elif estado == "FINAL":

            robot.set_direct_velocity(
                0.0,
                0.0
            )

        robot.update(dt)

        # =========================
        # Tela
        # =========================
        screen.fill(COR_FUNDO)

        robot.draw(screen)

        info = [
            "EXERCICIO 2 - QUADRADO",
            f"Estado: {estado}",
            f"Lado atual: {contador_lados}/4",
            f"X = {robot.x:.2f}",
            f"Y = {robot.y:.2f}",
            f"Theta = {math.degrees(robot.theta):.2f} graus",
            "",
            "Reta: 2 segundos",
            "Giro: 1 segundo",
        ]

        for i, texto in enumerate(info):
            rendered = font.render(
                texto,
                True,
                (220, 220, 220)
            )

            screen.blit(
                rendered,
                (15, 15 + i * 20)
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
