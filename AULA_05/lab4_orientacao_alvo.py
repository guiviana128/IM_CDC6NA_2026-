import math
# pyrefly: ignore [missing-import]
import pygame

def calcular_orientacao_alvo(x, y, theta, x_alvo, y_alvo, Kp=1.5):
    """
    Calcula o comando de velocidade angular (omega) usando controle proporcional
    para orientar o robo em direcao ao ponto alvo (x_alvo, y_alvo).
    """
    # 1. Calcula o angulo desejado ate o alvo usando math.atan2
    dx = x_alvo - x
    dy = y_alvo - y
    theta_alvo = math.atan2(dy, dx)
    
    # 2. Calcula o erro de orientacao e_theta normalizado em [-pi, pi]
    e_theta = math.atan2(math.sin(theta_alvo - theta), math.cos(theta_alvo - theta))
    
    # 3. Lei de controle proporcional
    omega = Kp * e_theta
    
    return omega

def main():
    print("=" * 60)
    print("EXERCICIO 4: Controlador Proporcional para Atracao ao Alvo")
    print("=" * 60)
    
    casos = [
        {"desc": "Alvo a 45° no primeiro quadrante", "x": 0.0, "y": 0.0, "th": 0.0, "tx": 2.0, "ty": 2.0},
        {"desc": "Alvo atras a esquerda (135°)", "x": 1.0, "y": 1.0, "th": 0.0, "tx": -1.0, "ty": 3.0},
        {"desc": "Alvo quase oposto (Tratamento de descontinuidade +-pi)", "x": 0.0, "y": 0.0, "th": 0.1, "tx": -3.0, "ty": -0.1},
        {"desc": "Robo ja perfeitamente alinhado", "x": 2.0, "y": 3.0, "th": 1.5708, "tx": 2.0, "ty": 6.0},
    ]
    
    for c in casos:
        x, y, th = c["x"], c["y"], c["th"]
        tx, ty = c["tx"], c["ty"]
        th_alvo = math.atan2(ty - y, tx - x)
        e_th = math.atan2(math.sin(th_alvo - th), math.cos(th_alvo - th))
        w = calcular_orientacao_alvo(x, y, th, tx, ty, Kp=1.5)
        
        print(f"\nCaso: {c['desc']}")
        print(f"  Pose Robo: ({x:.2f}, {y:.2f}) | theta = {math.degrees(th):.1f} deg ({th:.4f} rad)")
        print(f"  Posicao Alvo: ({tx:.2f}, {ty:.2f})")
        print(f"  Theta Alvo: {math.degrees(th_alvo):.1f} deg ({th_alvo:.4f} rad)")
        print(f"  Erro e_theta (Normalizado): {math.degrees(e_th):.1f} deg ({e_th:+.4f} rad)")
        print(f"  Comando Proporcional: omega = Kp * e_theta = 1.5 * ({e_th:+.4f}) = {w:+.4f} rad/s")

    # Renderizacao visual
    pygame.init()
    WIDTH, HEIGHT = 900, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 4 - Controlador Proporcional de Orientacao")
    
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_body = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)
    
    screen.fill((240, 243, 246))
    
    title = font_title.render("Exercicio 4: Controlador Proporcional para Atracao e Alinhamento ao Alvo", True, (20, 30, 60))
    screen.blit(title, (30, 20))
    
    # Painel Esquerdo: Simulacao de Campo 2D
    pygame.draw.rect(screen, (255, 255, 255), (30, 65, 520, 510), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (30, 65, 520, 510), 2, border_radius=10)
    
    # Grid cartesiano
    for gx in range(50, 530, 50):
        pygame.draw.line(screen, (235, 240, 245), (gx, 80), (gx, 550), 1)
    for gy in range(80, 560, 50):
        pygame.draw.line(screen, (235, 240, 245), (50, gy), (530, gy), 1)
        
    rx, ry = 180, 380
    r_theta = math.radians(20) # apontando levemente acima do eixo X
    
    tx, ty = 430, 160 # Alvo no canto superior direito
    
    dx_px, dy_px = tx - rx, ty - ry
    # No pygame, Y cresce para baixo, entao no plano matematico dy_math = -(ty - ry)
    theta_alvo_math = math.atan2(-(ty - ry), (tx - rx))
    erro_math = math.atan2(math.sin(theta_alvo_math - r_theta), math.cos(theta_alvo_math - r_theta))
    omega_cmd = 1.5 * erro_math
    
    # Linha tracejada ate o alvo
    pygame.draw.line(screen, (160, 180, 220), (rx, ry), (tx, ty), 2)
    
    # Vetor de orientacao atual do robo (Vermelho)
    v_len = 80
    vx = rx + int(v_len * math.cos(r_theta))
    vy = ry - int(v_len * math.sin(r_theta))
    pygame.draw.line(screen, (220, 50, 50), (rx, ry), (vx, vy), 4)
    pygame.draw.circle(screen, (220, 50, 50), (vx, vy), 5)
    
    # Vetor desejado ate o alvo (Azul)
    dx_norm = math.cos(theta_alvo_math)
    dy_norm = -math.sin(theta_alvo_math)
    dvx = rx + int(v_len * dx_norm)
    dvy = ry + int(v_len * dy_norm)
    pygame.draw.line(screen, (30, 120, 220), (rx, ry), (dvx, dvy), 3)
    
    # Arco do erro angular e_theta
    pygame.draw.arc(screen, (240, 140, 20), (rx - 55, ry - 55, 110, 110), r_theta, theta_alvo_math, 3)
    
    # Desenho do robo
    pygame.draw.circle(screen, (50, 70, 100), (rx, ry), 22)
    pygame.draw.circle(screen, (255, 255, 255), (rx, ry), 22, 2)
    
    # Desenho do Alvo (Target)
    pygame.draw.circle(screen, (40, 180, 80), (tx, ty), 18)
    pygame.draw.circle(screen, (255, 255, 255), (tx, ty), 18, 3)
    pygame.draw.circle(screen, (40, 180, 80), (tx, ty), 6)
    screen.blit(font_title.render("ALVO", True, (20, 120, 40)), (tx - 25, ty - 45))
    
    # Rotulos de angulos
    screen.blit(font_small.render("\u03b8 atual", True, (200, 30, 30)), (vx + 8, vy - 5))
    screen.blit(font_small.render("\u03b8 alvo", True, (20, 100, 200)), (dvx + 8, dvy - 5))
    screen.blit(font_small.render(f"Erro e_\u03b8 = {math.degrees(erro_math):.1f}\u00b0", True, (200, 100, 0)), (rx + 60, ry - 40))
    
    # Painel Direito: Explicacao Matematica e Dados
    pygame.draw.rect(screen, (255, 255, 255), (570, 65, 300, 510), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (570, 65, 300, 510), 2, border_radius=10)
    
    screen.blit(font_title.render("Calculo do Controlador", True, (40, 80, 160)), (585, 80))
    
    # Bloco 1: Formulas
    pygame.draw.rect(screen, (245, 248, 255), (585, 120, 270, 120), border_radius=8)
    pygame.draw.rect(screen, (180, 200, 235), (585, 120, 270, 120), 1, border_radius=8)
    screen.blit(font_body.render("1. \u03b8_alvo = atan2(\u0394y, \u0394x)", True, (30, 30, 60)), (595, 130))
    screen.blit(font_body.render("2. e_\u03b8 = wrapToPi(\u03b8_alvo - \u03b8)", True, (30, 30, 60)), (595, 160))
    screen.blit(font_body.render("3. \u03c9 = Kp \u00b7 e_\u03b8  (Kp = 1.5)", True, (30, 30, 60)), (595, 190))
    
    # Bloco 2: Valores Numericos
    pygame.draw.rect(screen, (240, 255, 245), (585, 255, 270, 175), border_radius=8)
    pygame.draw.rect(screen, (160, 220, 180), (585, 255, 270, 175), 1, border_radius=8)
    screen.blit(font_body.render(f"Pose: ({rx}, {ry})", True, (40, 40, 40)), (595, 265))
    screen.blit(font_body.render(f"Alvo: ({tx}, {ty})", True, (40, 40, 40)), (595, 290))
    screen.blit(font_body.render(f"\u03b8 atual: {math.degrees(r_theta):.1f}\u00b0 ({r_theta:.3f} rad)", True, (180, 40, 40)), (595, 315))
    screen.blit(font_body.render(f"\u03b8 alvo: {math.degrees(theta_alvo_math):.1f}\u00b0 ({theta_alvo_math:.3f} rad)", True, (30, 80, 180)), (595, 340))
    screen.blit(font_body.render(f"e_\u03b8: {math.degrees(erro_math):.1f}\u00b0 ({erro_math:+.3f} rad)", True, (180, 100, 20)), (595, 365))
    screen.blit(font_title.render(f"\u03c9_cmd: {omega_cmd:+.3f} rad/s", True, (20, 130, 40)), (595, 395))
    
    # Beneficios do controle proporcional e normalizacao
    screen.blit(font_small.render("\u2713 Giro sempre pelo menor caminho", True, (80, 80, 80)), (590, 455))
    screen.blit(font_small.render("\u2713 Desacelera o giro ao aproximar do alvo", True, (80, 80, 80)), (590, 480))
    screen.blit(font_small.render("\u2713 Evita sobressinal com ganho Kp ajustado", True, (80, 80, 80)), (590, 505))
    
    pygame.display.flip()
    pygame.image.save(screen, "c:/TEMP/imr/IM_CDC6NA_2026-/AULA_05/print_lab4.png")
    print("\n[OK] Imagem salva: AULA_05/print_lab4.png")
    pygame.quit()

if __name__ == "__main__":
    main()
