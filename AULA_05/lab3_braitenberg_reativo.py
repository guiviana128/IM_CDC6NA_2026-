# pyrefly: ignore [missing-import]
import pygame
import math

def controle_reativo(distancias, K_lat=0.8, dist_critica=0.4):
    """
    Implementa controle reativo tipo Braitenberg com trava de seguranca.
    distancias = {'frente': float, 'esquerda': float, 'direita': float}
    Retorna: (v, omega)
    """
    dist_frente = distancias.get('frente', 5.0)
    dist_esq = distancias.get('esquerda', 5.0)
    dist_dir = distancias.get('direita', 5.0)
    
    # 1. Trava de Seguranca: obstaculo critico a frente
    if dist_frente < dist_critica:
        v = 0.0
        # Gira sobre o proprio eixo na direcao mais livre
        if dist_esq >= dist_dir:
            omega = 1.0   # Gira para a esquerda (+omega)
        else:
            omega = -1.0  # Gira para a direita (-omega)
    else:
        # 2. Frente livre: avanca e desvia suavemente das paredes laterais
        v = 0.5
        # Se dist_esq > dist_dir -> mais espaco na esquerda -> vira para a esquerda (+omega)
        erro_lateral = dist_esq - dist_dir
        omega = K_lat * erro_lateral
        # Limita omega para estabilidade
        omega = max(-1.5, min(1.5, omega))
        
    return v, omega

