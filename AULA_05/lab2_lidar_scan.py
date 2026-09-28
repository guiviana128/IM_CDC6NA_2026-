# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import pygame
import math

def processar_scan(leituras_lidar):
    """
    Recebe um array/lista de 360 leituras de distancia do LiDAR (0 a 359 graus).
    Filtra ruidos (descarta valores < 0.1 m ou > 5.0 m).
    Retorna um dicionario com a menor distancia valida em 3 setores:
      - Frente: 345° a 359° e 0° a 15°
      - Esquerda: 45° a 135°
      - Direita: 225° a 315°
    """
    leituras = np.array(leituras_lidar, dtype=float)
    
    # Mascara de indices por setor
    # Frente: [345..359] e [0..15]
    indices_frente = np.concatenate([np.arange(345, 360), np.arange(0, 16)])
    indices_esq = np.arange(45, 136)
    indices_dir = np.arange(225, 316)
    
    def extrair_min_valido(indices, default_val=5.0):
        valores = leituras[indices]
        # Filtro de limiar: 0.1 m <= d <= 5.0 m
        validos = valores[(valores >= 0.1) & (valores <= 5.0)]
        if len(validos) > 0:
            return float(np.min(validos))
        return float(default_val)
    
    min_frente = extrair_min_valido(indices_frente)
    min_esq = extrair_min_valido(indices_esq)
    min_dir = extrair_min_valido(indices_dir)
    
    return {
        'frente': round(min_frente, 4),
        'esquerda': round(min_esq, 4),
        'direita': round(min_dir, 4)
    }

def gerar_scan_simulado():
    """Gera 360 leituras realistas com obstaculo frontal, lateral e ruidos/invalids."""
    np.random.seed(42)
    # Fundo livre com raio medio ~4.5m
    leituras = np.random.uniform(4.0, 4.8, 360)
    
    # Parede / Obstaculo a Frente (350° a 10°) a ~ 0.85m com variacao
    for ang in list(range(350, 360)) + list(range(0, 11)):
        leituras[ang] = 0.85 + np.random.normal(0, 0.03)
        
    # Parede a Esquerda (60° a 100°) a ~ 1.20m
    for ang in range(60, 101):
        leituras[ang] = 1.20 + np.random.normal(0, 0.04)
        
    # Parede a Direita (250° a 290°) a ~ 2.10m
    for ang in range(250, 291):
        leituras[ang] = 2.10 + np.random.normal(0, 0.05)
        
    # Insercao de ruidos invalidos: leituras 0.0 (reflexao perdida) e > 5.0 (fora de alcance)
    leituras[5] = 0.0
    leituras[8] = 0.03   # < 0.1 m -> ruido espurio
    leituras[75] = 99.0  # > 5.0 m -> fora de alcance
    leituras[85] = 0.0
    leituras[270] = 0.05 # < 0.1 m -> ruido
    leituras[300] = 12.5 # > 5.0 m
    
    return leituras

