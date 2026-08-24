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


class DiffDriveRobot:
    def __init__(self, x, y, theta=0.0, wheelbase=30.0, radius=15.0):
        # Estado do robô
        self.x = float(x)
        self.y = float(y)
        self.theta = float(theta)

        # Parâmetros físicos
        self.L = float(wheelbase)
        self.radius = float(radius)

        # Velocidades
        self.v = 0.0
        self.omega = 0.0

        # Histórico
        self.history = []

    def set_wheel_velocities(self, v_left, v_right):
        """Converte velocidades das rodas em v e omega."""
        self.v = (v_right + v_left) / 2.0
        self.omega = (v_right - v_left) / self.L

    def update(self, dt):
        """Atualiza a pose usando a cinemática diferencial."""
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
            self.history.append((self.x, self.y))

            if len(self.history) > 500:
                self.history.pop(0)

    def draw(self, surface):
        # Rastro
        if len(self.history) > 1:
            pygame.draw.lines(
                surface,
                COR_TRAJETORIA,
                False,
                self.history,
                2
            )

        # Corpo
        pos = (int(self.x), int(self.y))

        pygame.draw.circle(
            surface,
            COR_ROBO,
            pos,
            int(self.radius)
        )

        # Direção
        frente_x = self.x + (self.radius + 10) * math.cos(self.theta)
        frente_y = self.y + (self.radius + 10) * math.sin(self.theta)

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
        "Aula 02 - Controle por Rodas"
    )

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)

    robot = DiffDriveRobot(
        x=LARGURA_TELA // 2,
        y=ALTURA_TELA // 2
    )

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # =========================
        # Controle das rodas
        # =========================
        keys = pygame.key.get_pressed()

        v_left = 0.0
        v_right = 0.0

        VELOCIDADE_RODA = 100.0

        # Roda esquerda
        if keys[pygame.K_w]:
            v_left = VELOCIDADE_RODA

        if keys[pygame.K_s]:
            v_left = -VELOCIDADE_RODA

        # Roda direita
        if keys[pygame.K_i]:
            v_right = VELOCIDADE_RODA

        if keys[pygame.K_k]:
            v_right = -VELOCIDADE_RODA

        # Aplica as velocidades individuais
        robot.set_wheel_velocities(
            v_left,
            v_right
        )

        robot.update(dt)

        # =========================
        # Renderização
        # =========================
        screen.fill(COR_FUNDO)

        robot.draw(screen)

        info_txt = [
            f"X: {robot.x:.1f} | Y: {robot.y:.1f}",
            f"Theta: {math.degrees(robot.theta):.1f} graus",
            f"v = {robot.v:.1f} px/s",
            f"omega = {robot.omega:.2f} rad/s",
            "",
            "W/S = roda esquerda",
            "I/K = roda direita",
            "W + I = frente",
            "S + K = tras",
            "W + K = gira em torno do proprio eixo",
            "I + S = gira em torno do proprio eixo",
        ]

        for i, txt in enumerate(info_txt):
            rendered = font.render(
                txt,
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
