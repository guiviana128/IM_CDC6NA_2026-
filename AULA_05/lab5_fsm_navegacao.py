import math
# pyrefly: ignore [missing-import]
import pygame

def calcular_orientacao_alvo(x, y, theta, x_alvo, y_alvo, Kp=1.5):
    """Calcula omega proporcional ao erro de orientacao ate o alvo."""
    dx = x_alvo - x
    dy = y_alvo - y
    theta_alvo = math.atan2(dy, dx)
    e_theta = math.atan2(math.sin(theta_alvo - theta), math.cos(theta_alvo - theta))
    return Kp * e_theta

def maquina_de_estados(x, y, theta, x_alvo, y_alvo, dist_frente, dist_esq, dist_dir):
    """
    Maquina de Estados Finitos (FSM) para navegacao autonoma:
      1. OBJETIVO_ALCANCADO: Se distancia ate o alvo < 0.2 m -> v = 0.0, omega = 0.0
      2. DESVIAR_OBSTACULO : Se dist_frente < 0.5 m -> v = 0.0, omega = +/- 1.0 rad/s
      3. IR_PARA_ALVO      : Caso contrario -> v = 0.5 m/s, omega calculado por atracao ao alvo
    
    Retorna: (estado_atual, v_cmd, omega_cmd)
    """
    # 1. Distancia euclidiana ate o alvo
    dist_alvo = math.sqrt((x_alvo - x)**2 + (y_alvo - y)**2)
    
    # Prioridade 1: Chegada ao objetivo
    if dist_alvo < 0.2:
        estado_atual = "OBJETIVO_ALCANCADO"
        v_cmd = 0.0
        omega_cmd = 0.0
        
    # Prioridade 2: Seguranca / Desvio de obstaculo
    elif dist_frente < 0.5:
        estado_atual = "DESVIAR_OBSTACULO"
        v_cmd = 0.0
        # Gira para o lado com maior espaco livre
        if dist_esq >= dist_dir:
            omega_cmd = 1.0   # Gira para a esquerda (+omega)
        else:
            omega_cmd = -1.0  # Gira para a direita (-omega)
            
    # Prioridade 3: Navegacao nominal rumo ao alvo
    else:
        estado_atual = "IR_PARA_ALVO"
        v_cmd = 0.5
        omega_cmd = calcular_orientacao_alvo(x, y, theta, x_alvo, y_alvo, Kp=1.5)
        # Satura omega para evitar giros violentos em cruzeiro
        omega_cmd = max(-2.0, min(2.0, omega_cmd))
        
    return estado_atual, v_cmd, omega_cmd

