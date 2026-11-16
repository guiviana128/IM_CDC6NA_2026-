#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOG-IA V2 - Simulador Urbano de Cão-Guia Autônomo (AC-4 - Entrega Final)

Evolução da V1 com:
  Marco 1 - semáforo com fases All-Red, veículos com cinemática, infratores e
            barreira física do meio-fio (aplicar_barreira).
  Marco 2 - arquitetura híbrida: A* em grade 10x10 px, C-Space com inflação
            assimétrica, custo reduzido no piso tátil, destinos 1-4 e
            replanejamento automático após 3,5 s preso em desvio local.
  Marco 3 - LiDAR com rect.clipline, ruído gaussiano, dropout de 2%, filtro de
            mediana temporal (3 varreduras) e predição por zona varrida.
  Marco 4 - tutor como entidade física presa pelo arnês, áudio estéreo e
            telemetria/benchmark headless.

Uso:
  python dog_ia_v2.py                          # modo interativo (janela)
  python dog_ia_v2.py --seed 3                 # interativo com seed fixa
  python dog_ia_v2.py --benchmark 20 --seed 1  # avaliação sem janela
  python dog_ia_v2.py --trace Mercado          # 1 viagem sem janela, imprime os estados
  python dog_ia_v2.py --gravar video.mp4       # grava ida e volta (precisa de ffmpeg)
