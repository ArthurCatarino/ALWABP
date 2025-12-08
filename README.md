# Relatório Técnico: Otimização de Balanceamento de Linha (ALWABP) via Colônia de Formigas Híbrida

**Autores:** Guilherme Freire, Mateus Poddis, Arthur Catarino  
**Data:** Dezembro, 2025

---

## Resumo
Este relatório documenta a implementação de uma meta-heurística baseada em Otimização por Colônia de Formigas (ACO) para a resolução do Problema de Balanceamento de Linha de Montagem com Atribuição de Trabalhadores (ALWABP). O trabalho foca na minimização do tempo de ciclo ($E_{max}$) em um cenário onde a eficiência dos trabalhadores é heterogênea. A solução proposta introduz uma estratégia de feromônio em dois níveis, heurísticas baseadas em *Order Strength*, pré-processamento topológico e uma busca local dedicada à redução de gargalos, além de tratar restrições de inviabilidade através de penalização dinâmica.

---

## 1. Introdução
O alocamento eficiente de recursos é um desafio central na Pesquisa Operacional. O problema abordado, ALWABP (*Assembly Line Worker Assignment and Balancing Problem*), estende o problema clássico de balanceamento de linhas ao considerar que o tempo de execução de uma tarefa varia conforme o trabalhador designado para a estação.

O objetivo é minimizar o *makespan* ou tempo de ciclo, definido pela estação com a maior carga de trabalho. Devido à natureza NP-difícil do problema, métodos exatos tornam-se inviáveis para grandes instâncias, motivando o uso de meta-heurísticas. Este projeto implementa um algoritmo ACO híbrido, robusto a dados de entrada que representam falhas ou indisponibilidade (divisão por zero), utilizando técnicas de penalização "Grande-M".

## 2. Formulação Matemática
A modelagem matemática segue a estrutura formalizada para o problema. Seja $N$ o conjunto de tarefas e $K$ o conjunto de trabalhadores/estações. Definimos as variáveis de decisão:

* $X_{nek} \in \{0,1\}$: Variável binária que indica se a tarefa $n$ é realizada na estação $e$ pelo trabalhador $k$.
* $Y_{ek} \in \{0,1\}$: Variável binária que indica se o trabalhador $k$ está alocado à estação $e$.
* $E_{max}$: O tempo de ciclo (estação com a carga mais pesada).

A Função Objetivo é minimizar o tempo de ciclo:

$$\text{Min } E_{max}$$

Sujeito às seguintes restrições principais:

1.  **Definição do Tempo de Ciclo:** A carga de qualquer estação não pode exceder $E_{max}$:
    $$\forall e \in K, \quad \sum_{n \in N}\sum_{k \in K} X_{nek} \cdot T_{nk} \le E_{max}$$

2.  **Unicidade da Tarefa:** Cada tarefa deve ser executada exatamente uma vez:
    $$\forall n \in N, \quad \sum_{e \in K}\sum_{k \in K} X_{nek} = 1$$

3.  **Alocação Única:** Cada estação possui apenas um trabalhador e cada trabalhador assume apenas uma estação:
    $$\forall e \in K, \sum_{k \in K} Y_{ek} = 1 \quad \text{e} \quad \forall k \in K, \sum_{e \in K} Y_{ek} = 1$$

4.  **Vínculo Lógico:** Uma tarefa só ocorre se o trabalhador estiver na estação:
    $$X_{nek} \le Y_{ek}$$

5.  **Precedência:** Respeito ao grafo $G_{ij}=1$, onde a tarefa $i$ deve ocorrer em uma estação anterior ou igual à tarefa $j$.

## 3. Algoritmo Proposto e Implementação
A solução foi implementada em Python utilizando uma variação do *Max-Min Ant System*. O algoritmo se destaca por utilizar uma estrutura de decisão hierárquica, pré-processamento topológico e tratamento numérico de exceções.

### 3.1. Pré-processamento e Análise da Instância
A eficiência do algoritmo depende fundamentalmente da preparação dos dados:
* **Grafos:** Constrói-se a matriz de tempos $T_{nk}$ e o grafo de precedências $G$. Gera-se também o grafo inverso $G^{-1}$.
* **Topologia:** As tarefas são ordenadas topologicamente e segmentadas em regiões correspondentes ao número de estações ($|K|$).
* **Métricas:** Calculam-se o *Lower Bound* (LB), a Carga Alvo ($C_{alvo}$) e o *Order Strength* (OS).

