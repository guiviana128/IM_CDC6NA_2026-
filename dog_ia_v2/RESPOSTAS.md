# DOG-IA – Respostas das Questões Técnicas (AC-4)

Todos os números abaixo saíram da execução do nosso `dog_ia_v2.py`.

---

## 1. Arquitetura Híbrida de Navegação

**Qual limitação crítica da navegação puramente reativa é resolvida pela arquitetura híbrida, e por que o planejador global sozinho também não basta em um ambiente urbano?**

Na versão 1, o robô decide para onde ir olhando só o que o LiDAR está vendo naquele momento e a direção do alvo. Funciona bem quando o caminho é simples, mas ele não tem noção do mapa como um todo. O maior problema disso são os mínimos locais. Se ele encontra um obstáculo em formato de "U", ou fica entre a banca e o poste, ele vira para um lado, depois para o outro, e acaba preso ou andando em círculos, porque qualquer movimento em direção ao alvo o leva de volta para o obstáculo. Além disso, ele não sabe onde fica a faixa de pedestres (tanto que na V1 ele atravessa a avenida em linha reta), não consegue comparar rotas e não tem como dar preferência ao piso tátil.

Com o A\* esse problema é resolvido, porque o robô passa a ter uma visão do mapa inteiro antes de sair. Ele já calcula um caminho completo até o destino, contornando os obstáculos, passando pela faixa e preferindo o piso tátil, que tem custo menor na grade.

Mas só o A\* também não é suficiente na rua. O plano é feito em cima de um mapa fixo, e a cidade não é fixa: carros passam o tempo todo, alguns furam o sinal, aparecem pessoas e objetos que não estavam no mapa. Recalcular o A\* a cada quadro seria pesado demais e lento para reagir a um carro vindo em alta velocidade. Também existe o ruído do sensor e o fato de o robô nunca seguir a rota com perfeição.

Por isso a melhor solução é juntar os dois. O A\* define o caminho geral, e a parte reativa (LiDAR, previsão de colisão e freio de emergência) cuida do que acontece no momento. Quando o robô fica preso desviando de alguma coisa por mais de 3,5 segundos, o sistema pede uma nova rota ao A\*. Uma camada complementa a outra.

---

## 2. Máquina de Estados

### 2.1 Estados por que o robô passou na viagem até o Mercado

Rodamos a viagem com `python dog_ia_v2.py --trace Mercado --seed 1`, que faz uma viagem sem abrir janela e imprime cada mudança de estado. O resultado foi este (tempo contado a partir do momento em que apertamos o 1):

| Tempo | Estado | Próximo estado | O que causou a mudança |
|---|---|---|---|
| 0,00 s | AGUARDANDO_DESTINO | PLANEJANDO | Apertamos a tecla 1 e escolhemos o Mercado. |
| 0,00 s | PLANEJANDO | NAVEGANDO | O A\* encontrou a rota (114 pontos). Como o Mercado fica do outro lado da avenida, a rota passa pela faixa. |
| 3,85 s | NAVEGANDO | AGUARDANDO_SINAL | O robô chegou à linha de espera, 24 px antes do meio-fio. |
| 9,78 s | AGUARDANDO_SINAL | ATRAVESSANDO | O sinal de pedestre abriu com 5,3 s restantes, mais que o limite de 2,44 s, e não havia carro previsto na faixa. |
| 11,28 s | ATRAVESSANDO | NAVEGANDO | O robô chegou à outra calçada com o tutor já fora da rua. |
| 15,57 s | NAVEGANDO | DESTINO_ALCANCADO | Chegou ao Mercado. |

A viagem toda levou 15,6 s e o robô andou 10,4 m. Quase 6 segundos foram só esperando o semáforo, o que mostra o quanto o sinal pesa no tempo total.

Nessa execução não apareceu obstáculo novo nem carro infrator, então três estados não apareceram:
- **DESVIO_LOCAL**: quando o LiDAR vê algo que não estava no mapa;
- **REPLANEJANDO**: quando o desvio passa de 3,5 s;
- **FREIO_EMERGENCIA**: quando um carro infrator entra na rota.

Dá para provocar os dois primeiros clicando com o botão direito no caminho do robô para criar um obstáculo. O freio apareceu nos testes com mais infratores (questão 5).

### 2.2 Qual a diferença entre AGUARDANDO_SINAL e FREIO_EMERGENCIA?

Os dois deixam o robô parado, mas por motivos bem diferentes.

O **AGUARDANDO_SINAL** é uma parada que já estava prevista. O robô está na calçada, em um lugar seguro, esperando o semáforo abrir para pedestres, como qualquer pessoa faria. Também fica nesse estado se o sinal abriu mas já não sobra tempo suficiente para atravessar, ou se tem algum carro chegando na faixa. Não existe perigo nesse momento; é só o robô respeitando a regra de trânsito.

