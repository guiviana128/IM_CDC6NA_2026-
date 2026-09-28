import math
# pyrefly: ignore [missing-import]
import pygame

def converter_cmd_vel(v, omega, L=0.3, max_wheel_speed=1.5):
    """
    Converte comandos /cmd_vel (v, omega) para velocidades das rodas (v_e, v_d)
    de um robo diferencial com distancia entre eixos L e limite de velocidade max_wheel_speed.
    Aplica saturacao proporcional para preservar o raio de curvatura.
    """
    # 1. Cinemática diferencial inversa (velocidades brutas)
    v_e_raw = v - (omega * L / 2.0)
    v_d_raw = v + (omega * L / 2.0)
    
    # 2. Identifica a maior velocidade em modulo
    max_raw = max(abs(v_e_raw), abs(v_d_raw))
    
    # 3. Se ultrapassar o limite maximo, aplica fator de escala proporcional
    if max_raw > max_wheel_speed:
        escala = max_wheel_speed / max_raw
        v_e = v_e_raw * escala
        v_d = v_d_raw * escala
        saturado = True
    else:
        v_e = v_e_raw
        v_d = v_d_raw
        saturado = False
        
    return v_e, v_d

def main():
    print("=" * 60)
    print("EXERCICIO 1: Conversor de /cmd_vel com Saturacao dos Motores")
    print("=" * 60)
    
    # Casos de teste
    testes = [
        {"desc": "Comando do Enunciado", "v": 1.2, "omega": 3.0},
        {"desc": "Velocidade Linear Baixa (Sem Saturacao)", "v": 0.5, "omega": 1.0},
        {"desc": "Giro Puro Rapido", "v": 0.0, "omega": 12.0},
        {"desc": "Re com Curva Excessiva", "v": -1.2, "omega": -4.0},
    ]
    
    for t in testes:
        v, omega = t["v"], t["omega"]
        ve, vd = converter_cmd_vel(v, omega)
        v_e_raw = v - (omega * 0.3 / 2.0)
        v_d_raw = v + (omega * 0.3 / 2.0)
        sat = max(abs(v_e_raw), abs(v_d_raw)) > 1.5
        print(f"\nTeste: {t['desc']}")
        print(f"  Entrada /cmd_vel: v = {v:.2f} m/s, omega = {omega:.2f} rad/s")
        print(f"  Velocidades brutas:  v_e = {v_e_raw:+.4f} m/s, v_d = {v_d_raw:+.4f} m/s")
        print(f"  Saturado?: {'SIM (Escalado proporcionalmente)' if sat else 'NAO'}")
        print(f"  Saida Final Motores: v_e = {ve:+.4f} m/s, v_d = {vd:+.4f} m/s")
        print(f"  Max Wheel Speed: {max(abs(ve), abs(vd)):.4f} m/s (Limite = 1.5000 m/s)")

    # Renderizacao visual e geracao de print de evidencia
    pygame.init()
    WIDTH, HEIGHT = 900, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 1 - Atuador /cmd_vel com Saturacao")
    
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_body = pygame.font.SysFont("Arial", 18)
    font_small = pygame.font.SysFont("Arial", 15)
    
    screen.fill((240, 243, 246))
    
    # Cabecalho
    title = font_title.render("Exercicio 1: No Atuador - Conversor /cmd_vel com Saturacao Proporcional", True, (20, 30, 60))
    screen.blit(title, (30, 25))
    
    # Painel de informacoes do teste principal
    v_in, w_in = 1.2, 3.0
    ve_out, vd_out = converter_cmd_vel(v_in, w_in)
    ve_raw = v_in - (w_in * 0.3 / 2.0)
    vd_raw = v_in + (w_in * 0.3 / 2.0)
    
    # Caixa de comando de entrada
    pygame.draw.rect(screen, (255, 255, 255), (30, 70, 380, 220), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (30, 70, 380, 220), 2, border_radius=10)
    
    sec1 = font_title.render("1. Comando /cmd_vel (ROS 2)", True, (40, 80, 160))
    screen.blit(sec1, (45, 85))
    screen.blit(font_body.render(f"Velocidade Linear (v): {v_in:.2f} m/s", True, (40, 40, 40)), (45, 125))
    screen.blit(font_body.render(f"Velocidade Angular (\u03c9): {w_in:.2f} rad/s", True, (40, 40, 40)), (45, 155))
    screen.blit(font_body.render(f"Distancia entre rodas (L): 0.30 m", True, (40, 40, 40)), (45, 185))
    screen.blit(font_body.render(f"Limite maximo (v_max): \u00b11.50 m/s", True, (180, 40, 40)), (45, 215))
    screen.blit(font_small.render("Formula: v_e = v - (\u03c9\u00b7L/2) | v_d = v + (\u03c9\u00b7L/2)", True, (100, 100, 100)), (45, 250))
    
    # Caixa de comparacao Bruto vs Saturado
    pygame.draw.rect(screen, (255, 255, 255), (440, 70, 430, 220), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (440, 70, 430, 220), 2, border_radius=10)
    
    sec2 = font_title.render("2. Processamento e Saturacao", True, (40, 80, 160))
    screen.blit(sec2, (455, 85))
    
    screen.blit(font_body.render(f"Velocidades Brutas:", True, (50, 50, 50)), (455, 120))
    screen.blit(font_body.render(f"  \u2022 v_e (bruta) = {ve_raw:+.4f} m/s", True, (50, 50, 50)), (455, 145))
    screen.blit(font_body.render(f"  \u2022 v_d (bruta) = {vd_raw:+.4f} m/s (ULTRAPASSA 1.5!)", True, (200, 30, 30)), (455, 170))
    
    escala = 1.5 / vd_raw
    screen.blit(font_body.render(f"Fator de Escala s = 1.5 / {vd_raw:.2f} = {escala:.4f}", True, (20, 120, 40)), (455, 205))
    screen.blit(font_body.render(f"Velocidades Finais dos Motores:", True, (30, 30, 30)), (455, 235))
    screen.blit(font_body.render(f"  \u2192 v_e = {ve_out:+.4f} m/s  |  v_d = {vd_out:+.4f} m/s", True, (20, 130, 30)), (455, 260))
    
    # Diagrama grafico do Robo e das Rodas
    pygame.draw.rect(screen, (255, 255, 255), (30, 310, 840, 260), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (30, 310, 840, 260), 2, border_radius=10)
    
    sec3 = font_title.render("3. Visualizacao Dinamica do Robo Diferencial", True, (40, 80, 160))
    screen.blit(sec3, (45, 325))
    
    cx, cy = 450, 445
    # Chassi do robo
    pygame.draw.circle(screen, (70, 130, 180), (cx, cy), 55)
    pygame.draw.circle(screen, (30, 70, 120), (cx, cy), 55, 3)
    # Direcao da frente
    pygame.draw.polygon(screen, (255, 215, 0), [(cx, cy - 45), (cx - 15, cy - 20), (cx + 15, cy - 20)])
    
    # Roda Esquerda
    we_x, we_y = cx - 75, cy
    pygame.draw.rect(screen, (30, 30, 30), (we_x - 12, we_y - 35, 24, 70), border_radius=5)
    # Vetor Roda Esquerda
    len_e = int(ve_out * 45)
    pygame.draw.line(screen, (30, 150, 30), (we_x, we_y), (we_x, we_y - len_e), 5)
    pygame.draw.polygon(screen, (30, 150, 30), [(we_x, we_y - len_e - 6), (we_x - 6, we_y - len_e), (we_x + 6, we_y - len_e)])
    
    # Roda Direita
    wd_x, wd_y = cx + 75, cy
    pygame.draw.rect(screen, (30, 30, 30), (wd_x - 12, wd_y - 35, 24, 70), border_radius=5)
    # Vetor Roda Direita
    len_d = int(vd_out * 45)
    pygame.draw.line(screen, (200, 50, 50), (wd_x, wd_y), (wd_x, wd_y - len_d), 5)
    pygame.draw.polygon(screen, (200, 50, 50), [(wd_x, wd_y - len_d - 6), (wd_x - 6, wd_y - len_d), (wd_x + 6, wd_y - len_d)])
    
    # Rotulos das rodas
    screen.blit(font_body.render(f"Roda Esquerda (v_e)", True, (20, 20, 20)), (we_x - 160, we_y - 20))
    screen.blit(font_body.render(f"{ve_out:.4f} m/s", True, (30, 150, 30)), (we_x - 160, we_y + 5))
    
    screen.blit(font_body.render(f"Roda Direita (v_d)", True, (20, 20, 20)), (wd_x + 30, wd_y - 20))
    screen.blit(font_body.render(f"{vd_out:.4f} m/s (SAT)", True, (200, 50, 50)), (wd_x + 30, wd_y + 5))
    
    # Indicador de giro e curvatura
    screen.blit(font_body.render(f"Curvatura Preservada: Raio R = v / \u03c9 = {(v_in/w_in):.3f} m", True, (50, 50, 120)), (280, 530))
    
    pygame.display.flip()
    pygame.image.save(screen, "c:/TEMP/imr/IM_CDC6NA_2026-/AULA_05/print_lab1.png")
    print("\n[OK] Imagem salva: AULA_05/print_lab1.png")
    pygame.quit()

if __name__ == "__main__":
    main()