### 3.2. Estrutura de Feromônios em Dois Níveis
O algoritmo utiliza duas matrizes distintas:
* `feromoniosTE`: Guia a alocação de Trabalhadores às Estações.
* `feromoniosTarefas`: Guia a sequência de tarefas dentro de cada estação.

### 3.3. Construção da Solução

**Fase 1: Alocação de Trabalhadores**
A regra de transição utiliza:
$$P_{ek} = \frac{[\tau_{ek}]^\alpha \cdot [\eta_{ek}]^\beta}{\sum_{l \in \mathcal{U}} [\tau_{el}]^\alpha \cdot [\eta_{el}]^\beta}$$

A heurística $\eta_{ek}$ é ponderada pelo *Order Strength* (OS):
$$\eta_{ek} = OS \cdot \left( \frac{1}{\bar{T}_{local}} \right) + (1 - OS) \cdot \left( \frac{1}{\bar{T}_{global}} \right)$$

**Fase 2: Alocação de Tarefas**
Heurística gulosa ($1/T_{n,k}$) com probabilidade:
$$P_{ij} = \frac{[\tau_{ij}]^\alpha \cdot [\eta_{ij}]^\beta}{\sum_{u \in \Omega} [\tau_{iu}]^\alpha \cdot [\eta_{iu}]^\beta}$$

### 3.4. Tratamento de Inviabilidade (Penalização)
Tarefas alocadas a trabalhadores incapazes ($T_{nk} = \infty$) são penalizadas via "Grande-M":

$$
Tempo_{calc} = 
\begin{cases} 
  \frac{T_i}{D_i} & \text{se } D_i > 0 \\
  999999 & \text{se } D_i \le 0 
\end{cases}
$$

### 3.5. Busca Local (Shift)
Após a construção, aplica-se um refinamento determinístico que move tarefas da estação gargalo para outras estações, validando aptidão e precedência ($G$ e $G^{-1}$).

### 3.6. Atualização de Feromônios
Evaporação ($\rho = 0.1$) e reforço elitista:
$$\tau_{ij} \leftarrow (1 - \rho) \cdot \tau_{ij}$$
$$\Delta \tau = \frac{100}{C_{max}}$$

## 4. Resultados e Discussões

Esta seção apresenta a análise comparativa entre o método exato (Solver Gurobi) e a meta-heurística proposta (ACO Proposto).

### 4.1. Análise de Desempenho Geral

**Tabela 1: Comparativo de Desempenho (ACO Proposto vs. Solver Gurobi)**

| Classe | Sol. Inicial | Sol. Final | Melhoria (%) | Gap Ótimo (%) | Tempo ACO (s) | Tempo Solver (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ros** | 22.37 | 21.05 | 5.89% | 26.30% | 1.77 | 0.51 |
| **Hes** | 117.13 | 101.93 | 12.98% | 33.10% | 2.23 | 0.84 |
| **Ton** | 170.53 | 153.30 | 10.11% | 109.28% | 9.38 | 306.03 |
| **Wee** | 48.05 | 40.95 | 14.78% | 107.34% | 15.84 | 288.20 |

### 4.2. Eficiência Computacional
* **Instâncias Leves (Ros, Hes):** O Solver Gurobi prova a otimalidade em < 1s.
* **Instâncias Complexas (Ton, Wee):** O Gurobi atinge o limite de 300s. O **ACO Proposto** encontra soluções em 9-16s (redução de ~95% no tempo), sendo uma alternativa viável para resposta rápida.

### 4.3. Evolução da Solução
A busca local e o feromônio garantem uma **melhoria média consistente (5% a 14%)** da solução inicial para a final, comprovando que o algoritmo não estagna prematuramente.

## 5. Conclusão
A abordagem de Colônia de Formigas Híbrida mostrou-se robusta. A penalização assegurou estabilidade matemática e a busca local garantiu refinamento constante. Embora não supere o método exato em instâncias pequenas, o algoritmo oferece um ganho de tempo crítico em instâncias complexas.

## Referências
1. Goldbarg, M. C.; Luna, H. P. L. *Otimização Combinatória e Programação Linear*. Elsevier, 2005.
2. Dorigo, M.; Stützle, T. *Ant Colony Optimization*. MIT Press, 2004.
3. Freire, G.; Poddis, M.; Catarino, A. *Modelagem ALWABP*. Lavras, 2025.