def main():
    print("=" * 60)
    print("EXERCICIO 3: Logica Reativa de Obstaculos com Trava de Seguranca")
    print("=" * 60)
    
    casos = [
        {"desc": "Bloqueio Frontal Crítico (Esquerda mais livre)", "dist": {'frente': 0.25, 'esquerda': 2.1, 'direita': 0.8}},
        {"desc": "Bloqueio Frontal Crítico (Direita mais livre)",  "dist": {'frente': 0.35, 'esquerda': 0.9, 'direita': 2.5}},
        {"desc": "Frente Livre e Corredor Equilibrado",            "dist": {'frente': 2.50, 'esquerda': 1.2, 'direita': 1.2}},
        {"desc": "Frente Livre mas Próximo da Parede Direita",     "dist": {'frente': 1.80, 'esquerda': 2.0, 'direita': 0.5}},
        {"desc": "Frente Livre mas Próximo da Parede Esquerda",    "dist": {'frente': 1.80, 'esquerda': 0.4, 'direita': 1.9}},
    ]
    
    for c in casos:
        v, w = controle_reativo(c["dist"])
        f, e, d = c["dist"]["frente"], c["dist"]["esquerda"], c["dist"]["direita"]
        print(f"\nCenario: {c['desc']}")
        print(f"  Entradas Sensor: Frente = {f:.2f}m, Esq = {e:.2f}m, Dir = {d:.2f}m")
        print(f"  Comando Gerado : v = {v:.2f} m/s, omega = {w:+.2f} rad/s")
        if f < 0.4:
            print(f"  Acao: [TRAVA DE SEGURANCA ATIVADA] Freio imediato e giro in-place!")
        else:
            print(f"  Acao: [CRUZEIRO REATIVO] Avanco continuo com correcao proporcional")

    # Renderizacao grafica do comportamento reativo
    pygame.init()
    WIDTH, HEIGHT = 900, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 3 - Logica Reativa e Trava de Seguranca")
    
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_body = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 14)
    
    screen.fill((240, 243, 246))
    
    title = font_title.render("Exercicio 3: Logica Reativa de Obstaculos (Braitenberg + Trava de Seguranca)", True, (20, 30, 60))
    screen.blit(title, (30, 20))
    
    # 2 Cenarios Visuais lado a lado
    # Cenario A: Trava de Seguranca (Freio + Giro in-place)
    # Cenario B: Frente Livre (Cruzeiro + Desvio lateral)
    
    # Caixa Cenario A
    pygame.draw.rect(screen, (255, 255, 255), (30, 65, 410, 500), border_radius=10)
    pygame.draw.rect(screen, (230, 160, 160), (30, 65, 410, 500), 2, border_radius=10)
    
    screen.blit(font_title.render("Cenario A: Trava de Seguranca", True, (180, 40, 40)), (45, 80))
    screen.blit(font_small.render("Condicao: dist_frente < 0.4m (Emergencia)", True, (100, 100, 100)), (45, 110))
    
    # Desenho da arena A
    ax, ay = 235, 290
    # Parede frontal
    pygame.draw.rect(screen, (160, 50, 50), (100, 160, 270, 25), border_radius=4)
    screen.blit(font_small.render("PAREDE FRONTAL (d = 0.28m)", True, (255, 255, 255)), (140, 164))
    
    # Obstaculo lateral direito
    pygame.draw.rect(screen, (160, 50, 50), (320, 220, 30, 120), border_radius=4)
    
    # Robo A
    pygame.draw.circle(screen, (220, 50, 50), (ax, ay), 26)
    pygame.draw.circle(screen, (120, 20, 20), (ax, ay), 26, 2)
    # Feixes de sensor A
    pygame.draw.line(screen, (255, 0, 0), (ax, ay), (ax, 185), 3) # Frente (colisao iminente)
    pygame.draw.line(screen, (50, 180, 50), (ax, ay), (ax - 90, ay), 2) # Esq (livre)
    pygame.draw.line(screen, (255, 150, 0), (ax, ay), (ax + 85, ay), 2) # Dir (perto)
    
    # Seta de giro in-place (+omega para esquerda)
    pygame.draw.arc(screen, (30, 120, 220), (ax - 40, ay - 40, 80, 80), math.pi/4, 5*math.pi/4, 4)
    pygame.draw.polygon(screen, (30, 120, 220), [(ax - 28, ay + 20), (ax - 40, ay + 35), (ax - 20, ay + 35)])
    
    # Dados Cenario A
    v_a, w_a = controle_reativo({'frente': 0.28, 'esquerda': 2.1, 'direita': 0.85})
    pygame.draw.rect(screen, (255, 240, 240), (45, 410, 380, 140), border_radius=8)
    screen.blit(font_body.render(f"Telemetria: Frente=0.28m | Esq=2.10m | Dir=0.85m", True, (40, 40, 40)), (55, 420))
    screen.blit(font_title.render(f"Comando: v = {v_a:.1f} m/s (FREIO ATIVO)", True, (180, 20, 20)), (55, 450))
    screen.blit(font_title.render(f"Comando: \u03c9 = {w_a:+.1f} rad/s (GIRO ESQ)", True, (30, 100, 200)), (55, 480))
    screen.blit(font_small.render("Robo para e gira no proprio eixo rumo a area livre", True, (100, 50, 50)), (55, 518))
    
    # Caixa Cenario B
    pygame.draw.rect(screen, (255, 255, 255), (460, 65, 410, 500), border_radius=10)
    pygame.draw.rect(screen, (160, 210, 170), (460, 65, 410, 500), 2, border_radius=10)
    
    screen.blit(font_title.render("Cenario B: Cruzeiro Reativo", True, (30, 130, 60)), (475, 80))
    screen.blit(font_small.render("Condicao: dist_frente \u2265 0.4m (Frente Desimpedida)", True, (100, 100, 100)), (475, 110))
    
    # Desenho da arena B
    bx, by = 665, 300
    # Paredes do corredor
    pygame.draw.rect(screen, (100, 120, 140), (510, 140, 20, 220), border_radius=4)
    pygame.draw.rect(screen, (100, 120, 140), (790, 140, 20, 220), border_radius=4)
    
    # Trajetoria curva suave
    pontos_traj = [(665, 340), (663, 310), (655, 270), (640, 220), (620, 170)]
    pygame.draw.lines(screen, (40, 160, 220), False, pontos_traj, 3)
    
    # Robo B
    pygame.draw.circle(screen, (40, 140, 80), (bx, by), 26)
    pygame.draw.circle(screen, (20, 80, 40), (bx, by), 26, 2)
    # Feixes de sensor B
    pygame.draw.line(screen, (50, 180, 50), (bx, by), (bx, 150), 2) # Frente livre (2.5m)
    pygame.draw.line(screen, (50, 180, 50), (bx, by), (530, by), 2) # Esq (1.35m)
    pygame.draw.line(screen, (230, 130, 0), (bx, by), (790, by), 2) # Dir (1.25m)
    
    # Vetor velocidade linear
    pygame.draw.line(screen, (30, 120, 220), (bx, by), (bx - 15, by - 45), 4)
    pygame.draw.polygon(screen, (30, 120, 220), [(bx - 15, by - 55), (bx - 23, by - 42), (bx - 7, by - 42)])
    
    # Dados Cenario B
    v_b, w_b = controle_reativo({'frente': 2.5, 'esquerda': 1.8, 'direita': 0.7})
    pygame.draw.rect(screen, (240, 255, 245), (475, 410, 380, 140), border_radius=8)
    screen.blit(font_body.render(f"Telemetria: Frente=2.50m | Esq=1.80m | Dir=0.70m", True, (40, 40, 40)), (485, 420))
    screen.blit(font_title.render(f"Comando: v = {v_b:.1f} m/s (AVANCO)", True, (30, 130, 60)), (485, 450))
    screen.blit(font_title.render(f"Comando: \u03c9 = {w_b:+.2f} rad/s (CORRECAO)", True, (30, 100, 200)), (485, 480))
    screen.blit(font_small.render(f"\u03c9 = K_lat \u00b7 (d_esq - d_dir) = 0.8 \u00b7 (1.8 - 0.7) = {w_b:+.2f} rad/s", True, (40, 100, 50)), (485, 518))
    
    pygame.display.flip()
    pygame.image.save(screen, "c:/TEMP/imr/IM_CDC6NA_2026-/AULA_05/print_lab3.png")
    print("\n[OK] Imagem salva: AULA_05/print_lab3.png")
    pygame.quit()

if __name__ == "__main__":
    main()