"""
import argparse
import csv
import heapq
import math
import os
import random
import subprocess
import sys
from array import array
from collections import deque

import pygame

# ==================== CONFIGURAÇÕES GERAIS ====================
LARGURA, ALTURA = 1050, 680
FPS = 60
DT_FIXO = 1.0 / FPS                 # passo de simulação (s) - independente do FPS real
AREA_MAPA_LARGURA = LARGURA - 260   # 790 px de mapa, 260 px de painel
PX_POR_METRO = 130.0                # 156 px/s ~ 1,2 m/s (passo humano)

# Avenida e faixa de pedestres
RUA_Y = 250
RUA_ALTURA = 170
RUA_FIM = RUA_Y + RUA_ALTURA        # 420
FAIXA_X = 580
FAIXA_LARGURA = 95
FAIXA_CX = 628                      # centro da faixa (alinhado ao piso tátil vertical)

# Robô, guia e travessia
VEL_ROBO = 156.0                    # px/s
W_MAX = 4.5                         # rad/s
R_ROBO = 18                         # raio para colisão com veículos
R_FISICO = 16                       # raio para colisão com obstáculos fixos
R_TUTOR = 12
GUIA = 42                           # comprimento do arnês (px)
FOLGA_GUIA = 10                     # tensão tolerada antes de reduzir a velocidade
VEL_MAX_TUTOR = 150.0               # o tutor anda um pouco mais devagar que o robô
K_TUTOR = 12.0                      # ganho do "puxão" do arnês
FOLGA_MEIO_FIO = 24
LIMITE_TRAVESSIA = (RUA_ALTURA + FOLGA_MEIO_FIO + GUIA) / VEL_ROBO * 1.35 + 0.4  # ~2,44 s
MARGEM_BARREIRA = 8                 # centro do robô não passa desta distância do meio-fio
TOL_PONTO = 10
LOOKAHEAD = 28

# Semáforo (fase, duração em segundos)
FASES = [("VERDE", 8.0), ("AMARELO", 2.5), ("TODOS_VERM_1", 1.5),
         ("PEDESTRE", 7.0), ("TODOS_VERM_2", 1.5)]

# Veículos
ACEL = 110.0                        # px/s²
DESACEL = 240.0                     # frenagem confortável (planejada)
DESACEL_MAX = 450.0                 # frenagem máxima física
VEL_CARRO = (170.0, 230.0)
CARRO_COMP, CARRO_LARG = 46, 24
DIST_SEGUIMENTO = 16                # distância mínima para o carro da frente (px)
HEADWAY = 0.4                       # tempo de seguimento (s)
PROB_INFRATOR = 0.10
FAIXA_LESTE_Y = 377                 # mão sul, sentido -> (direção +1)
FAIXA_OESTE_Y = 293                 # mão norte, sentido <- (direção -1)
LINHA_RETENCAO = {1: FAIXA_X - 14, -1: FAIXA_X + FAIXA_LARGURA + 14}
PERCEPCAO_NORMAL = 150              # distância em que o motorista vê o pedestre
PERCEPCAO_INFRATOR = 55             # motorista infrator/distraído

# Grade de ocupação / A*
CELULA = 10
INFLACAO = {"solo": 30, "edificacao": 22, "suspenso": 38}
CUSTO_TATIL = 0.45
MARGEM_RUA = 15
TEMPO_MAX_DESVIO = 3.5
LIMIAR_DESVIO = 34

# LiDAR
ALCANCE_LIDAR = 165
NUM_RAIOS = 19
FOV = math.radians(150)
SIGMA_RUIDO = 1.5
TAXA_DROPOUT = 0.02
JANELA_MEDIANA = 3
HORIZONTE_PREDICAO = 1.0
DIST_QUASE = 22

# Paleta (mesma da V1 + novas cores)
BRANCO = (245, 245, 245)
PRETO = (20, 22, 28)
ASFALTO = (42, 45, 52)
CALCADA_CLARA = (130, 134, 142)
MEIO_FIO = (175, 180, 188)
PISO_TATIL = (235, 190, 20)
GRAMA = (46, 115, 65)
CORPO_ROBO = (30, 136, 229)
DETALHE_ROBO = (15, 76, 129)
CABECA_ROBO = (230, 236, 245)
ARNES_GUIA = (255, 215, 0)
VERDE_LIVRE = (46, 204, 113)
LARANJA_ALERTA = (255, 140, 0)
VERMELHO_PERIGO = (225, 55, 55)
ROXO_SUSPENSO = (155, 89, 182)
AMARELO_SINAL = (250, 200, 30)
CINZA_TEXTO = (170, 175, 185)
CIANO_ROTA = (80, 220, 230)
CORES_CARROS = [(200, 60, 60), (60, 120, 200), (230, 230, 235), (40, 40, 45),
                (90, 160, 90), (200, 160, 60), (130, 130, 140)]

# Piso tátil (mesmos retângulos da V1)
TATIL_RECTS = [pygame.Rect(40, 120, 595, 14), pygame.Rect(621, 120, 14, 130),
               pygame.Rect(621, RUA_FIM, 14, 130), pygame.Rect(150, 536, 485, 14)]

PAREDES = [pygame.Rect(0, 0, 15, ALTURA), pygame.Rect(AREA_MAPA_LARGURA - 15, 0, 15, ALTURA),
           pygame.Rect(0, 0, AREA_MAPA_LARGURA, 15), pygame.Rect(0, ALTURA - 15, AREA_MAPA_LARGURA, 15)]

DESTINOS = {"Mercado": (110, 530), "Farmácia": (715, 535), "Padaria": (715, 150), "Casa": (95, 127)}
TECLAS_DESTINO = {pygame.K_1: "Mercado", pygame.K_2: "Farmácia", pygame.K_3: "Padaria", pygame.K_4: "Casa"}

# Pontos fixos da travessia: (ponto de espera, ponto de saída do outro lado)
_TRAVESSIA_DIST = RUA_ALTURA + FOLGA_MEIO_FIO + GUIA            # 236 px
PONTOS_TRAVESSIA = {
    "norte": ((FAIXA_CX, RUA_Y - FOLGA_MEIO_FIO), (FAIXA_CX, RUA_Y - FOLGA_MEIO_FIO + _TRAVESSIA_DIST)),
    "sul": ((FAIXA_CX, RUA_FIM + FOLGA_MEIO_FIO), (FAIXA_CX, RUA_FIM + FOLGA_MEIO_FIO - _TRAVESSIA_DIST)),
}


# ==================== FUNÇÕES AUXILIARES ====================
def rotacionar_ponto(cx, cy, px, py, angulo):
    """Rotaciona um ponto (px, py) ao redor de (cx, cy) dado um ângulo em radianos."""
    s, c = math.sin(angulo), math.cos(angulo)
    dx, dy = px - cx, py - cy
    return (int(cx + dx * c - dy * s), int(cy + dx * s + dy * c))


def normalizar_angulo(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def limitar(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def dist_ponto_rect(px, py, r):
    """Distância euclidiana de um ponto até a borda de um retângulo (0 se dentro)."""
    dx = max(r.left - px, 0.0, px - r.right)
    dy = max(r.top - py, 0.0, py - r.bottom)
    return math.hypot(dx, dy)


def lado_da_rua(y):
    return "norte" if y < RUA_Y + RUA_ALTURA / 2 else "sul"


# ==================== MARCO 1: SEMÁFORO ====================
class Semaforo:
    """Ciclo VERDE -> AMARELO -> TODOS_VERM_1 -> PEDESTRE -> TODOS_VERM_2, em tempo simulado."""

    def __init__(self, rng):
        self.idx = rng.randrange(len(FASES))
        self.t = rng.uniform(0, FASES[self.idx][1])

    @property
    def fase(self):
        return FASES[self.idx][0]

    @property
    def restante(self):
        return FASES[self.idx][1] - self.t

    def atualizar(self, dt):
        self.t += dt
        while self.t >= FASES[self.idx][1]:
            self.t -= FASES[self.idx][1]
            self.idx = (self.idx + 1) % len(FASES)

    def sinal_veiculos(self):
        if self.fase == "VERDE":
            return "VERDE"
        if self.fase == "AMARELO":
            return "AMARELO"
        return "VERMELHO"


# ==================== MARCO 1: VEÍCULOS ====================
class Veiculo:
    _contador = 0

    def __init__(self, direcao, vmax, infrator, cor, v_inicial):
        Veiculo._contador += 1
        self.id = Veiculo._contador
        self.dir = direcao
        self.y = FAIXA_LESTE_Y if direcao > 0 else FAIXA_OESTE_Y
        self.x = -CARRO_COMP if direcao > 0 else AREA_MAPA_LARGURA + CARRO_COMP
        self.vmax = vmax
        self.v = v_inicial
        self.infrator = infrator
        self.cor = cor
        self.decisao_amarelo = None   # "PARAR" ou "SEGUIR", decidido quando o amarelo acende

    def frente(self):
        return self.x + self.dir * CARRO_COMP / 2

    def traseira(self):
        return self.x - self.dir * CARRO_COMP / 2

    def rect(self):
        return pygame.Rect(int(self.x - CARRO_COMP / 2), int(self.y - CARRO_LARG / 2), CARRO_COMP, CARRO_LARG)

    def dist_linha(self):
        """Distância (px) da frente do carro até a linha de retenção (>0 = antes da linha)."""
        return (LINHA_RETENCAO[self.dir] - self.frente()) * self.dir

    def zona_varrida(self, horizonte):
        """Retângulo que o carro vai ocupar entre agora e agora + horizonte (swept volume)."""
        if self.v < 8:
            return None
        r = self.rect()
        futuro = r.move(int(self.dir * self.v * horizonte), 0)
        return r.union(futuro).inflate(8, 8)


class Trafego:
    def __init__(self, rng):
        self.rng = rng
        self.carros = []
        self.timers = {1: rng.uniform(0, 1.5), -1: rng.uniform(0, 1.5)}

    def _gerar(self, direcao):
        spawn_x = -CARRO_COMP if direcao > 0 else AREA_MAPA_LARGURA + CARRO_COMP
        mesmos = [c for c in self.carros if c.dir == direcao]
        vmax = self.rng.uniform(*VEL_CARRO)
        infrator = self.rng.random() < PROB_INFRATOR
        cor = self.rng.choice(CORES_CARROS)
        v0 = vmax * 0.9
        if mesmos:
            ultimo = min(mesmos, key=lambda c: c.x * direcao)
            gap = (ultimo.traseira() - (spawn_x + direcao * CARRO_COMP / 2)) * direcao
            if gap < 30:
                return False
            v0 = min(v0, math.sqrt(max(0.0, ultimo.v ** 2 + 2 * DESACEL * (gap - DIST_SEGUIMENTO))))
        self.carros.append(Veiculo(direcao, vmax, infrator, cor, v0))
        return True

    def atualizar(self, dt, semaforo, pedestres):
        for d in (1, -1):
            self.timers[d] -= dt
            if self.timers[d] <= 0:
                self.timers[d] = self.rng.uniform(1.6, 4.0) if self._gerar(d) else 0.4

        sinal = semaforo.sinal_veiculos()
        for d in (1, -1):
            fila = sorted((c for c in self.carros if c.dir == d), key=lambda c: -c.x * d)
            for i, c in enumerate(fila):
                v_alvo = c.vmax

                # 1) Distância de seguimento em relação ao carro da frente
                if i > 0:
                    lider = fila[i - 1]
                    gap = (lider.traseira() - c.frente()) * d
                    v_alvo = min(v_alvo, math.sqrt(max(0.0, lider.v ** 2 + 2 * DESACEL *
                                                       (gap - DIST_SEGUIMENTO - c.v * HEADWAY))))

                # 2) Semáforo: frenagem antes da linha de retenção (infrator ignora)
                if sinal == "VERDE":
                    c.decisao_amarelo = None
                d_linha = c.dist_linha()
                if not c.infrator and d_linha > -2:
                    if sinal == "AMARELO" and c.decisao_amarelo is None:
                        c.decisao_amarelo = "PARAR" if c.v ** 2 / (2 * DESACEL) <= d_linha else "SEGUIR"
                    deve_parar = ((sinal == "VERMELHO" and c.decisao_amarelo != "SEGUIR") or
                                  (sinal == "AMARELO" and c.decisao_amarelo == "PARAR"))
                    if deve_parar:
                        v_alvo = min(v_alvo, math.sqrt(2 * DESACEL * max(0.0, d_linha - 2)))

                # 3) Motorista vê o pedestre (robô/tutor) na sua frente e freia
                alcance = PERCEPCAO_INFRATOR if c.infrator else PERCEPCAO_NORMAL
                for (px, py, pr) in pedestres:
                    if abs(py - c.y) < CARRO_LARG / 2 + pr + 4:
                        a_frente = (px - c.frente()) * d - pr
                        if -CARRO_COMP < a_frente < alcance:
                            v_alvo = min(v_alvo, math.sqrt(2 * DESACEL_MAX * max(0.0, a_frente - 6)))

                # Cinemática: aceleração e desaceleração limitadas
                if c.v < v_alvo:
                    c.v = min(v_alvo, c.v + ACEL * dt)
                else:
                    c.v = max(v_alvo, c.v - DESACEL_MAX * dt)
                c.x += d * c.v * dt

        self.carros = [c for c in self.carros if -90 < c.x < AREA_MAPA_LARGURA + 90]


# ==================== MARCO 2: PLANEJADOR A* ====================
class PlanejadorAStar:
    VIZINHOS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]

    def __init__(self):
        self.cols = AREA_MAPA_LARGURA // CELULA
        self.lins = ALTURA // CELULA
        self.custo = [math.inf] * (self.cols * self.lins)
        self.versao = 0

    @staticmethod
    def _area_caminhavel(cx, cy):
        m = INFLACAO["edificacao"]          # paredes e canteiros contam como edificação
        if cx < 15 + m or cx > AREA_MAPA_LARGURA - 15 - m:
            return False
        if cy < 28 + m or cy > ALTURA - 28 - m:
            return False
        if RUA_Y - MARGEM_RUA < cy < RUA_FIM + MARGEM_RUA:   # rua: só atravessa pela faixa
            return False
        return True

    def construir(self, obstaculos):
        """Grade de ocupação com C-Space (inflação assimétrica por tipo de obstáculo)."""
        for o in obstaculos:
            o["no_mapa"] = True          # agora faz parte do mapa do planejador
        inflados = [(o["rect"], INFLACAO[o["tipo"]]) for o in obstaculos if o["tipo"] in INFLACAO]
        custo = []
        for j in range(self.lins):
            cy = j * CELULA + CELULA / 2
            for i in range(self.cols):
                cx = i * CELULA + CELULA / 2
                if not self._area_caminhavel(cx, cy) or any(dist_ponto_rect(cx, cy, r) < m for r, m in inflados):
                    custo.append(math.inf)
                elif any(t.collidepoint(cx, cy) for t in TATIL_RECTS):
                    custo.append(CUSTO_TATIL)
                else:
                    custo.append(1.0)
        self.custo = custo
        self.versao += 1

    def celula(self, x, y):
        return (int(limitar(x // CELULA, 0, self.cols - 1)), int(limitar(y // CELULA, 0, self.lins - 1)))

    def centro(self, n):
        return ((n % self.cols) * CELULA + CELULA / 2, (n // self.cols) * CELULA + CELULA / 2)

    def _livre_mais_proximo(self, n):
        """BFS até a célula livre mais próxima (usado quando o início/fim cai em área inflada)."""
        vistos = {n}
        fila = deque([n])
        while fila:
            u = fila.popleft()
            if self.custo[u] != math.inf:
                return u
            ui, uj = u % self.cols, u // self.cols
            for di, dj, _ in self.VIZINHOS[:4]:
                vi, vj = ui + di, uj + dj
                if 0 <= vi < self.cols and 0 <= vj < self.lins:
                    v = vj * self.cols + vi
                    if v not in vistos:
                        vistos.add(v)
                        fila.append(v)
        return None

    def _heuristica(self, a, b):
        """Distância octile (admissível: multiplicada pelo menor custo de célula)."""
        dx = abs(a % self.cols - b % self.cols)
        dy = abs(a // self.cols - b // self.cols)
        return (max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)) * CUSTO_TATIL

    def buscar(self, inicio, fim):
        si, sj = self.celula(*inicio)
        gi, gj = self.celula(*fim)
        s = sj * self.cols + si
        g = gj * self.cols + gi
        if self.custo[s] == math.inf:
            s = self._livre_mais_proximo(s)
        fim_livre = self.custo[g] != math.inf
        if not fim_livre:
            g = self._livre_mais_proximo(g)
        if s is None or g is None:
            return None

        aberto = [(self._heuristica(s, g), 0.0, s)]
        gscore = {s: 0.0}
        veio = {s: None}
        encontrou = False
        while aberto:
            _, gc, u = heapq.heappop(aberto)
            if u == g:
                encontrou = True
                break
            if gc > gscore[u]:
                continue
            ui, uj = u % self.cols, u // self.cols
            for di, dj, passo in self.VIZINHOS:
                vi, vj = ui + di, uj + dj
                if not (0 <= vi < self.cols and 0 <= vj < self.lins):
                    continue
                v = vj * self.cols + vi
                cv = self.custo[v]
                if cv == math.inf:
                    continue
                if di and dj and (self.custo[uj * self.cols + vi] == math.inf or
                                  self.custo[vj * self.cols + ui] == math.inf):
                    continue            # não corta quina de obstáculo
                ng = gc + passo * (self.custo[u] + cv) / 2
                if ng < gscore.get(v, math.inf):
                    gscore[v] = ng
                    veio[v] = u
                    heapq.heappush(aberto, (ng + self._heuristica(v, g), ng, v))
        if not encontrou:
            return None

        caminho = []
        n = g
        while n is not None:
            caminho.append(self.centro(n))
            n = veio[n]
        caminho.reverse()
        pontos = [tuple(inicio)] + caminho
        if fim_livre:
            pontos.append(tuple(fim))
        return pontos

    def planejar_rota(self, origem, destino):
        """Rota hierárquica: se o destino está do outro lado da avenida, passa pela faixa."""
        lo, ld = lado_da_rua(origem[1]), lado_da_rua(destino[1])
        if lo == ld:
            p = self.buscar(origem, destino)
            return [{"tipo": "caminho", "pontos": p}] if p else None
        espera, saida = PONTOS_TRAVESSIA[lo]
        p1 = self.buscar(origem, espera)
        p2 = self.buscar(saida, destino)
        if not p1 or not p2:
            return None
        return [{"tipo": "caminho", "pontos": p1},
                {"tipo": "travessia", "espera": espera, "saida": saida},
                {"tipo": "caminho", "pontos": p2}]


# ==================== MARCO 4: TUTOR ====================
class Tutor:
    """Pessoa guiada: entidade independente presa ao robô pelo arnês."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.angulo = 0.0

    def distancia(self, robo):
        return math.hypot(robo.x - self.x, robo.y - self.y)

    def tensao(self, robo):
        return max(0.0, self.distancia(robo) - GUIA)

    def atualizar(self, dt, robo):
        dx, dy = robo.x - self.x, robo.y - self.y
        d = math.hypot(dx, dy)
        if d < 1e-6:
            return
        self.angulo = math.atan2(dy, dx)
        excesso = d - GUIA
        if excesso > 0:
            passo = min(min(VEL_MAX_TUTOR, K_TUTOR * excesso) * dt, excesso)
            self.x += dx / d * passo
            self.y += dy / d * passo
        elif d < GUIA - 14:          # robô recuou: o tutor dá um passo para trás
            passo = min(60 * dt, GUIA - 14 - d)
            self.x -= dx / d * passo
            self.y -= dy / d * passo


