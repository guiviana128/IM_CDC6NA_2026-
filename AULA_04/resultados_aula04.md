AULA 04 — LABORATÓRIOS
AC-2 — Parte 1

Nesta aula foram desenvolvidos cinco exercícios em Python com Pygame, envolvendo movimentação de robôs, sensores e controle de trajetória.

Exercício 1 — Validador de Pose

Neste exercício foi simulado o movimento de um robô a partir de comandos de velocidade e tempo.

O robô iniciou em:

x = 0.0 m
y = 0.0 m
θ = 0.0 rad

Após os três movimentos, a pose final ficou aproximadamente em:

x = 2.0 m
y = 1.2 m
θ = 1.5708 rad

A simulação apresentou resultado próximo ao valor calculado teoricamente.

Observação: apesar do enunciado citar uma rotação de 45°, os valores informados resultam em aproximadamente 90°.

Exercício 2 — Ackermann

Neste exercício foi simulada a movimentação de um veículo com direção Ackermann.

A velocidade angular foi calculada pela relação:

ω = (v / L) × tan(φ)

O ângulo máximo de esterço foi limitado a 30°.

Também foi possível observar que o veículo Ackermann possui um raio mínimo de curva e não consegue girar parado sobre o próprio eixo como um robô diferencial.

Exercício 3 — Filtro de Sensor

Foi criada uma simulação com 7 feixes de distância cobrindo um campo de visão de 180°.

As leituras receberam ruído aleatório e depois passaram por um filtro.

As leituras menores que 10 px foram descartadas e as maiores que 200 px foram limitadas a 200 px.

Assim foi possível comparar o valor bruto do sensor com o valor já tratado.

Exercício 4 — Braitenberg

Neste exercício os sensores foram ligados diretamente às rodas do mesmo lado.

Sensor esquerdo → roda esquerda
Sensor direito → roda direita

Quando um obstáculo é detectado, a velocidade das rodas muda e o robô altera sua trajetória em direção ao obstáculo.

Esse comportamento representa a atração/agressão proposta no exercício.

Exercício 5 — Centralização no Corredor

O objetivo foi fazer o robô se manter no centro de um corredor usando dois sensores laterais.

O erro de centralização foi calculado por:

e = d_esq - d_dir

A correção angular foi feita por:

ω = Kp × e

Com isso, mesmo começando fora do centro, o robô corrige sua posição durante o movimento.

Conclusão

Os exercícios ajudaram a visualizar na prática conceitos de cinemática, sensores, controle proporcional e comportamento de robôs móveis.

O uso do Pygame facilitou a visualização dos movimentos e das correções realizadas em cada situação.