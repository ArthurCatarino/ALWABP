# Otimização de Balanceamento de Linha (ALWABP) via Colônia de Formigas Híbrida

Este repositório contém a implementação de algoritmos para resolução do **Problema de Balanceamento de Linha de Montagem com Atribuição de Trabalhadores (ALWABP)**. O projeto compara uma abordagem exata utilizando o solver **Gurobi** contra uma meta-heurística híbrida baseada em **Otimização por Colônia de Formigas (ACO)**.

## 📄 Relatório Técnico e Resultados

A análise completa, incluindo a modelagem matemática, detalhes da implementação híbrida e a discussão aprofundada dos resultados, está disponível no documento abaixo:

👉 **[Clique aqui para acessar o Relatório Técnico Completo (PDF)](./Relatorio_Final_ALWABP.pdf)**

👉***[Planilha com resultados detalhados https://docs.google.com/spreadsheets/d/1pq_1FrpysOCSsRL1IiJ-cJYwZ7q3aYZ7Q9jPux9OSoQ/edit?usp=sharing ]***
---

## 🚀 Funcionalidades

O projeto é dividido em três módulos principais:

1.  **ACO Híbrido (`main.py`):** Algoritmo de Colônia de Formigas com feromônio em dois níveis, heurísticas baseadas em *Order Strength* e busca local (*Shift*).
2.  **Solver Exato (`solver_gurobi.py`):** Modelo matemático formal resolvido via Gurobi Optimizer.
3.  **Benchmark (`benchmark.py`):** Script de automação que executa testes em lote nas instâncias (*Hes, Ros, Ton, Wee*) e gera planilhas comparativas.

## 🛠️ Pré-requisitos

Para executar este projeto, você precisará de:

* **Python 3.8+**
* **Licença do Gurobi:** É necessário ter uma licença válida (WLS, Academic ou Commercial) configurada na sua máquina.

### Instalação das Dependências

Instale a biblioteca do Gurobi via pip:

```bash
pip install gurobipy