def main():
    print("=" * 60)
    print("EXERCICIO 2: No Sensor - Processador e Filtro do Topico /scan")
    print("=" * 60)
    
    scan = gerar_scan_simulado()
    resultado = processar_scan(scan)
    
    print("\nProcessamento dos dados de 360 graus do LiDAR:")
    print(f"  Total de feixes analisados: {len(scan)}")
    print(f"  Menor distancia Frente (345 deg a 15 deg) : {resultado['frente']:.3f} m")
    print(f"  Menor distancia Esquerda (45 deg a 135 deg): {resultado['esquerda']:.3f} m")
    print(f"  Menor distancia Direita (225 deg a 315 deg): {resultado['direita']:.3f} m")
    print(f"\nDicionario retornado:\n  {resultado}")
    
    # Visualizacao grafica em Radar Polar com Pygame
    pygame.init()
    WIDTH, HEIGHT = 900, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lab 2 - Processamento /scan LiDAR 360")
    
    font_title = pygame.font.SysFont("Arial", 22, bold=True)
    font_body = pygame.font.SysFont("Arial", 17)
    font_small = pygame.font.SysFont("Arial", 14)
    
    screen.fill((240, 243, 246))
    
    title = font_title.render("Exercicio 2: No Sensor - Processamento e Filtro do Topico /scan (LiDAR 360\u00b0)", True, (20, 30, 60))
    screen.blit(title, (30, 20))
    
    # Painel Esquerdo: Radar Polar
    cx, cy = 290, 320
    raio_max_px = 220
    
    pygame.draw.rect(screen, (255, 255, 255), (30, 65, 520, 510), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (30, 65, 520, 510), 2, border_radius=10)
    
    # Circulos concentricos de distancia (1m, 2m, 3m, 4m, 5m)
    for dist_m in [1.0, 2.0, 3.0, 4.0, 5.0]:
        r_px = int((dist_m / 5.0) * raio_max_px)
        pygame.draw.circle(screen, (225, 230, 240), (cx, cy), r_px, 1)
        screen.blit(font_small.render(f"{dist_m:.0f}m", True, (140, 150, 170)), (cx + r_px - 14, cy + 3))
        
    # Eixos cardeais
    pygame.draw.line(screen, (210, 220, 230), (cx - raio_max_px, cy), (cx + raio_max_px, cy), 1)
    pygame.draw.line(screen, (210, 220, 230), (cx, cy - raio_max_px), (cx, cy + raio_max_px), 1)
    
    # Plot de cada um dos 360 feixes
    for ang_deg in range(360):
        val = scan[ang_deg]
        ang_rad = math.radians(ang_deg)
        
        # Cor por setor ou se for invalido/filtrado
        valido = (0.1 <= val <= 5.0)
        
        # No sistema de coordenadas do plano do robo: 0 deg = Frente (-Y na tela)
        # angulo 0 = frente (cima), 90 = esquerda (esquerda), 180 = tras (baixo), 270 = direita (direita)
        # x_p = cx - r * sin(ang), y_p = cy - r * cos(ang)
        r_plot = min(val, 5.0) if valido else 5.0
        r_px = (r_plot / 5.0) * raio_max_px
        
        px = cx - int(r_px * math.sin(ang_rad))
        py = cy - int(r_px * math.cos(ang_rad))
        
        if not valido:
            cor = (200, 200, 200) # Invalido / Ruido descartado
            pygame.draw.circle(screen, (220, 100, 100), (px, py), 2)
        elif (345 <= ang_deg < 360) or (0 <= ang_deg <= 15):
            cor = (230, 50, 50)   # Setor Frente
            pygame.draw.line(screen, (255, 200, 200), (cx, cy), (px, py), 1)
            pygame.draw.circle(screen, cor, (px, py), 3)
        elif 45 <= ang_deg <= 135:
            cor = (40, 120, 220)  # Setor Esquerda
            pygame.draw.line(screen, (200, 220, 255), (cx, cy), (px, py), 1)
            pygame.draw.circle(screen, cor, (px, py), 3)
        elif 225 <= ang_deg <= 315:
            cor = (40, 170, 80)   # Setor Direita
            pygame.draw.line(screen, (200, 250, 210), (cx, cy), (px, py), 1)
            pygame.draw.circle(screen, cor, (px, py), 3)
        else:
            cor = (160, 160, 170) # Outros setores
            pygame.draw.circle(screen, cor, (px, py), 2)
            
    # Desenho do robo central
    pygame.draw.circle(screen, (40, 60, 100), (cx, cy), 14)
    pygame.draw.polygon(screen, (255, 215, 0), [(cx, cy - 12), (cx - 5, cy), (cx + 5, cy)])
    
    # Painel Direito: Resultados e Metricas
    pygame.draw.rect(screen, (255, 255, 255), (570, 65, 300, 510), border_radius=10)
    pygame.draw.rect(screen, (200, 210, 225), (570, 65, 300, 510), 2, border_radius=10)
    
    sec_title = font_title.render("Leituras Processadas", True, (40, 80, 160))
    screen.blit(sec_title, (585, 80))
    
    # Card Frente
    pygame.draw.rect(screen, (255, 240, 240), (585, 120, 270, 95), border_radius=8)
    pygame.draw.rect(screen, (230, 150, 150), (585, 120, 270, 95), 1, border_radius=8)
    screen.blit(font_body.render("SETOR FRENTE [345\u00b0 - 15\u00b0]", True, (180, 30, 30)), (595, 130))
    screen.blit(font_title.render(f"Min: {resultado['frente']:.3f} m", True, (180, 20, 20)), (595, 155))
    screen.blit(font_small.render("Status: Obstaculo Proximo!", True, (120, 30, 30)), (595, 190))
    
    # Card Esquerda
    pygame.draw.rect(screen, (240, 245, 255), (585, 230, 270, 95), border_radius=8)
    pygame.draw.rect(screen, (150, 180, 230), (585, 230, 270, 95), 1, border_radius=8)
    screen.blit(font_body.render("SETOR ESQUERDA [45\u00b0 - 135\u00b0]", True, (30, 80, 180)), (595, 240))
    screen.blit(font_title.render(f"Min: {resultado['esquerda']:.3f} m", True, (20, 60, 160)), (595, 265))
    screen.blit(font_small.render("Status: Parede Lateral Detectada", True, (30, 60, 120)), (595, 300))
    
    # Card Direita
    pygame.draw.rect(screen, (240, 255, 245), (585, 340, 270, 95), border_radius=8)
    pygame.draw.rect(screen, (150, 220, 170), (585, 340, 270, 95), 1, border_radius=8)
    screen.blit(font_body.render("SETOR DIREITA [225\u00b0 - 315\u00b0]", True, (30, 140, 60)), (595, 350))
    screen.blit(font_title.render(f"Min: {resultado['direita']:.3f} m", True, (20, 120, 50)), (595, 375))
    screen.blit(font_small.render("Status: Espaco Livre", True, (20, 100, 40)), (595, 410))
    
    # Filtro de Ruido aplicado
    screen.blit(font_small.render("\u2713 Filtro aplicado: 0.1m \u2264 d \u2264 5.0m", True, (80, 80, 80)), (590, 460))
    screen.blit(font_small.render("\u2713 Leituras nulas (0.0) e >5.0 descartadas", True, (80, 80, 80)), (590, 485))
    screen.blit(font_small.render("\u2713 360 raios analisados em tempo real", True, (80, 80, 80)), (590, 510))
    
    pygame.display.flip()
    pygame.image.save(screen, "c:/TEMP/imr/IM_CDC6NA_2026-/AULA_05/print_lab2.png")
    print("\n[OK] Imagem salva: AULA_05/print_lab2.png")
    pygame.quit()

if __name__ == "__main__":
    main()