O **FREIO_EMERGENCIA** é uma reação a uma situação de risco. Ele é acionado quando o robô projeta para onde os carros vão estar no próximo segundo e percebe que um deles vai atingir ele ou o tutor. Isso pode acontecer no meio da travessia, mesmo com o sinal aberto, normalmente por causa de um motorista que furou o vermelho. Esse evento é registrado nas métricas e dispara o alerta sonoro. Quando o perigo passa, o robô volta ao que estava fazendo.

Ou seja, no primeiro caso o robô está seguindo a regra; no segundo, está se protegendo de alguém que não seguiu.

---

## 3. Percepção e Ruído do Sensor

### 3.1 Por que a mediana é melhor que a média para falhas do tipo "leitura = alcance máximo"?

Quando o sensor falha, ele devolve o alcance máximo (165 px), como se não tivesse nada na frente, mesmo que exista um obstáculo bem perto. Esse valor é muito diferente das leituras normais, e a média é muito afetada por esse tipo de valor fora do padrão.

Um exemplo: o obstáculo está a 40 px e uma das três leituras falhou. Ficamos com 40, 40 e 165.

- A média dá cerca de 81,7 px. O robô acharia que o obstáculo está duas vezes mais longe do que realmente está, e poderia demorar para desviar.
- A mediana dá 40 px, que é o valor correto. A leitura com falha simplesmente é ignorada.

Como a taxa de falha é de 2%, é muito raro acontecerem duas falhas seguidas no mesmo raio dentro de uma janela de 3 leituras. Então a mediana elimina praticamente todas as leituras falsas sem mexer nas leituras boas.

### 3.2 Qual o custo do filtro em atraso de detecção?

Com 60 varreduras por segundo, cada varredura leva cerca de 16,7 ms.

Quando um obstáculo aparece, a mediana só passa a mostrar ele quando 2 das 3 leituras já o detectaram. Na primeira varredura com o obstáculo, a janela ainda tem duas leituras "livres", então a mediana continua livre. Na segunda, o obstáculo já é maioria e é detectado.

Isso gera um atraso extra de uma varredura, ou seja, uns **0,017 s**. Contando a própria varredura em que o objeto surge, a detecção acontece em até uns **0,033 s**. Nesse tempo o robô, a 156 px/s, anda menos de 5 px, então o custo é bem pequeno comparado ao ganho de não reagir a leituras falsas.

### 3.3 E se o filtro usasse 15 varreduras em vez de 3?

O filtro ficaria mais resistente a falhas, porque seriam necessárias 8 falhas seguidas para enganar a mediana. Em compensação, o atraso subiria para umas 7 varreduras, cerca de **0,12 s**. Parece pouco, mas nesse tempo o robô anda uns 18 px sem "enxergar" o obstáculo novo, e um carro a 200 px/s anda mais de 20 px.

Um problema ainda pior é que objetos rápidos ou que aparecem por pouco tempo, como um carro passando pela frente do feixe, precisariam ser vistos em pelo menos 8 das 15 leituras. Muitas vezes isso não aconteceria e o objeto simplesmente não seria detectado.

Para um robô que anda no meio do trânsito, perder tempo de reação é perigoso. Por isso a janela de 3 é um bom meio-termo: tira as leituras falsas com um atraso mínimo.

---

## 4. Segurança Temporal na Travessia

### 4.1 Cálculo do limite

A fórmula é: tempo_restante > (RUA_ALTURA + 24 + GUIA) / velocidade × 1,35 + 0,4

Substituindo os valores:

- Distância total: 170 + 24 + 42 = 236 px
- Tempo para percorrer: 236 / 156 ≈ 1,51 s
- Com a margem de segurança: 1,51 × 1,35 ≈ 2,04 s
- Somando o tempo de reação: 2,04 + 0,4 ≈ **2,44 s**

Ou seja, o robô só começa a atravessar se ainda restarem mais de 2,44 segundos de sinal aberto para o pedestre.

Uma coisa interessante da fórmula é que ela soma o comprimento da guia (42 px). Não basta o robô chegar do outro lado: a travessia só termina quando o tutor também sai da rua. O fator de 1,35 dá uma folga de 35% para o caso de o robô precisar diminuir a velocidade (por exemplo, quando a guia fica tensionada porque a pessoa está andando mais devagar), e os 0,4 s cobrem o tempo de arrancada.

### 4.2 Por que existem as fases de "todos vermelhos" de 1,5 s? Que risco elas eliminam?

Essas fases servem como um tempo de segurança entre um fluxo e outro, em que ninguém tem sinal verde.

O primeiro "todos vermelhos" vem logo depois do amarelo. Ele existe porque nem todo carro consegue parar quando o amarelo acende: quem já estava muito perto da faixa acaba passando. Sem esse intervalo, o sinal do pedestre poderia abrir com esse carro ainda cruzando a faixa. Ele também cobre o motorista que "estica" o amarelo e o tempo de reação de quem está dirigindo.