# ==================== MARCO 4: ÁUDIO ESTÉREO ====================
class AudioEstereo:
    def __init__(self, ativo=True):
        self.ok = False
        self.mudo = False
        self.sons = {}
        if not ativo:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            freq, _, canais = pygame.mixer.get_init()
            self.sons = {
                "VERMELHO": self._tom(freq, canais, 980, 0.10, 0.55),
                "LARANJA": self._tom(freq, canais, 620, 0.09, 0.40),
                "ESPERA": self._tom(freq, canais, 440, 0.05, 0.25),
            }
            self.ok = True
        except Exception:
            self.ok = False

    @staticmethod
    def _tom(freq_amostra, canais, freq, duracao, volume):
        n = int(freq_amostra * duracao)
        dados = array("h")
        for k in range(n):
            env = min(1.0, k / 200, (n - k) / 400)
            amostra = int(32767 * volume * env * math.sin(2 * math.pi * freq * k / freq_amostra))
            for _ in range(canais):
                dados.append(amostra)
        return pygame.mixer.Sound(buffer=dados.tobytes())

    def tocar(self, tipo, pan):
        """pan = -1 (esquerda) ... +1 (direita)."""
        if not self.ok or self.mudo or tipo not in self.sons:
            return
        canal = self.sons[tipo].play()
        if canal:
            canal.set_volume(min(1.0, 1.0 - pan), min(1.0, 1.0 + pan))


# ==================== MARCO 4: MÉTRICAS ====================
class Metricas:
    CHAVES = ["alertas", "freios", "colisoes", "quase", "replans", "bloqueios", "toques_cabeca"]

    def __init__(self):
        self.viagens = []
        self.atual = None
        self.total = {k: 0 for k in self.CHAVES}
        self.total["dist"] = 0.0

    def iniciar_viagem(self, t, origem, destino):
        if self.atual is not None:
            self.encerrar(t, concluida=False)
        self.atual = {"origem": origem, "destino": destino, "t0": t, "tempo": 0.0, "dist": 0.0,
                      "concluida": False, **{k: 0 for k in self.CHAVES}}

    def inc(self, chave):
        self.total[chave] += 1
        if self.atual is not None:
            self.atual[chave] += 1

    def somar_distancia(self, d):
        self.total["dist"] += d
        if self.atual is not None:
            self.atual["dist"] += d

    def encerrar(self, t, concluida):
        if self.atual is None:
            return
        self.atual["tempo"] = t - self.atual["t0"]
        self.atual["concluida"] = concluida
        self.viagens.append(self.atual)
        self.atual = None

    @property
    def concluidas(self):
        return sum(1 for v in self.viagens if v["concluida"])


# ==================== ROBÔ CÃO-GUIA ====================
class RoboCaoGuia:
    def __init__(self, x, y, angulo=0.0):
        self.x, self.y = x, y
        self.angulo = angulo
        self.raio = 20
        self.hist_lidar = deque(maxlen=JANELA_MEDIANA)   # filtro de mediana temporal
        self.leituras_lidar = []
        self.estado = "AGUARDANDO_DESTINO"
        self.motivo = "aguardando o usuário escolher um destino"
        self.status_assistivo = "Pronto. Escolha um destino (1-4)."
        self.cor_alerta = VERDE_LIVRE
        self.segmentos = []
        self.seg_idx = 0
        self.wp_idx = 0
        self.destino = None
        self.destino_nome = ""
        self.autorizado = False
        self.t_desvio = 0.0
        self.t_livre = 0.0
        self.t_nav = 0.0
        self.t_seguro = 0.0
        self.estado_retorno = "NAVEGANDO"
        self.vel_atual = 0.0
        self.tensao = 0.0
        self.passo_animacao = 0.0
        self.carro_perigo = None

    # ---------- Marco 3: LiDAR realista ----------
    def ler_lidar(self, obstaculos, veiculos, rng):
        alc = ALCANCE_LIDAR
        candidatos = []
        for obs in obstaculos:
            if dist_ponto_rect(self.x, self.y, obs["rect"]) < alc:
                candidatos.append((obs["rect"], obs["tipo"], obs))
        for c in veiculos:
            r = c.rect()
            if dist_ponto_rect(self.x, self.y, r) < alc:
                candidatos.append((r, "veiculo", None))
        for p in PAREDES:
            if dist_ponto_rect(self.x, self.y, p) < alc:
                candidatos.append((p, "parede", None))

        a0 = self.angulo - FOV / 2
        passo = FOV / (NUM_RAIOS - 1)
        brutas, tipos, angulos, conhecidos = [], [], [], []
        for i in range(NUM_RAIOS):
            ang = a0 + i * passo
            fx, fy = self.x + math.cos(ang) * alc, self.y + math.sin(ang) * alc
            melhor, tipo, ref, conhecido = alc, None, None, True
            for rect, t, o in candidatos:
                seg = rect.clipline(self.x, self.y, fx, fy)     # interseção analítica
                if seg:
                    (x1, y1), (x2, y2) = seg
                    d = min(math.hypot(x1 - self.x, y1 - self.y), math.hypot(x2 - self.x, y2 - self.y))
                    if d < melhor:
                        melhor, tipo, ref = d, t, o
                        conhecido = (o.get("conhecido", True) or o.get("no_mapa", False)) if o is not None \
                            else t != "veiculo"
            if ref is not None:
                ref["visto"] = True          # o obstáculo passa a ser "conhecido" no próximo replanejamento
            if rng.random() < TAXA_DROPOUT:  # falha: devolve o alcance máximo
                melhor, tipo = alc, None
            elif melhor < alc:
                melhor = limitar(melhor + rng.gauss(0.0, SIGMA_RUIDO), 0.0, alc)
            brutas.append(melhor)
            tipos.append(tipo)
            conhecidos.append(conhecido)
            angulos.append(ang)

        self.hist_lidar.append(brutas)
        self.leituras_lidar = []
        for i in range(NUM_RAIOS):
            vals = sorted(h[i] for h in self.hist_lidar)
            n = len(vals)
            med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
            self.leituras_lidar.append({"angulo": angulos[i], "distancia": med,
                                        "tipo": tipos[i] if med < alc - 5 else None,
                                        "conhecido": conhecidos[i]})

    # ---------- Desenho ----------
    def desenhar(self, tela, tutor):
        # 1. Feixes do LiDAR (leituras filtradas)
        for r in self.leituras_lidar:
            fim_x = self.x + math.cos(r["angulo"]) * r["distancia"]
            fim_y = self.y + math.sin(r["angulo"]) * r["distancia"]
            cor = VERDE_LIVRE if r["distancia"] >= ALCANCE_LIDAR - 5 else VERMELHO_PERIGO
            pygame.draw.line(tela, cor, (self.x, self.y), (fim_x, fim_y), 1)
            if r["tipo"]:
                pygame.draw.circle(tela, BRANCO, (int(fim_x), int(fim_y)), 3)

        # 2. Arnês (cor indica a tensão) e tutor
        t = limitar((self.tensao - FOLGA_GUIA) / 20, 0, 1) if self.tensao > FOLGA_GUIA else 0
        cor_arnes = (255, int(215 * (1 - t)), int(40 * (1 - t)))
        pygame.draw.line(tela, cor_arnes, (self.x, self.y), (tutor.x, tutor.y), 4)
        pygame.draw.circle(tela, (235, 235, 240), (int(tutor.x), int(tutor.y)), R_TUTOR)
        pygame.draw.circle(tela, PRETO, (int(tutor.x), int(tutor.y)), R_TUTOR, 2)
        nx, ny = rotacionar_ponto(tutor.x, tutor.y, tutor.x + 8, tutor.y, tutor.angulo)
        pygame.draw.circle(tela, PRETO, (nx, ny), 3)

        # 3. Patas articuladas
        balanco = math.sin(self.passo_animacao) * 5
        for ox, oy in [(10 + balanco, -14), (10 - balanco, 14), (-12 - balanco, -14), (-12 + balanco, 14)]:
            pygame.draw.circle(tela, DETALHE_ROBO, rotacionar_ponto(self.x, self.y, self.x + ox, self.y + oy,
                                                                    self.angulo), 5)
        # 4. Tronco
        corpo = [rotacionar_ponto(self.x, self.y, self.x + px, self.y + py, self.angulo)
                 for px, py in [(16, -11), (16, 11), (-18, 11), (-18, -11)]]
        pygame.draw.polygon(tela, CORPO_ROBO, corpo)
        pygame.draw.polygon(tela, BRANCO, corpo, 2)
        # 5. Cabeça e orelhas
        cab = rotacionar_ponto(self.x, self.y, self.x + 21, self.y, self.angulo)
        pygame.draw.circle(tela, CABECA_ROBO, cab, 9)
        pygame.draw.circle(tela, DETALHE_ROBO, cab, 9, 2)
        for oy in (-10, 10):
            pygame.draw.circle(tela, DETALHE_ROBO, rotacionar_ponto(self.x, self.y, self.x + 19, self.y + oy,
                                                                    self.angulo), 4)
        # 6. Torre do LiDAR
        pygame.draw.circle(tela, LARANJA_ALERTA, rotacionar_ponto(self.x, self.y, self.x + 3, self.y,
                                                                  self.angulo), 5)


