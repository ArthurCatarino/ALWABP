import gurobipy as gp
from gurobipy import Model, GRB

import sys

# ----------------------------
# 1) Leitura do arquivo de instâncias:
# ----------------------------

def ler_instancia_alwabp(caminho_arquivo):
    """
    Lê uma instância ALWABP do formato especificado.
    Retorna: N, K, tnk (matriz de tempos), G (matriz de precedência)
    """
    tnk = [] # Matriz de tempos (N x K)
    G = []   # Matriz de Adjacência do Grafo (N x N)
    
    with open(caminho_arquivo, 'r') as f:
        
        linha = f.readline()

        n = int(linha.strip())

        # Matriz de precedência 
        G = [[0 for _ in range(n)] for _ in range(n)]

        #  Leitura dos Tempos        
        linha = f.readline().strip()
        partes = linha.split()
        
        # Número de trabalhadores:
        k = len(partes)
        
        BIG_M = 1000000 

        def processar_tempo(valor):
            if valor == "Inf":           
                return BIG_M
            return int(valor)


        tnk.append([processar_tempo(x) for x in partes])
        
        for _ in range(n - 1):
            linha = f.readline().strip()
            partes = linha.split()
          
            if len(partes) != k:
                raise ValueError(f"Erro: Linha de tempo com número incorreto de colunas.")
            tnk.append([processar_tempo(x) for x in partes])

        # Leitura das Precedências (Grafo G)
        
        while True:
            linha = f.readline()
            if not linha:
                break
                
            partes = list(map(int, linha.strip().split()))
            
            # Condição de parada (-1 -1)
            if partes[0] == -1:
                break
            
            # Tarefa i deve ocorrer antes da tarefa j
            tarefa_i = partes[0] - 1
            tarefa_j = partes[1] - 1
            
            G[tarefa_i][tarefa_j] = 1

    return n, k, tnk, G


nome_arquivo = r"C:\\Users\\Mateus\\Documents\\ProgramaçãoMatemática\\Trabalho\\alwabp\\1_ton"

n, k, tnk, G = ler_instancia_alwabp(nome_arquivo)
e = k


# ----------------------------
# 2) Modelo Matemático:
# ----------------------------

modelo = Model("ALWABP")

x = modelo.addVars(n,e,k, vtype = GRB.BINARY, name = "x")
y = modelo.addVars(e,k, vtype = GRB.BINARY, name = "y")
E_max = modelo.addVar(lb=0, vtype=GRB.CONTINUOUS, name="E_max")

modelo  .setObjective(E_max, GRB.MINIMIZE)

# Estação com mais carga:
for E in range(e):
    carga_estacao = gp.quicksum(x[N, E, K] * tnk[N][K] for N in range(n) for K in range(k))
    modelo.addConstr(carga_estacao <= E_max, name=f"Definicao_Emax_Estacao_{E}")

# Apenas uma estação e um trabalhador executa a tarefa:
for N in range(n):
    soma_x = gp.quicksum(x[N, E, K] for E in range(e) for K in range(k))
    modelo.addConstr(soma_x == 1, name=f"Tarefa_Unica_{N}")

# Apenas um trabalhador por estação:
for E in range(e):
    soma_trabalhadores = gp.quicksum(y[E, K] for K in range(k))
    modelo.addConstr(soma_trabalhadores == 1, name=f"Um_Trabalhador_na_Estacao_{E}")

# O trabalhador fica em apenas uma estação:
for K in range(k):
    soma_estacoes = gp.quicksum(y[E, K] for E in range(e))
    modelo.addConstr(soma_estacoes == 1, name=f"Trabalhador_{K}_uma_estacao")

# A tarefa é executada ao trabalhador k na estaçãao e 
# apenas se o trabalhador estiver designado a estação:
for N in range(n):
    for E in range(e):
        for K in range(k):
            modelo.addConstr(x[N, E, K] <= y[E, K], name=f"Vinculo_X_Y_{n}_{e}_{k}")


#Verificação de precedencia das tarefas:
for i in range(n):
    for j in range(n):
        if G[i][j] == 1: 
            
            posicao_i = gp.quicksum(E * x[i, E, K] for E in range(e) for K in range(k))
            posicao_j = gp.quicksum(E * x[j, E, K] for E in range(e) for K in range(k))
        
            modelo.addConstr(posicao_i <= posicao_j, name=f"Precedencia_{i}_{j}")

# Otimiza o modelo
modelo.optimize()

# Verifica e imprime a solução
if modelo.status == GRB.OPTIMAL:
    print(f"\nTempo de Ciclo Mínimo (E_max): {E_max.X}")
    
    print("\n--- Alocações ---")
    for E in range(e):
        # Descobre qual trabalhador está na estação e
        trabalhador_alocado = -1
        for K in range(k):
            if y[E, K].X > 0.5: # Se for 1
                trabalhador_alocado = K
                break
        
        print(f"Estação {E+1} (Trabalhador {trabalhador_alocado+1}):")
        
        # Descobre quais tarefas estão lá
        tarefas = []
        tempo_total = 0
        for N in range(n):
            if x[N, E, trabalhador_alocado].X > 0.5:
                tarefas.append(N+1) # +1 para printar como no arquivo original
                tempo_total += tnk[N][trabalhador_alocado]
        
        print(f"  Tarefas: {tarefas}")
        print(f"  Carga Total: {tempo_total}")