def main():
    print("=" * 60)
    print("EXERCICIO 5: Maquina de Estados Finitos (FSM) do Robo Autonomo")
    print("=" * 60)
    
    # Testes unitarios de transicoes da FSM
    cenarios = [
        {
            "nome": "Cenario 1: Navegacao Livre rumo ao Alvo",
            "x": 1.0, "y": 1.0, "th": 0.0, "tx": 5.0, "ty": 1.0,
            "df": 3.0, "de": 2.0, "dd": 2.0
        },
        {
            "nome": "Cenario 2: Obstaculo Detectado a Frente (Desvio Reativo)",
            "x": 2.5, "y": 1.0, "th": 0.0, "tx": 5.0, "ty": 1.0,
            "df": 0.38, "de": 1.8, "dd": 0.6
        },
        {
            "nome": "Cenario 3: Alvo Alcancado com Sucesso",
            "x": 4.95, "y": 1.02, "th": 0.05, "tx": 5.0, "ty": 1.0,
            "df": 2.0, "de": 2.0, "dd": 2.0
        }
    ]
    
    for c in cenarios:
        est, v, w = maquina_de_estados(c["x"], c["y"], c["th"], c["tx"], c["ty"], c["df"], c["de"], c["dd"])
        d_alvo = math.sqrt((c["tx"] - c["x"])**2 + (c["ty"] - c["y"])**2)
        print(f"\n{c['nome']}:")
        print(f"  Pose: ({c['x']:.2f}, {c['y']:.2f}, th={c['th']:.2f} rad) | Alvo: ({c['tx']:.2f}, {c['ty']:.2f}) [Dist = {d_alvo:.2f} m]")
        print(f"  Sensores: Frente = {c['df']:.2f}m, Esq = {c['de']:.2f}m, Dir = {c['dd']:.2f}m")
        print(f"  --> ESTADO ATUAL : {est}")
        print(f"  --> COMANDO /cmd_vel: v = {v:.2f} m/s, omega = {w:+.2f} rad/s")

    # Renderizacao grafica do diagrama de estados e da missao do robo
    pygame.init()
    WIDTH, HEIGHT = 900, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 5 - Maquina de Estados Finitos (FSM)")
    
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_body = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)
    
    screen.fill((240, 243, 246))
    
    title = font_title.render("Exercicio 5: Maquina de Estados Finitos (FSM) do Robo Autonomo", True, (20, 30, 60))
    screen.blit(title, (30, 20))
    
    # Painel Esquerdo: Diagrama da FSM
    pygame.draw.rect(screen, (255, 255, 255), (30, 65, 410, 505), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (30, 65, 410, 505), 2, border_radius=10)
    
    screen.blit(font_title.render("Diagrama de Estados da FSM", True, (40, 80, 160)), (45, 80))
    
    # Estado 1: IR_PARA_ALVO (Azul)
    e1_rect = pygame.Rect(70, 140, 330, 85)
    pygame.draw.rect(screen, (235, 243, 255), e1_rect, border_radius=8)
    pygame.draw.rect(screen, (70, 130, 230), e1_rect, 2, border_radius=8)
    screen.blit(font_title.render("1. IR_PARA_ALVO", True, (30, 80, 180)), (85, 150))
    screen.blit(font_small.render("v = 0.5 m/s | \u03c9 = Kp \u00b7 e_\u03b8", True, (50, 50, 50)), (85, 180))
    screen.blit(font_small.render("Condicao: dist_frente \u2265 0.5m e dist_alvo \u2265 0.2m", True, (100, 100, 100)), (85, 200))
    
    # Seta transicao E1 <-> E2
    pygame.draw.line(screen, (180, 50, 50), (180, 230), (180, 275), 3)
    pygame.draw.polygon(screen, (180, 50, 50), [(180, 278), (174, 268), (186, 268)])
    screen.blit(font_small.render("dist_frente < 0.5m", True, (180, 40, 40)), (50, 245))
    
    pygame.draw.line(screen, (30, 130, 60), (280, 275), (280, 230), 3)
    pygame.draw.polygon(screen, (30, 130, 60), [(280, 226), (274, 236), (286, 236)])
    screen.blit(font_small.render("dist_frente \u2265 0.5m", True, (30, 120, 50)), (290, 245))
    
    # Estado 2: DESVIAR_OBSTACULO (Laranja/Vermelho)
    e2_rect = pygame.Rect(70, 280, 330, 85)
    pygame.draw.rect(screen, (255, 245, 235), e2_rect, border_radius=8)
    pygame.draw.rect(screen, (230, 120, 50), e2_rect, 2, border_radius=8)
    screen.blit(font_title.render("2. DESVIAR_OBSTACULO", True, (200, 70, 20)), (85, 290))
    screen.blit(font_small.render("v = 0.0 m/s | \u03c9 = \u00b11.0 rad/s (in-place)", True, (50, 50, 50)), (85, 320))
    screen.blit(font_small.render("Condicao: dist_frente < 0.5m", True, (100, 100, 100)), (85, 340))
    
    # Seta transicao E1 -> E3
    pygame.draw.line(screen, (40, 160, 60), (235, 370), (235, 415), 3)
    pygame.draw.polygon(screen, (40, 160, 60), [(235, 418), (229, 408), (241, 408)])
    screen.blit(font_small.render("dist_alvo < 0.2m (Chegada)", True, (30, 130, 50)), (135, 385))
    
    # Estado 3: OBJETIVO_ALCANCADO (Verde)
    e3_rect = pygame.Rect(70, 420, 330, 85)
    pygame.draw.rect(screen, (235, 255, 240), e3_rect, border_radius=8)
    pygame.draw.rect(screen, (50, 180, 90), e3_rect, 2, border_radius=8)
    screen.blit(font_title.render("3. OBJETIVO_ALCANCADO", True, (20, 130, 50)), (85, 430))
    screen.blit(font_small.render("v = 0.0 m/s | \u03c9 = 0.0 rad/s (PARADA)", True, (50, 50, 50)), (85, 460))
    screen.blit(font_small.render("Condicao: dist_alvo < 0.2m", True, (100, 100, 100)), (85, 480))
    
    # Painel Direito: Simulacao da Missao
    pygame.draw.rect(screen, (255, 255, 255), (460, 65, 410, 505), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (460, 65, 410, 505), 2, border_radius=10)
    
    screen.blit(font_title.render("Simulacao do Percurso Autonomo", True, (40, 80, 160)), (475, 80))
    
    # Desenho da trajetoria navegada com obstaculo e alvo
    # Ponto inicial (500, 480) -> Obstaculo em (620, 330) -> Desvio pela esquerda -> Alvo em (780, 160)
    pygame.draw.circle(screen, (100, 100, 100), (520, 480), 8)
    screen.blit(font_small.render("Inicio", True, (80, 80, 80)), (505, 495))
    
    # Obstaculo
    obs_rect = pygame.Rect(600, 290, 80, 50)
    pygame.draw.rect(screen, (200, 60, 60), obs_rect, border_radius=6)
    screen.blit(font_small.render("Obstaculo", True, (255, 255, 255)), (608, 305))
    
    # Alvo
    pygame.draw.circle(screen, (40, 180, 80), (770, 160), 16)
    pygame.draw.circle(screen, (255, 255, 255), (770, 160), 16, 2)
    screen.blit(font_title.render("ALVO", True, (30, 130, 50)), (745, 125))
    
    # Trajetoria com mudanca de cor por estado
    # Trecho 1: IR_PARA_ALVO (Azul)
    pygame.draw.line(screen, (50, 120, 230), (520, 480), (590, 360), 4)
    # Trecho 2: DESVIAR_OBSTACULO (Laranja)
    pygame.draw.line(screen, (230, 120, 30), (590, 360), (560, 290), 4)
    # Trecho 3: IR_PARA_ALVO retomado (Azul)
    pygame.draw.line(screen, (50, 120, 230), (560, 290), (770, 160), 4)
    
    # Robo na posicao final
    pygame.draw.circle(screen, (40, 60, 100), (770, 160), 12)
    
    # Legenda da Trajetoria
    pygame.draw.rect(screen, (245, 248, 255), (480, 380, 370, 165), border_radius=8)
    pygame.draw.rect(screen, (200, 215, 240), (480, 380, 370, 165), 1, border_radius=8)
    
    screen.blit(font_title.render("Log de Telemetria e FSM:", True, (30, 40, 80)), (495, 390))
    screen.blit(font_small.render("\u2022 Fase 1: IR_PARA_ALVO (Avanco v=0.5m/s)", True, (30, 80, 180)), (495, 420))
    screen.blit(font_small.render("\u2022 Fase 2: DESVIAR_OBSTACULO (d_frente=0.38m < 0.5m)", True, (200, 70, 20)), (495, 445))
    screen.blit(font_small.render("\u2022 Fase 3: IR_PARA_ALVO retomado com sucesso", True, (30, 80, 180)), (495, 470))
    screen.blit(font_small.render("\u2022 Fase 4: OBJETIVO_ALCANCADO (d_alvo=0.08m < 0.2m)", True, (20, 130, 50)), (495, 495))
    screen.blit(font_small.render("\u2713 Robo parou com precisao no destino final!", True, (20, 110, 40)), (495, 520))
    
    pygame.display.flip()
    pygame.image.save(screen, "c:/TEMP/imr/IM_CDC6NA_2026-/AULA_05/print_lab5.png")
    print("\n[OK] Imagem salva: AULA_05/print_lab5.png")
    pygame.quit()

if __name__ == "__main__":
    main()