O segundo vem depois da fase do pedestre. Ele dá tempo para quem começou a atravessar no finalzinho, como um tutor que anda mais devagar, terminar de sair da rua antes de os carros receberem o verde.

O risco que essas fases eliminam é o de acidente na troca de sinal: o último carro de um ciclo atropelar o primeiro pedestre do outro, ou o contrário.

---

## 5. Avaliação Experimental

Comandos utilizados:

```bash
python dog_ia_v2.py --benchmark 20 --seed 1
python dog_ia_v2.py --benchmark 20 --seed 7
```

### 5.1 Resultados

| Métrica | Seed 1 | Seed 7 |
|---|---|---|
| Taxa de sucesso | 100% (20 de 20) | 100% (20 de 20) |
| Tempo médio por viagem | 12,6 s (desvio padrão 5,6 s) | 10,4 s (desvio padrão 5,5 s) |
| Colisões | 0 | 0 |
| Quase-colisões | 0 | 0 |
| Freios de emergência | 0 | 0 |
| Alertas vermelhos | 50 | 31 |
| Replanejamentos | 4 | 0 |
| Distância total | 158,3 m | 135,1 m |

Como explicação: no benchmark, cada viagem sorteia um destino diferente do lugar onde o robô está e, em metade das viagens, coloca uma caixa "surpresa" sobre a rota, que o robô não conhece. Os arquivos `benchmark_seed1.csv` e `benchmark_seed7.csv` têm o resultado de cada viagem.

Como os infratores são só 10% dos carros, com 20 viagens nenhum deles cruzou o caminho do robô durante uma travessia. Para ter certeza de que o freio funciona, fizemos um teste extra com 60% de carros infratores (seed 3). O resultado foi 100% de sucesso, 3 freios de emergência, 3 quase-colisões e nenhuma colisão.

### 5.2 Por que a seed fixa torna o experimento reproduzível, e por que os resultados das duas seeds são diferentes?

O computador não gera números realmente aleatórios. Ele usa uma fórmula que, a partir de um número inicial (a seed), produz sempre a mesma sequência de valores. Se a seed é a mesma, tudo que depende de sorte na simulação se repete exatamente igual: o ruído do LiDAR, as falhas de 2%, o momento em que cada carro aparece, a velocidade de cada um, quais carros furam o sinal e quais destinos são escolhidos.

Além disso, o modo benchmark usa um passo de tempo fixo, sem depender do FPS. Então o resultado não muda se o computador for mais rápido ou mais lento. Qualquer pessoa que rodar com a seed 1 vai obter os mesmos números, o que permite conferir os resultados e comparar versões diferentes do código de forma justa.

Rodamos a seed 1 duas vezes e os números saíram exatamente iguais.

Quando trocamos para a seed 7, a sequência de números muda e, com ela, o cenário inteiro. Os carros chegam em outros momentos, os infratores aparecem em outras viagens e o robô chega ao semáforo em outra fase, esperando mais ou menos tempo. Foi isso que vimos: as duas seeds tiveram 100% de sucesso, mas o tempo médio foi de 12,6 s em uma e 10,4 s na outra. Na seed 1 o sorteio caiu mais vezes em viagens que atravessam a avenida, que são as mais demoradas por causa do semáforo. Ela também teve 4 replanejamentos por causa das caixas surpresa, contra nenhum na seed 7. Cada seed funciona como uma amostra diferente. Como são só 20 viagens, é normal os resultados variarem bastante de uma seed para outra. O ideal, para tirar conclusões mais confiáveis, seria rodar várias seeds e calcular a média e o desvio padrão.

### 5.3 Proposta de melhoria

Nossa proposta é aumentar o tempo de previsão da zona varrida de 1,0 s para 1,5 s e só deixar o robô começar a travessia se a faixa estiver livre pelos próximos 2 segundos.

Nos nossos testes normais já não houve colisões, mas no teste com muitos infratores apareceram 3 quase-colisões. É aí que a melhoria faria diferença. Com ela, esperamos que caiam as **quase-colisões** e as **colisões**. O robô passaria a perceber um carro infrator mais cedo, enquanto ele ainda está longe, e pararia antes de entrar na frente dele, em vez de frear já dentro da faixa.

Por outro lado, o **tempo médio de viagem** provavelmente aumentaria. Com uma previsão mais longa, carros que iriam frear normalmente também acionariam o alerta. Isso geraria mais freios de emergência "desnecessários" e mais situações em que o robô perde o sinal e precisa esperar o próximo ciclo.

Outra ideia seria aumentar o custo, no A\*, das células da calçada que ficam perto do meio-fio. Assim o robô andaria mais afastado da rua, o que reduziria o risco perto dos carros, mas a distância percorrida ficaria um pouco maior.
