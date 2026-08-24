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
COR_ALVO = (255, 200, 0)

# Ganhos do controlador
K_LINEAR = 1.0
K_ANGULAR = 3.0

# Velocidade máxima
V_MAX = 120.0
OMEGA_MAX = 3.0

# Tolerância para chegada
TOLERANCIA = 10.0


class DiffDriveRobot:
    def __init__(
        self,
        x,
        y,
        theta=0.0,
        wheelbase=30.0,
        radius=15.0
    ):
        self.x = float(x)
        self.y = float(y)
        self.theta = float(theta)

        self.L = float(wheelbase)
        self.radius = float(radius)

        self.v = 0.0
        self.omega = 0.0

        self.history = []

    def set_direct_velocity(self, v, omega):
        self.v = v
        self.omega = omega

    def update(self, dt):
        self.theta += self.omega * dt

        self.theta = (
            self.theta + math.pi
        ) % (2 * math.pi) - math.pi

        self.x += (
            self.v
            * math.cos(self.theta)
            * dt
        )

        self.y += (
            self.v
            * math.sin(self.theta)
            * dt
        )

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

            if len(self.history) > 1000:
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
        frente_x = self.x + 25 * math.cos(self.theta)
        frente_y = self.y + 25 * math.sin(self.theta)

        pygame.draw.line(
            surface,
            COR_DIRECAO,
            pos,
            (int(frente_x), int(frente_y)),
            3
        )


def limitar(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def erro_angular(angulo):
    """
    Mantém o erro angular no intervalo [-pi, pi].
    """
    return (
        angulo + math.pi
    ) % (2 * math.pi) - math.pi


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (LARGURA_TELA, ALTURA_TELA)
    )

    pygame.display.set_caption(
        "Aula 02 - Go-To-Goal"
    )

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14)

    robot = DiffDriveRobot(
        LARGURA_TELA // 2,
        ALTURA_TELA // 2
    )

    # Não existe objetivo inicialmente
    target = None

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        # =========================
        # Eventos
        # =========================
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # Clique esquerdo define novo objetivo
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                target = event.pos

        # =========================
        # Controlador Go-To-Goal
        # =========================
        if target is not None:

            dx = target[0] - robot.x
            dy = target[1] - robot.y

            distancia = math.hypot(dx, dy)

            # Verifica se chegou
            if distancia < TOLERANCIA:

                robot.set_direct_velocity(
                    0.0,
                    0.0
                )

            else:
                # Ângulo que aponta para o objetivo
                theta_desejado = math.atan2(
                    dy,
                    dx
                )

                # Erro de orientação
                erro_theta = erro_angular(
                    theta_desejado - robot.theta
                )

                # Controle proporcional
                v_cmd = K_LINEAR * distancia

                omega_cmd = (
                    K_ANGULAR
                    * erro_theta
                )

                # Limitação das velocidades
                v_cmd = limitar(
                    v_cmd,
                    0.0,
                    V_MAX
                )

                omega_cmd = limitar(
                    omega_cmd,
                    -OMEGA_MAX,
                    OMEGA_MAX
                )

                robot.set_direct_velocity(
                    v_cmd,
                    omega_cmd
                )

        else:
            robot.set_direct_velocity(
                0.0,
                0.0
            )

        # Atualiza robô
        robot.update(dt)

        # =========================
        # Renderização
        # =========================
        screen.fill(COR_FUNDO)

        robot.draw(screen)

        # Desenha objetivo
        if target is not None:

            pygame.draw.circle(
                screen,
                COR_ALVO,
                target,
                8
            )

            pygame.draw.circle(
                screen,
                COR_ALVO,
                target,
                15,
                2
            )

        # =========================
        # Telemetria
        # =========================
        info = [
            "EXERCICIO 3 - GO-TO-GOAL",
            "Clique com o botao esquerdo para escolher o alvo.",
            f"X = {robot.x:.1f}",
            f"Y = {robot.y:.1f}",
            f"Theta = {math.degrees(robot.theta):.1f} graus",
            f"v = {robot.v:.1f} px/s",
            f"omega = {robot.omega:.2f} rad/s",
        ]

        if target is not None:

            distancia = math.hypot(
                target[0] - robot.x,
                target[1] - robot.y
            )

            info.append(
                f"Distancia ao alvo = {distancia:.1f} px"
            )

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