# ==================== CENÁRIO ====================
def criar_cenario():
    """Obstáculos da V1 + edificações dos destinos."""
    return [
        {"rect": pygame.Rect(230, 85, 45, 75), "tipo": "solo", "nome": "Banca / Hidrante"},
        {"rect": pygame.Rect(460, 160, 32, 32), "tipo": "solo", "nome": "Poste de Luz"},
        {"rect": pygame.Rect(380, 460, 40, 40), "tipo": "solo", "nome": "Lixeira Urbana"},
        {"rect": pygame.Rect(350, 75, 85, 65), "tipo": "suspenso", "nome": "Copa de Árvore"},
        {"rect": pygame.Rect(520, 485, 95, 65), "tipo": "suspenso", "nome": "Toldo de Loja"},
        {"rect": pygame.Rect(15, 28, 75, 55), "tipo": "edificacao", "nome": "Casa"},
        {"rect": pygame.Rect(660, 28, 115, 62), "tipo": "edificacao", "nome": "Padaria"},
        {"rect": pygame.Rect(40, 580, 130, 72), "tipo": "edificacao", "nome": "Mercado"},
        {"rect": pygame.Rect(660, 585, 115, 67), "tipo": "edificacao", "nome": "Farmácia"},
    ]


# ==================== SIMULAÇÃO (mundo + controle) ====================
class Simulacao:
    def __init__(self, seed=None, audio=None, log_estados=False):
        self.rng = random.Random(seed)
        self.t = 0.0
        self.semaforo = Semaforo(self.rng)
        self.trafego = Trafego(self.rng)
        self.obstaculos = criar_cenario()
        self.planejador = PlanejadorAStar()
        self.planejador.construir(self.obstaculos_mapa())
        self.metricas = Metricas()
        self.audio = audio
        self.log_estados = log_estados
        self.log = []
        x, y = DESTINOS["Casa"]
        self.robo = RoboCaoGuia(x, y)
        self.tutor = Tutor(x - GUIA, y)
        self.local_atual = "Casa"
        self.fila_destinos = []
        self.espera_fila = 0.0
        self.nivel_alerta = "VERDE"
        self.t_beep = 0.0
        self.bloqueio_ativo = False
        self.toque_ativo = False
        self.reg_colisoes = set()
        self.reg_quase = set()
        self.ultimo_evento = ""

    # ---------- utilidades ----------
    def obstaculos_mapa(self):
        """Obstáculos que o robô conhece: os do mapa + os já vistos pelo LiDAR."""
        return [o for o in self.obstaculos if o.get("conhecido", True) or o.get("visto")]

    def aquecer(self, segundos):
        """Deixa o trânsito circular antes de começar (sem contar nas métricas)."""
        for _ in range(int(segundos / DT_FIXO)):
            self.passo(DT_FIXO)

    def _mudar(self, novo, motivo):
        r = self.robo
        if novo == r.estado:
            return
        self.log.append((self.t, r.estado, novo, motivo))
        if self.log_estados:
            print(f"[{self.t:7.2f} s] {r.estado:>18} -> {novo:<18} | {motivo}")
        r.estado = novo
        r.motivo = motivo
        if novo == "NAVEGANDO":
            r.t_nav = 0.0

    # ---------- destinos ----------
    def definir_destino(self, nome, ponto=None):
        r = self.robo
        if r.autorizado:                     # no meio da faixa: termina a travessia antes
            self.fila_destinos.insert(0, nome if ponto is None else (nome, ponto))
            return False
        ponto = DESTINOS[nome] if ponto is None else ponto
        r.destino, r.destino_nome = ponto, nome
        self.metricas.iniciar_viagem(self.t, self.local_atual, nome)
        self._mudar("PLANEJANDO", f"destino '{nome}' selecionado")
        self.planejador.construir(self.obstaculos_mapa())
        segs = self.planejador.planejar_rota((r.x, r.y), ponto)
        if not segs:
            self._mudar("AGUARDANDO_DESTINO", "A* não encontrou rota")
            self.metricas.encerrar(self.t, concluida=False)
            return False
        r.segmentos, r.seg_idx, r.wp_idx = segs, 0, 0
        r.t_desvio = 0.0
        travessia = any(s["tipo"] == "travessia" for s in segs)
        n = sum(len(s["pontos"]) for s in segs if s["tipo"] == "caminho")
        self._mudar("NAVEGANDO", f"rota A* com {n} pontos" + (" + travessia na faixa" if travessia else ""))
        return True

    def ida_e_volta(self, ida="Mercado", volta="Casa"):
        self.fila_destinos = [volta]
        self.definir_destino(ida)

    def adicionar_obstaculo(self, x, y, tipo="solo", tamanho=44, surpresa=False):
        self.obstaculos.append({"rect": pygame.Rect(int(x - tamanho / 2), int(y - tamanho / 2), tamanho, tamanho),
                                "tipo": tipo, "nome": "Obstáculo", "conhecido": False, "surpresa": surpresa})

    def adicionar_obstaculo_surpresa(self):
        """Benchmark: coloca uma caixa desconhecida sobre a rota (sem bloquear todas as rotas)."""
        r = self.robo
        caminhos = [s["pontos"] for s in r.segmentos if s["tipo"] == "caminho" and len(s["pontos"]) > 25]
        if not caminhos:
            return False
        for _ in range(12):
            pts = self.rng.choice(caminhos)
            x, y = pts[int(len(pts) * self.rng.uniform(0.3, 0.7))]
            perto = [(r.x, r.y), r.destino] + [p for v in PONTOS_TRAVESSIA.values() for p in v]
            if any(math.hypot(x - px, y - py) < 80 for px, py in perto):
                continue
            teste = pygame.Rect(int(x - 18), int(y - 18), 36, 36)
            obs_teste = self.obstaculos_mapa() + [{"rect": teste, "tipo": "solo"}]
            plan = PlanejadorAStar()
            plan.construir(obs_teste)
            if plan.planejar_rota((r.x, r.y), r.destino):
                self.adicionar_obstaculo(x, y, "solo", 36, surpresa=True)
                return True
        return False

    def remover_surpresas(self):
        self.obstaculos = [o for o in self.obstaculos if not o.get("surpresa")]

    def teleportar(self, nome):
        x, y = DESTINOS[nome]
        r = self.robo
        r.x, r.y, r.angulo = x, y, 0.0
        r.autorizado = False
        r.hist_lidar.clear()
        self.tutor.x, self.tutor.y = x - GUIA, y
        self._mudar("AGUARDANDO_DESTINO", "robô reposicionado após falha")
        self.local_atual = nome

    # ---------- Marco 1: barreira do meio-fio ----------
    def aplicar_barreira(self, x_ant, y_ant, x, y):
        """Impede o robô de descer o meio-fio fora da faixa ou sem autorização."""
        na_rua = RUA_Y - MARGEM_BARREIRA < y < RUA_FIM + MARGEM_BARREIRA
        if not na_rua:
            return x, y, False
        x_min, x_max = FAIXA_X + 10, FAIXA_X + FAIXA_LARGURA - 10
        if self.robo.autorizado:
            if x_min <= x <= x_max:
                return x, y, False
            return limitar(x, x_min, x_max), y, True      # na travessia não sai da faixa
        if y_ant <= RUA_Y + RUA_ALTURA / 2:
            y = RUA_Y - MARGEM_BARREIRA
        else:
            y = RUA_FIM + MARGEM_BARREIRA
        return x, y, True

    def _resolver_colisao_estatica(self, x, y, x_ant, y_ant):
        for o in self.obstaculos:
            if o["tipo"] not in ("solo", "edificacao"):
                continue                # o robô é baixo: passa por baixo de obstáculos suspensos
            r = o["rect"]
            d = dist_ponto_rect(x, y, r)
            if d < R_FISICO:
                if d < 1e-6:
                    return x_ant, y_ant
                cx, cy = limitar(x, r.left, r.right), limitar(y, r.top, r.bottom)
                x = cx + (x - cx) / d * R_FISICO
                y = cy + (y - cy) / d * R_FISICO
        return x, y

    # ---------- Marco 3: zona varrida ----------
    def _zona_varrida_perigo(self):
        r, tu = self.robo, self.tutor
        corpo = pygame.Rect(int(r.x - R_ROBO), int(r.y - R_ROBO), 2 * R_ROBO, 2 * R_ROBO)
        zonas = [corpo, pygame.Rect(int(tu.x - R_TUTOR), int(tu.y - R_TUTOR), 2 * R_TUTOR, 2 * R_TUTOR)]
        atravessando = r.estado == "ATRAVESSANDO" or (r.estado == "FREIO_EMERGENCIA" and
                                                     r.estado_retorno == "ATRAVESSANDO")
        if atravessando:      # projeta também para onde o robô vai em 0,5 s
            px = r.x + math.cos(r.angulo) * VEL_ROBO * 0.5
            py = r.y + math.sin(r.angulo) * VEL_ROBO * 0.5
            zonas.append(corpo.union(pygame.Rect(int(px - R_ROBO), int(py - R_ROBO), 2 * R_ROBO, 2 * R_ROBO)))
        for c in self.trafego.carros:
            z = c.zona_varrida(HORIZONTE_PREDICAO)
            if z and any(z.colliderect(q) for q in zonas):
                return True, c
        return False, None

    def _faixa_livre(self):
        area = pygame.Rect(FAIXA_X - 12, RUA_Y, FAIXA_LARGURA + 24, RUA_ALTURA)
        for c in self.trafego.carros:
            if c.rect().colliderect(area):
                return False
            z = c.zona_varrida(2.0)
            if z and z.colliderect(area):
                return False
        return True

    # ---------- controle (máquina de estados) ----------
    def _perseguir(self, tx, ty, final):
        r = self.robo
        d = math.hypot(tx - r.x, ty - r.y)
        erro = normalizar_angulo(math.atan2(ty - r.y, tx - r.x) - r.angulo)
        w = limitar(5.0 * erro, -W_MAX, W_MAX)
        v = 0.0 if abs(erro) > 1.0 else VEL_ROBO * max(0.25, math.cos(erro))
        if final and d < 40:
            v *= max(0.3, d / 40)
        return v, w

    def _reancorar(self):
        r = self.robo
        seg = r.segmentos[r.seg_idx]
        if seg["tipo"] != "caminho":
            return
        pts = seg["pontos"]
        r.wp_idx = min(range(r.wp_idx, len(pts)), key=lambda k: math.hypot(pts[k][0] - r.x, pts[k][1] - r.y))

    def _seguir_caminho(self):
        r = self.robo
        pts = r.segmentos[r.seg_idx]["pontos"]
        while r.wp_idx < len(pts) - 1 and math.hypot(pts[r.wp_idx][0] - r.x, pts[r.wp_idx][1] - r.y) < LOOKAHEAD:
            r.wp_idx += 1
        tx, ty = pts[r.wp_idx]
        ultimo = r.wp_idx == len(pts) - 1
        if ultimo and math.hypot(tx - r.x, ty - r.y) < TOL_PONTO:
            if r.seg_idx + 1 < len(r.segmentos):
                r.seg_idx += 1
                r.wp_idx = 0
                self._mudar("AGUARDANDO_SINAL", "chegou à linha de espera da faixa (24 px antes do meio-fio)")
            else:
                self._mudar("DESTINO_ALCANCADO", f"chegou a {r.destino_nome}")
                self.metricas.encerrar(self.t, concluida=True)
                self.local_atual = r.destino_nome
            return 0.0, 0.0
        return self._perseguir(tx, ty, final=ultimo)

    def _replanejar(self, motivo):
        r = self.robo
        self._mudar("REPLANEJANDO", motivo)
        self.metricas.inc("replans")
        self.ultimo_evento = "Rota recalculada pelo A*"
        self.planejador.construir(self.obstaculos_mapa())
        segs = self.planejador.planejar_rota((r.x, r.y), r.destino)
        r.t_desvio = 0.0
        if segs:
            r.segmentos, r.seg_idx, r.wp_idx = segs, 0, 0
            self._mudar("NAVEGANDO", "nova rota A* incluindo os obstáculos vistos pelo LiDAR")
        else:
            self._mudar("DESVIO_LOCAL", "A* sem rota: mantendo evasão local")

    def _controlar(self, dt):
        r, tu = self.robo, self.tutor
        L = r.leituras_lidar
        mais_perto = min(L[8:11], key=lambda l: l["distancia"])
        min_cen, tipo_cen = mais_perto["distancia"], mais_perto["tipo"]
        # Camada reativa: reage só ao que NÃO está no mapa do A* (obstáculos novos).
        # Os conhecidos já foram contornados pelo C-Space da rota global.
        obst_frente = (tipo_cen not in (None, "veiculo") and not mais_perto["conhecido"]
                       and min_cen < LIMIAR_DESVIO)
        min_esq = min(l["distancia"] for l in L[:7])
        min_dir = min(l["distancia"] for l in L[12:])
        perigo, carro = self._zona_varrida_perigo()
        r.carro_perigo = carro
        v = w = 0.0
        e = r.estado

        if e == "FREIO_EMERGENCIA":
            if perigo:
                r.t_seguro = 0.0
            else:
                r.t_seguro += dt
                if r.t_seguro >= 0.3:
                    self._mudar(r.estado_retorno, "zona varrida livre: nenhum veículo em rota de colisão")

        elif perigo and e in ("NAVEGANDO", "DESVIO_LOCAL", "ATRAVESSANDO"):
            r.estado_retorno = "ATRAVESSANDO" if e == "ATRAVESSANDO" else "NAVEGANDO"
            r.t_seguro = 0.0
            tipo = "infrator " if carro.infrator else ""
            self._mudar("FREIO_EMERGENCIA", f"veículo {tipo}com zona varrida (1,0 s) sobre o robô/tutor")
            self.metricas.inc("freios")

        elif e == "AGUARDANDO_SINAL":
            sx, sy = r.segmentos[r.seg_idx]["saida"]
            w = limitar(4.0 * normalizar_angulo(math.atan2(sy - r.y, sx - r.x) - r.angulo), -W_MAX, W_MAX)
            s = self.semaforo
            if s.fase == "PEDESTRE" and s.restante > LIMITE_TRAVESSIA and self._faixa_livre():
                r.autorizado = True
                self._mudar("ATRAVESSANDO", f"fase PEDESTRE com {s.restante:.1f} s restantes "
                                            f"(> {LIMITE_TRAVESSIA:.2f} s) e faixa livre")

        elif e == "ATRAVESSANDO":
            sx, sy = r.segmentos[r.seg_idx]["saida"]
            if math.hypot(sx - r.x, sy - r.y) < TOL_PONTO:
                r.autorizado = False
                r.seg_idx += 1
                r.wp_idx = 0
                self._mudar("NAVEGANDO", "chegou à calçada oposta com o tutor fora da via")
            else:
                v, w = self._perseguir(sx, sy, final=False)

        elif e == "NAVEGANDO":
            r.t_nav += dt
            if r.t_nav > 2.0:
                r.t_desvio = 0.0
            if obst_frente:
                r.t_livre = 0.0
                self._mudar("DESVIO_LOCAL", f"LiDAR: obstáculo ({tipo_cen}) a {min_cen:.0f} px à frente")
            else:
                v, w = self._seguir_caminho()

        elif e == "DESVIO_LOCAL":
            r.t_desvio += dt
            if r.t_desvio > TEMPO_MAX_DESVIO:
                self._replanejar(f"preso em desvio local por mais de {TEMPO_MAX_DESVIO} s")
            elif not obst_frente and (min_cen > LIMIAR_DESVIO + 14 or mais_perto["conhecido"]
                                      or tipo_cen is None):
                r.t_livre += dt
                v = 0.5 * VEL_ROBO
                if r.t_livre > 0.35:
                    self._reancorar()
                    self._mudar("NAVEGANDO", "frente livre: retomando a rota global")
            else:
                r.t_livre = 0.0
                w = 2.4 if min_dir > min_esq else -2.4
                # O LiDAR não enxerga o meio-fio: perto da rua, gira sempre para longe dela
                dist_meio_fio = (RUA_Y - r.y) if lado_da_rua(r.y) == "norte" else (r.y - RUA_FIM)
                if dist_meio_fio < 45:
                    longe_da_rua = -math.pi / 2 if lado_da_rua(r.y) == "norte" else math.pi / 2
                    w = 2.4 if normalizar_angulo(longe_da_rua - r.angulo) > 0 else -2.4
                v = 0.0 if min_cen < 24 else 0.35 * VEL_ROBO

        # Marco 4: acoplamento físico do tutor (reduz a velocidade se a guia esticar)
        r.tensao = tu.tensao(r)
        if r.tensao > FOLGA_GUIA:
            v *= max(0.15, 1.0 - (r.tensao - FOLGA_GUIA) / 25.0)

        r.angulo = normalizar_angulo(r.angulo + w * dt)
        nx = r.x + math.cos(r.angulo) * v * dt
        ny = r.y + math.sin(r.angulo) * v * dt
        nx, ny, bloqueou = self.aplicar_barreira(r.x, r.y, nx, ny)
        if bloqueou and not self.bloqueio_ativo:
            self.metricas.inc("bloqueios")
        self.bloqueio_ativo = bloqueou
        nx, ny = self._resolver_colisao_estatica(nx, ny, r.x, r.y)
        andou = math.hypot(nx - r.x, ny - r.y)
        r.x, r.y = nx, ny
        r.vel_atual = andou / dt if dt > 0 else 0.0
        r.passo_animacao += andou * 0.1
        self.metricas.somar_distancia(andou)

    # ---------- colisões ----------
    def _verificar_colisoes(self):
        r, tu = self.robo, self.tutor
        for c in self.trafego.carros:
            rc = c.rect()
            for nome, px, py, pr in (("robo", r.x, r.y, R_ROBO), ("tutor", tu.x, tu.y, R_TUTOR)):
                d = dist_ponto_rect(px, py, rc)
                chave = (c.id, nome)
                if d < pr:
                    if chave not in self.reg_colisoes:
                        self.reg_colisoes.add(chave)
                        self.metricas.inc("colisoes")
                        self.ultimo_evento = f"COLISÃO com veículo ({nome})"
                        c.v = 0.0
                elif d < pr + DIST_QUASE and c.v > 15:
                    if chave not in self.reg_quase and chave not in self.reg_colisoes:
                        self.reg_quase.add(chave)
                        self.metricas.inc("quase")
                        self.ultimo_evento = f"Quase-colisão ({nome})"
        toque = any(o["tipo"] == "suspenso" and dist_ponto_rect(tu.x, tu.y, o["rect"]) < R_TUTOR
                    for o in self.obstaculos)
        if toque and not self.toque_ativo:
            self.metricas.inc("toques_cabeca")
        self.toque_ativo = toque

    # ---------- alertas + áudio estéreo ----------
    def _atualizar_alertas(self, dt):
        r = self.robo
        L = r.leituras_lidar
        cen = min(L[7:12], key=lambda l: l["distancia"])
        esq = min(L[:7], key=lambda l: l["distancia"])
        dir_ = min(L[12:], key=lambda l: l["distancia"])
        pan, som = 0.0, None
        e = r.estado

        if e == "FREIO_EMERGENCIA":
            nivel, msg = "VERMELHO", "FREIO DE EMERGÊNCIA! Veículo em rota de colisão."
            if r.carro_perigo:
                c = r.carro_perigo
                pan = math.sin(normalizar_angulo(math.atan2(c.y - r.y, c.x - r.x) - r.angulo))
        elif e in ("DESVIO_LOCAL", "REPLANEJANDO") or cen["distancia"] < 45 and cen["tipo"] not in (None, "veiculo"):
            nivel = "VERMELHO"
            msg = ("ALERTA CABEÇA: galho/toldo baixo! Desviando..." if cen["tipo"] == "suspenso"
                   else "OBSTÁCULO À FRENTE: contornando...")
            pan = math.sin(normalizar_angulo(cen["angulo"] - r.angulo))
        elif e == "AGUARDANDO_SINAL":
            nivel, som = "LARANJA", "ESPERA"
            s = self.semaforo
            msg = (f"Sinal aberto, mas só {s.restante:.1f} s. Aguardando próximo ciclo."
                   if s.fase == "PEDESTRE" else "Aguardando sinal de pedestre.")
        elif e == "ATRAVESSANDO":
            nivel, msg = "VERDE", "Atravessando na faixa de pedestres..."
        elif e == "DESTINO_ALCANCADO":
            nivel, msg = "VERDE", f"DESTINO ALCANÇADO: {r.destino_nome}!"
        elif esq["distancia"] < 34 and esq["tipo"] not in (None, "veiculo"):
            nivel, msg, pan = "LARANJA", "Obstáculo à esquerda.", -0.8
        elif dir_["distancia"] < 34 and dir_["tipo"] not in (None, "veiculo"):
            nivel, msg, pan = "LARANJA", "Obstáculo à direita.", 0.8
        elif e == "AGUARDANDO_DESTINO":
            nivel, msg = "VERDE", "Pronto. Escolha um destino (1-4)."
        else:
            nivel, msg = "VERDE", "Caminho livre. Seguindo a rota (piso tátil)."

        if nivel == "VERMELHO" and self.nivel_alerta != "VERMELHO":
            self.metricas.inc("alertas")
        self.nivel_alerta = nivel
        r.cor_alerta = {"VERDE": VERDE_LIVRE, "LARANJA": LARANJA_ALERTA, "VERMELHO": VERMELHO_PERIGO}[nivel]
        r.status_assistivo = msg

        self.t_beep -= dt
        if self.audio and nivel != "VERDE" and self.t_beep <= 0:
            tipo = som or nivel
            self.audio.tocar(tipo, limitar(pan, -1, 1))
            self.t_beep = {"VERMELHO": 0.25, "LARANJA": 0.6, "ESPERA": 1.0}[tipo]

    def _processar_fila(self, dt):
        r = self.robo
        if not self.fila_destinos or r.autorizado:
            return
        if r.estado in ("DESTINO_ALCANCADO", "AGUARDANDO_DESTINO"):
            self.espera_fila += dt
            if self.espera_fila > 1.0:
                self.espera_fila = 0.0
                prox = self.fila_destinos.pop(0)
                if isinstance(prox, tuple):
                    self.definir_destino(prox[0], prox[1])
                else:
                    self.definir_destino(prox)

    # ---------- passo de simulação ----------
    def passo(self, dt):
        self.t += dt
        self.semaforo.atualizar(dt)
        r, tu = self.robo, self.tutor
        self.trafego.atualizar(dt, self.semaforo, [(r.x, r.y, R_ROBO), (tu.x, tu.y, R_TUTOR)])
        r.ler_lidar(self.obstaculos, self.trafego.carros, self.rng)
        self._controlar(dt)
        tu.atualizar(dt, r)
        self._verificar_colisoes()
        self._atualizar_alertas(dt)
        self._processar_fila(dt)


