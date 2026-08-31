# Resultados — Aula 03

## Laboratório 1
- Resultado observado:
  O script de raycasting com 3 sensores demonstrou corretamente a detecção de obstáculos retangulares e dos limites da tela. O robô variava a orientação conforme o mouse e os feixes mostravam a distância até o obstáculo em tempo real.
- Funcionamento dos sensores:
  Os sensores esquerdo, frontal e direito foram calculados com ângulos de -45°, 0° e +45° em relação à orientação do robô. A leitura era a menor distância detectada até o alcance máximo do sensor.
- Dificuldades encontradas:
  A principal dificuldade foi ajustar a amostragem ao longo do raio para evitar falsos positivos na borda da tela e garantir que a detecção de obstáculo fosse feita em pontos discretizados do feixe.

## Laboratório 2
- Tempo calculado para giro de 90°:
  Utilizando $\omega = 45^\circ/s$, o tempo necessário para girar $90^\circ$ foi:
  $$t = \frac{\Delta\theta}{\omega} = \frac{\pi/2}{\pi/4} = 2.0\ s$$
- Resultado observado:
  A simulação confirmou que a orientação mudou em 90° enquanto a posição x,y permaneceu constante, atendendo ao modelo de rotação in-place.
- Verificação da posição:
  A coordenada final foi mantida igual à inicial, validando a cinemática angular sem translação.

Saída esperada do script:
```text
LAB-2: Rotação In-Place
Ângulo alvo........: 90.0 graus (1.5708 rad)
Velocidade angular.: 45.0 graus/s (0.7854 rad/s)
Tempo necessário...: 2.000 s
RESULTADO: posição final (2.00, 3.00) — igual à inicial
Orientação final: 90.00 graus
```

## Laboratório 3
- Resultado observado:
  O robô com 5 sensores de feixe calculou as distâncias para os obstáculos e desenhou os raios com valores reais, além de aplicar ruído gaussiano simulado às medições.
- Efeito do ruído nas leituras:
  O ruído $N(0, 2.0)$ gerou pequenas variações nas leituras, mostrando que a percepção não é perfeita e que a navegação reativa deve considerar tolerância para ruído.
- Dificuldades encontradas:
  A maior dificuldade foi calibrar a leitura do sensor para que ela não ultrapassasse o alcance máximo e não se tornasse negativa ao aplicar o ruído.

## Laboratório 4
- Resultado observado:
  O veículo de Braitenberg evitou obstáculos de forma reativa e sem planejamento prévio, acelerando uma roda quando detectava obstáculo do lado oposto e girando no próprio eixo quando a frente estava bloqueada.
- Comportamento diante dos obstáculos:
  Quando o obstáculo estava à direita, a roda esquerda aumentava a velocidade, virando o robô para a esquerda; quando estava à esquerda, a roda direita aumentava. Em caso de obstrução frontal, o robô executava um giro brusco para escapar.
- Dificuldades encontradas:
  Foi necessário escolher um ganho adequado para equilibrar a resposta de desvio e a estabilidade do movimento, evitando oscilações excessivas.

## Laboratório 5
- Resultado observado:
  O robô navegou até o ponto clicado e, quando um obstáculo bloqueava o caminho, entrou em um modo de desvio reativo para contornar o obstáculo e retomar a aproximação ao alvo.
- Funcionamento do desvio e retorno ao alvo:
  O controlador proporcional guiou o robo até o alvo; quando algum sensor apontava risco de colisão, o torque repulsivo era somado à velocidade angular e o robô desviava. Quando o caminho estava livre, ele retomava a trajetória ao objetivo.
- Dificuldades encontradas:
  A parte mais delicada foi combinar atração ao alvo com repulsão de emergência sem que o robô ficasse girando excessivamente ou parasse abruptamente.

## Exercício de maior dificuldade
- Exercício escolhido:
  Laboratório 5.
- Motivo:
  Porque ele exige a sobreposição de dois comportamentos: atração ao alvo e desvio reativo. O equilíbrio entre os ganhos e a lógica de prioridade entre “seguir até o alvo” e “evitar colisão” torna o problema mais complexo do que os anteriores.

## Impressões gerais
- Dificuldades técnicas encontradas:
  A maior dificuldade foi a integração entre percepção sensorial, cinemática e controle reativo. Também houve necessidade de ajustar parâmetros como ganhos, limiares e faixas de detecção para obter comportamento estável.
- Conceitos compreendidos:
  Foi possível compreender melhor o uso de raycasting para sensores de distância, a cinemática angular em rotação in-place, o efeito do ruído em medições sensoriais e a lógica de comportamento reativo baseada no paradigma de Braitenberg.
- Pontos que precisam de mais estudo:
  O principal ponto de aprofundamento é a sintonia fina entre ganhos do controlador e a análise da dinâmica do robô em cenários com obstáculos múltiplos e caminhos estreitos.

## Declaração
- Relatório final concluído conforme as atividades da aula.
- Este documento foi elaborado sem uso de ferramentas de Inteligência Artificial.