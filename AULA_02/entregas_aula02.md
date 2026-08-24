1. Estado do Robô e Pose 2D

A pose do robô mostra onde ele está e para qual direção está apontando. No nosso programa, usamos:

[x, y, theta]


x e y representam a posição do robô na tela, enquanto theta representa sua orientação.

2. Cinemática Diferencial

O robô possui duas rodas, uma esquerda e uma direita. A diferença entre as velocidades delas determina como o robô se movimenta.

Quando as duas rodas giram na mesma velocidade, o robô anda em linha reta. Quando possuem velocidades diferentes, ele faz uma curva. Quando uma roda gira para frente e a outra para trás, o robô consegue girar em torno do próprio eixo.

As velocidades são usadas para calcular a velocidade linear (v) e a velocidade angular (omega) do robô.

3. Odometria Discreta

A odometria é usada para estimar a posição do robô conforme ele se movimenta.

A cada pequeno intervalo de tempo (dt), o programa atualiza x, y e theta usando as velocidades do robô.

Percebemos que essa estimativa não é perfeita. Pequenos erros podem se acumular durante o movimento e fazer com que o robô termine em uma posição diferente da esperada.

4. Navegação GO-TO-GOAL

No GO-TO-GOAL, escolhemos um ponto na tela usando o mouse e o robô tenta chegar até ele.

O programa calcula a distância e a direção até o objetivo e usa um controlador proporcional para decidir a velocidade e a rotação do robô.

Conforme o robô se aproxima do objetivo, ele diminui a velocidade. Quando chega a uma distância pequena do ponto, ele para automaticamente.

5. O que aprendemos

Na aula, conseguimos entender melhor como controlar um robô de duas rodas e como a movimentação das rodas influencia sua trajetória.

Também vimos que controlar o robô apenas pelo tempo, como no exercício do quadrado, pode gerar erros acumulados. Já o GO-TO-GOAL é mais inteligente porque usa a posição do objetivo para orientar o movimento.

Assim, a aula ajudou a entender na prática a relação entre posição, orientação, velocidade, odometria e controle de robôs móveis.