# ==================== RENDERIZAÇÃO ====================
def desenhar_ambiente_urbano(tela):
    tela.fill(CALCADA_CLARA)
    pygame.draw.rect(tela, GRAMA, (0, 0, AREA_MAPA_LARGURA, 28))
    pygame.draw.rect(tela, GRAMA, (0, ALTURA - 28, AREA_MAPA_LARGURA, 28))
    pygame.draw.rect(tela, ASFALTO, (0, RUA_Y, AREA_MAPA_LARGURA, RUA_ALTURA))
    pygame.draw.line(tela, MEIO_FIO, (0, RUA_Y), (AREA_MAPA_LARGURA, RUA_Y), 4)
    pygame.draw.line(tela, MEIO_FIO, (0, RUA_FIM), (AREA_MAPA_LARGURA, RUA_FIM), 4)
    for x in range(15, AREA_MAPA_LARGURA - 20, 45):
        if not (540 <= x <= 700):
            pygame.draw.line(tela, BRANCO, (x, RUA_Y + RUA_ALTURA // 2), (x + 22, RUA_Y + RUA_ALTURA // 2), 3)
    for y in range(RUA_Y + 12, RUA_FIM - 12, 22):
        pygame.draw.rect(tela, BRANCO, (FAIXA_X, y, FAIXA_LARGURA, 12))
    # linhas de retenção
    pygame.draw.line(tela, BRANCO, (LINHA_RETENCAO[1], RUA_Y + RUA_ALTURA // 2 + 4), (LINHA_RETENCAO[1], RUA_FIM - 4), 4)
    pygame.draw.line(tela, BRANCO, (LINHA_RETENCAO[-1], RUA_Y + 4), (LINHA_RETENCAO[-1], RUA_Y + RUA_ALTURA // 2 - 4), 4)
    for t in TATIL_RECTS:
        pygame.draw.rect(tela, PISO_TATIL, t)


def desenhar_semaforos(tela, sem, fonte):
    sinal = sem.sinal_veiculos()
    cores = {"VERMELHO": VERMELHO_PERIGO, "AMARELO": AMARELO_SINAL, "VERDE": VERDE_LIVRE}
    for (x, y) in [(LINHA_RETENCAO[1] - 22, RUA_FIM + 8), (LINHA_RETENCAO[-1] + 32, RUA_Y - 48)]:
        pygame.draw.rect(tela, PRETO, (x, y, 14, 40), border_radius=3)
        for k, nome in enumerate(["VERMELHO", "AMARELO", "VERDE"]):
            cor = cores[nome] if sinal == nome else (60, 60, 60)
            pygame.draw.circle(tela, cor, (x + 7, y + 7 + k * 13), 5)
    ped = sem.fase == "PEDESTRE"
    for (x, y) in [(FAIXA_X + FAIXA_LARGURA + 6, RUA_Y - 30), (FAIXA_X - 26, RUA_FIM + 6)]:
        pygame.draw.rect(tela, PRETO, (x, y, 20, 24), border_radius=3)
        pygame.draw.circle(tela, VERDE_LIVRE if ped else VERMELHO_PERIGO, (x + 10, y + 12), 7)
        if ped:
            txt = fonte.render(f"{sem.restante:.0f}", True, BRANCO)
            tela.blit(txt, (x + 10 - txt.get_width() // 2, y + 25))


def desenhar_obstaculos(tela, obstaculos, fonte):
    for obs in obstaculos:
        rect = obs["rect"]
        if obs["tipo"] == "edificacao":
            pygame.draw.rect(tela, (96, 84, 76), rect, border_radius=4)
            pygame.draw.rect(tela, (60, 52, 48), rect, 3, border_radius=4)
            lbl = fonte.render(obs["nome"].upper(), True, BRANCO)
            tela.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - 7))
        elif obs["tipo"] == "suspenso":
            pygame.draw.rect(tela, (90, 95, 102), rect.move(5, 5), border_radius=12)
            pygame.draw.rect(tela, ROXO_SUSPENSO, rect, border_radius=12)
            pygame.draw.rect(tela, BRANCO, rect, 2, border_radius=12)
            lbl = fonte.render("ALTO", True, BRANCO)
            tela.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - 7))
        else:
            cor_borda = BRANCO if obs.get("conhecido", True) else LARANJA_ALERTA
            pygame.draw.rect(tela, (70, 74, 82), rect, border_radius=5)
            pygame.draw.rect(tela, cor_borda, rect, 2, border_radius=5)
            lbl = fonte.render("SOLO" if obs.get("conhecido", True) else "NOVO", True, BRANCO)
            tela.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - 7))


def desenhar_destinos(tela, robo, fonte):
    for k, (nome, (x, y)) in enumerate(DESTINOS.items(), start=1):
        ativo = robo.destino_nome == nome and robo.estado != "AGUARDANDO_DESTINO"
        cor = VERDE_LIVRE if ativo else (220, 220, 225)
        pygame.draw.circle(tela, cor, (x, y), 13, 3)
        lbl = fonte.render(str(k), True, cor)
        tela.blit(lbl, (x - lbl.get_width() // 2, y - 7))


def desenhar_veiculos(tela, carros, overlay, fonte):
    for c in carros:
        z = c.zona_varrida(HORIZONTE_PREDICAO)
        if z:
            if c.infrator:
                pygame.draw.rect(overlay, (255, 80, 80, 60), z)
            else:
                pygame.draw.rect(overlay, (255, 255, 255, 40), z, 1)
    for c in carros:
        r = c.rect()
        pygame.draw.rect(tela, c.cor, r, border_radius=6)
        vidro_x = r.right - 16 if c.dir > 0 else r.left + 6
        pygame.draw.rect(tela, (150, 200, 230), (vidro_x, r.top + 4, 10, r.height - 8), border_radius=2)
        farol_x = r.right - 2 if c.dir > 0 else r.left + 1
        pygame.draw.rect(tela, (255, 250, 200), (farol_x - 1, r.top + 3, 2, 4))
        pygame.draw.rect(tela, (255, 250, 200), (farol_x - 1, r.bottom - 7, 2, 4))
        if c.infrator:
            pygame.draw.rect(tela, LARANJA_ALERTA, r, 2, border_radius=6)
            tela.blit(fonte.render("!", True, LARANJA_ALERTA), (r.centerx - 2, r.top - 15))


def desenhar_rota(tela, robo):
    if robo.estado in ("AGUARDANDO_DESTINO", "DESTINO_ALCANCADO") or not robo.segmentos:
        return
    for k in range(robo.seg_idx, len(robo.segmentos)):
        seg = robo.segmentos[k]
        if seg["tipo"] == "caminho":
            ini = robo.wp_idx if k == robo.seg_idx else 0
            for p in seg["pontos"][ini::2]:
                pygame.draw.circle(tela, CIANO_ROTA, (int(p[0]), int(p[1])), 2)
        else:
            (x1, y1), (x2, y2) = seg["espera"], seg["saida"]
            for t in range(0, 100, 8):
                a, b = t / 100, min(1.0, (t + 4) / 100)
                pygame.draw.line(tela, CIANO_ROTA, (x1 + (x2 - x1) * a, y1 + (y2 - y1) * a),
                                 (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), 2)


def superficie_grade(planejador):
    s = pygame.Surface((AREA_MAPA_LARGURA, ALTURA), pygame.SRCALPHA)
    for n, c in enumerate(planejador.custo):
        x, y = (n % planejador.cols) * CELULA, (n // planejador.cols) * CELULA
        if c == math.inf:
            s.fill((220, 40, 40, 55), (x, y, CELULA, CELULA))
        elif c < 1:
            s.fill((255, 220, 0, 70), (x, y, CELULA, CELULA))
    return s


NOMES_ESTADO = {
    "AGUARDANDO_DESTINO": BRANCO, "PLANEJANDO": CIANO_ROTA, "NAVEGANDO": VERDE_LIVRE,
    "DESVIO_LOCAL": LARANJA_ALERTA, "REPLANEJANDO": CIANO_ROTA, "AGUARDANDO_SINAL": AMARELO_SINAL,
    "ATRAVESSANDO": VERDE_LIVRE, "FREIO_EMERGENCIA": VERMELHO_PERIGO, "DESTINO_ALCANCADO": VERDE_LIVRE,
}


def desenhar_painel(tela, sim, fontes, escala, pausado):
    f_tit, f_txt, f_peq = fontes
    r, m, s = sim.robo, sim.metricas, sim.semaforo
    px = AREA_MAPA_LARGURA
    pygame.draw.rect(tela, PRETO, (px, 0, LARGURA - px, ALTURA))
    pygame.draw.line(tela, BRANCO, (px, 0), (px, ALTURA), 2)
    x = px + 14
    y = 12
    tela.blit(f_tit.render("TELEMETRIA DOG-IA V2", True, CORPO_ROBO), (x, y))
    y += 30

    def linha(rotulo, valor, cor=BRANCO, fonte=None):
        nonlocal y
        tela.blit(f_txt.render(rotulo, True, CINZA_TEXTO), (x, y))
        tela.blit((fonte or f_txt).render(valor, True, cor), (x + 92, y + (2 if fonte else 0)))
        y += 19

    linha("Estado:", r.estado, NOMES_ESTADO.get(r.estado, BRANCO), f_peq)
    linha("Destino:", r.destino_nome or "-")
    cor_fase = {"VERDE": VERDE_LIVRE, "AMARELO": AMARELO_SINAL, "PEDESTRE": CIANO_ROTA}.get(s.fase, VERMELHO_PERIGO)
    linha("Semáforo:", f"{s.fase} ({s.restante:.1f}s)", cor_fase)
    linha("Lim. travessia:", f"{LIMITE_TRAVESSIA:.2f} s")
    linha("Velocidade:", f"{r.vel_atual:.0f} px/s ({r.vel_atual / PX_POR_METRO:.2f} m/s)")
    min_d = min(l["distancia"] for l in r.leituras_lidar) if r.leituras_lidar else ALCANCE_LIDAR
    linha("LiDAR (filtr.):", f"{min_d:.0f} px")
    linha("Tensão guia:", f"{r.tensao:.1f} px", VERMELHO_PERIGO if r.tensao > FOLGA_GUIA else BRANCO)
    y += 4

    pygame.draw.rect(tela, r.cor_alerta, (x, y, 232, 62), border_radius=8)
    palavras, linha_atual, ya = r.status_assistivo.split(" "), "", y + 6
    for p in palavras:
        if len(linha_atual + p) < 30:
            linha_atual += p + " "
        else:
            tela.blit(f_txt.render(linha_atual, True, PRETO), (x + 8, ya))
            ya += 17
            linha_atual = p + " "
    tela.blit(f_txt.render(linha_atual, True, PRETO), (x + 8, ya))
    y += 72

    tela.blit(f_tit.render("MÉTRICAS", True, CORPO_ROBO), (x, y))
    y += 26
    va = m.atual
    linha("Viagens ok:", f"{m.concluidas}")
    linha("Tempo viagem:", f"{(sim.t - va['t0']) if va else (m.viagens[-1]['tempo'] if m.viagens else 0):.1f} s")
    linha("Distância:", f"{m.total['dist'] / PX_POR_METRO:.1f} m")
    linha("Alertas verm.:", f"{m.total['alertas']}")
    linha("Freios emerg.:", f"{m.total['freios']}")
    linha("Colisões:", f"{m.total['colisoes']}  quase: {m.total['quase']}",
          VERMELHO_PERIGO if m.total["colisoes"] else BRANCO)
    linha("Replanejam.:", f"{m.total['replans']}")
    y += 6

    tela.blit(f_tit.render("CONTROLES", True, CORPO_ROBO), (x, y))
    y += 26
    for texto in ["1 Mercado  2 Farmácia", "3 Padaria  4 Casa", "V: ida e volta (Mercado/Casa)",
                  "Clique esq.: destino livre", "Clique dir.: novo obstáculo",
                  "G: grade A*   M: som   P: pausa", "+/-: velocidade   R: reiniciar"]:
        tela.blit(f_peq.render(texto, True, BRANCO), (x, y))
        y += 16
    rodape = f"Sim: {sim.t:6.1f} s   {escala:g}x" + ("   PAUSADO" if pausado else "")
    tela.blit(f_peq.render(rodape, True, CINZA_TEXTO), (x, ALTURA - 20))


def renderizar(tela, sim, fontes, overlay, grade_surf=None, escala=1.0, pausado=False):
    desenhar_ambiente_urbano(tela)
    if grade_surf is not None:
        tela.blit(grade_surf, (0, 0))
    desenhar_rota(tela, sim.robo)
    desenhar_destinos(tela, sim.robo, fontes[2])
    desenhar_obstaculos(tela, sim.obstaculos, fontes[2])
    overlay.fill((0, 0, 0, 0))
    desenhar_veiculos(tela, sim.trafego.carros, overlay, fontes[1])
    tela.blit(overlay, (0, 0))
    desenhar_semaforos(tela, sim.semaforo, fontes[2])
    sim.robo.desenhar(tela, sim.tutor)
    for nome, (x, y) in DESTINOS.items():
        lbl = fontes[2].render(nome, True, BRANCO)
        tela.blit(lbl, (x - lbl.get_width() // 2, y + 15))
    desenhar_painel(tela, sim, fontes, escala, pausado)


def criar_fontes():
    return (pygame.font.SysFont("arial", 18, bold=True), pygame.font.SysFont("arial", 14),
            pygame.font.SysFont("arial", 12, bold=True))


# ==================== MODOS DE EXECUÇÃO ====================
def main_interativo(seed=None, som=True):
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("DOG-IA V2 - Simulador Urbano de Cão-Guia Autônomo")
    clock = pygame.time.Clock()
    fontes = criar_fontes()
    audio = AudioEstereo(som)
    overlay = pygame.Surface((AREA_MAPA_LARGURA, ALTURA), pygame.SRCALPHA)

    def nova_sim():
        s = Simulacao(seed=seed, audio=audio, log_estados=True)
        s.aquecer(15.0)
        s.metricas = Metricas()
        return s

    sim = nova_sim()
    escalas = [0.5, 1.0, 2.0, 4.0]
    i_escala = 1
    pausado = False
    mostrar_grade = False
    grade_surf, grade_versao = None, -1
    acumulado = 0.0

    rodando = True
    while rodando:
        dt_real = clock.tick(FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                rodando = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in TECLAS_DESTINO:
                    sim.fila_destinos.clear()
                    sim.definir_destino(TECLAS_DESTINO[ev.key])
                elif ev.key == pygame.K_v:
                    sim.ida_e_volta("Mercado", "Casa")
                elif ev.key == pygame.K_g:
                    mostrar_grade = not mostrar_grade
                elif ev.key == pygame.K_p:
                    pausado = not pausado
                elif ev.key == pygame.K_m:
                    audio.mudo = not audio.mudo
                elif ev.key == pygame.K_r:
                    sim = nova_sim()
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    i_escala = min(len(escalas) - 1, i_escala + 1)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    i_escala = max(0, i_escala - 1)
                elif ev.key == pygame.K_ESCAPE:
                    rodando = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if mx < AREA_MAPA_LARGURA:
                    if ev.button == 1:
                        sim.fila_destinos.clear()
                        sim.definir_destino("Ponto livre", (mx, my))
                    elif ev.button == 3:
                        sim.adicionar_obstaculo(mx, my, sim.rng.choice(["solo", "suspenso"]))

        if not pausado:
            acumulado += min(dt_real, 0.05) * escalas[i_escala]
            while acumulado >= DT_FIXO:
                sim.passo(DT_FIXO)
                acumulado -= DT_FIXO

        if mostrar_grade and grade_versao != sim.planejador.versao:
            grade_surf, grade_versao = superficie_grade(sim.planejador), sim.planejador.versao
        renderizar(tela, sim, fontes, overlay, grade_surf if mostrar_grade else None, escalas[i_escala], pausado)
        pygame.display.flip()
    pygame.quit()


def executar_benchmark(n, seed, salvar_csv=True, log_estados=False):
    """Modo headless: N viagens com passo fixo, sem janela."""
    timeout = 150.0
    sim = Simulacao(seed=seed, log_estados=log_estados)
    sim.aquecer(20.0)
    sim.metricas = Metricas()
    nomes = list(DESTINOS)
    print(f"\nDOG-IA V2 - benchmark: {n} viagens, seed={seed}\n")
    print(f"{'#':>3}  {'Origem -> Destino':<22} {'Ok':<4} {'Tempo(s)':>8} {'Dist(m)':>8} "
          f"{'Alert':>5} {'Freio':>5} {'Colis':>5} {'Quase':>5} {'Repl':>4}")
    for i in range(n):
        origem = sim.local_atual
        destino = sim.rng.choice([d for d in nomes if d != origem])
        sim.definir_destino(destino)
        if sim.rng.random() < 0.5:
            sim.adicionar_obstaculo_surpresa()
        t0 = sim.t
        while sim.robo.estado != "DESTINO_ALCANCADO" and sim.t - t0 < timeout:
            sim.passo(DT_FIXO)
        if sim.robo.estado != "DESTINO_ALCANCADO":
            sim.metricas.encerrar(sim.t, concluida=False)
            sim.teleportar(destino)
        sim.remover_surpresas()
        v = sim.metricas.viagens[-1]
        v["sucesso"] = v["concluida"] and v["colisoes"] == 0
        print(f"{i + 1:>3}  {origem + ' -> ' + destino:<22} {'sim' if v['sucesso'] else 'NÃO':<4} "
              f"{v['tempo']:>8.1f} {v['dist'] / PX_POR_METRO:>8.1f} {v['alertas']:>5} {v['freios']:>5} "
              f"{v['colisoes']:>5} {v['quase']:>5} {v['replans']:>4}")

    vs = sim.metricas.viagens
    ok = [v for v in vs if v["sucesso"]]
    tempos = [v["tempo"] for v in ok]
    media = sum(tempos) / len(tempos) if tempos else 0.0
    dp = math.sqrt(sum((t - media) ** 2 for t in tempos) / len(tempos)) if tempos else 0.0
    tot = lambda k: sum(v[k] for v in vs)
    print("\n================ RESUMO ================")
    print(f"Seed:                    {seed}")
    print(f"Taxa de sucesso:         {len(ok)}/{len(vs)} = {100 * len(ok) / len(vs):.1f} %")
    print(f"Tempo médio (sucesso):   {media:.1f} s  (desvio padrão {dp:.1f} s)")
    print(f"Distância total:         {sum(v['dist'] for v in vs) / PX_POR_METRO:.1f} m")
    print(f"Colisões:                {tot('colisoes')}")
    print(f"Quase-colisões:          {tot('quase')}")
    print(f"Freios de emergência:    {tot('freios')}")
    print(f"Alertas vermelhos:       {tot('alertas')}")
    print(f"Replanejamentos:         {tot('replans')}")
    print(f"Bloqueios de meio-fio:   {tot('bloqueios')}")
    print(f"Toques de cabeça:        {tot('toques_cabeca')}")
    print("========================================\n")

    if salvar_csv:
        nome = f"benchmark_seed{seed}.csv"
        with open(nome, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["viagem", "origem", "destino", "sucesso", "tempo_s", "dist_m", "alertas", "freios",
                        "colisoes", "quase_colisoes", "replanejamentos", "bloqueios_meio_fio"])
            for k, v in enumerate(vs, 1):
                w.writerow([k, v["origem"], v["destino"], int(v["sucesso"]), f"{v['tempo']:.2f}",
                            f"{v['dist'] / PX_POR_METRO:.2f}", v["alertas"], v["freios"], v["colisoes"],
                            v["quase"], v["replans"], v["bloqueios"]])
        print(f"Resultados salvos em {nome}")
    return vs


def executar_trace(destino, seed):
    """Uma viagem sem janela imprimindo cada transição de estado (Questão 2)."""
    sim = Simulacao(seed=seed, log_estados=False)
    sim.aquecer(15.0)
    sim.metricas = Metricas()
    sim.log.clear()
    t0 = sim.t
    sim.log_estados = True
    print(f"\nViagem Casa -> {destino} (seed={seed}). Tempo relativo ao início da viagem:\n")
    sim.t = 0.0
    sim.definir_destino(destino)
    while sim.robo.estado != "DESTINO_ALCANCADO" and sim.t < 150:
        sim.passo(DT_FIXO)
    v = sim.metricas.viagens[-1] if sim.metricas.viagens else None
    if v:
        print(f"\nConcluída: {v['concluida']}  tempo={v['tempo']:.1f} s  dist={v['dist'] / PX_POR_METRO:.1f} m")
    _ = t0


def gravar_video(caminho, seed, duracao_alvo=32.0, fps_video=30):
    """Grava a ida e volta (Casa -> Mercado -> Casa) em MP4 usando ffmpeg."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    def preparar():
        s = Simulacao(seed=seed)
        s.aquecer(15.0)
        s.metricas = Metricas()
        s.ida_e_volta("Mercado", "Casa")
        return s

    # 1ª passada (sem desenhar) para medir a duração e escolher a aceleração do vídeo
    s = preparar()
    while not (s.robo.estado == "DESTINO_ALCANCADO" and s.robo.destino_nome == "Casa") and s.t < 400:
        s.passo(DT_FIXO)
    duracao_sim = s.t - 15.0
    escala = max(1.0, duracao_sim / duracao_alvo)
    print(f"Ida e volta dura {duracao_sim:.1f} s simulados -> vídeo em {escala:.2f}x")

    pygame.init()
    tela = pygame.Surface((LARGURA, ALTURA))
    fontes = criar_fontes()
    overlay = pygame.Surface((AREA_MAPA_LARGURA, ALTURA), pygame.SRCALPHA)
    sim = preparar()
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{LARGURA}x{ALTURA}", "-r", str(fps_video), "-i", "-",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
                             caminho], stdin=subprocess.PIPE)
    passos = escala / fps_video / DT_FIXO
    acumulado, extra = 0.0, 0.0
    while True:
        acumulado += passos
        while acumulado >= 1:
            sim.passo(DT_FIXO)
            acumulado -= 1
        renderizar(tela, sim, fontes, overlay, None, round(escala, 1), False)
        proc.stdin.write(pygame.image.tobytes(tela, "RGB"))
        if sim.robo.estado == "DESTINO_ALCANCADO" and sim.robo.destino_nome == "Casa":
            extra += 1 / fps_video
            if extra > 1.5:
                break
        if sim.t > 500:
            break
    proc.stdin.close()
    proc.wait()
    print(f"Vídeo salvo em {caminho}")


def main():
    ap = argparse.ArgumentParser(description="DOG-IA V2 - simulador de cão-guia autônomo")
    ap.add_argument("--benchmark", type=int, metavar="N", help="executa N viagens sem janela")
    ap.add_argument("--seed", type=int, default=None, help="semente do gerador aleatório")
    ap.add_argument("--trace", metavar="DESTINO", help="uma viagem sem janela imprimindo os estados")
    ap.add_argument("--gravar", metavar="ARQUIVO.mp4", help="grava a ida e volta em vídeo (ffmpeg)")
    ap.add_argument("--sem-som", action="store_true", help="desativa o áudio")
    ap.add_argument("--log-estados", action="store_true", help="imprime as transições no benchmark")
    args = ap.parse_args()

    if args.benchmark:
        executar_benchmark(args.benchmark, args.seed, log_estados=args.log_estados)
    elif args.trace:
        executar_trace(args.trace, args.seed)
    elif args.gravar:
        gravar_video(args.gravar, args.seed)
    else:
        main_interativo(args.seed, som=not args.sem_som)


if __name__ == "__main__":
    main()
