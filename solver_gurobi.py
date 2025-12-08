import gurobipy as gp
from gurobipy import Model, GRB

def ler_instancia_alwabp(caminho_arquivo):
    """
    Lê o arquivo de texto e estrutura os dados.
    Retorna: n (tarefas), k (trabalhadores), t (matriz tempos), G (matriz adjacência)
    """
    t = [] # Matriz de tempos (N x K)
    G = [] # Matriz de Adjacência (N x N)
    n = 0
    k = 0
    
    try:
        with open(caminho_arquivo, 'r') as f:
            # Lê número de tarefas
            linha = f.readline()
            if not linha: return 0, 0, [], []
            n = int(linha.strip())

            # Inicializa grafo vazio
            G = [[0 for _ in range(n)] for _ in range(n)]

            # Lê primeira linha de tempos para descobrir K (número de trabalhadores)
            linha = f.readline().strip()
            partes = linha.split()
            k = len(partes)
            
            BIG_M = 1000000 

            def processar_tempo(valor):
                if valor == "Inf": return BIG_M
                return int(valor)

            # Adiciona primeira linha de tempos
            t.append([processar_tempo(x) for x in partes])
            
            # Lê o restante das tarefas
            for _ in range(n - 1):
                linha = f.readline().strip()
                partes = linha.split()
                t.append([processar_tempo(x) for x in partes])

            # Leitura das Precedências
            while True:
                linha = f.readline()
                if not linha: break
                
                partes = list(map(int, linha.strip().split()))
                
                # Condição de parada (-1 -1)
                if len(partes) < 2 or partes[0] == -1:
                    break
                
                # Ajuste de índice (Arquivo começa em 1, Python em 0)
                tarefa_i = partes[0] - 1
                tarefa_j = partes[1] - 1
                
                G[tarefa_i][tarefa_j] = 1

        return n, k, t, G

    except Exception as e:
        print(f"Erro na leitura do arquivo {caminho_arquivo}: {e}")
        return 0, 0, [], []

def construir_e_resolver_modelo(n, k, t, G, time_limit):
    """
    Recebe os dados estruturados e roda o Gurobi.
    Retorna: (ObjVal, Runtime, Status, Gap)
    """
    e = k # Número de estações = Número de trabalhadores

    try:
        modelo = Model("ALWABP")
        
        # Configurações do Solver
        modelo.setParam('OutputFlag', 0)         # 0 = Silencioso, 1 = Verboso
        modelo.setParam('TimeLimit', time_limit) # Tempo máximo em segundos
        modelo.setParam('Threads', 4)

        # --- Variáveis ---
        # x[i,s,w] = 1 se Tarefa i na Estação s pelo Trab w
        x = modelo.addVars(n, e, k, vtype=GRB.BINARY, name="x")
        
        # y[s,w] = 1 se Trab w alocado na Estação s
        y = modelo.addVars(e, k, vtype=GRB.BINARY, name="y")
        
        # Tempo de Ciclo (Objetivo)
        E_max = modelo.addVar(lb=0, vtype=GRB.CONTINUOUS, name="E_max")

        modelo.setObjective(E_max, GRB.MINIMIZE)

        # --- Restrições ---

        # 1. Definição do Tempo de Ciclo (E_max >= Carga da Estação)
        for E_idx in range(e):
            carga_estacao = gp.quicksum(x[N, E_idx, K] * t[N][K] for N in range(n) for K in range(k))
            modelo.addConstr(carga_estacao <= E_max, name=f"Carga_Estacao_{E_idx}")

        # 2. Cada tarefa deve ser alocada uma única vez
        for N in range(n):
            soma_x = gp.quicksum(x[N, E_idx, K] for E_idx in range(e) for K in range(k))
            modelo.addConstr(soma_x == 1, name=f"Tarefa_Unica_{N}")

        # 3. Cada estação tem exatamente um trabalhador
        for E_idx in range(e):
            soma_trabalhadores = gp.quicksum(y[E_idx, K] for K in range(k))
            modelo.addConstr(soma_trabalhadores == 1, name=f"Um_Trab_Estacao_{E_idx}")

        # 4. Cada trabalhador em exatamente uma estação
        for K in range(k):
            soma_estacoes = gp.quicksum(y[E_idx, K] for E_idx in range(e))
            modelo.addConstr(soma_estacoes == 1, name=f"Trab_{K}_Uma_Estacao")

        # 5. Vínculo: Se tarefa N é feita na estação E pelo trab K, então Y[E,K] deve ser 1
        for N in range(n):
            for E_idx in range(e):
                for K in range(k):
                    modelo.addConstr(x[N, E_idx, K] <= y[E_idx, K], name=f"Link_X_Y_{N}_{E_idx}_{K}")

        # 6. Precedência
        # Se G[i][j]=1 (i precede j), então Estação(i) <= Estação(j)
        for i in range(n):
            for j in range(n):
                if G[i][j] == 1: 
                    posicao_i = gp.quicksum(E_idx * x[i, E_idx, K] for E_idx in range(e) for K in range(k))
                    posicao_j = gp.quicksum(E_idx * x[j, E_idx, K] for E_idx in range(e) for K in range(k))
                    modelo.addConstr(posicao_i <= posicao_j, name=f"Prec_{i}_{j}")

        modelo.optimize()

        if modelo.SolCount > 0:
            status_str = "OTIMO" if modelo.status == GRB.OPTIMAL else "LIMIT_TEMPO"
            gap_interno = modelo.MIPGap * 100 # Em porcentagem
            return modelo.ObjVal, modelo.Runtime, status_str, gap_interno
        else:
            return float('inf'), modelo.Runtime, "SemSolucao", 0.0

    except gp.GurobiError as e:
        print(f"Erro no Solver Gurobi: {e}")
        return float('inf'), 0, "ErroSolver", 0.0

def resolver_gurobi(caminho_arquivo, time_limit=3600):
    """
    Função Wrapper: Lê o arquivo e chama o modelo.
    """
    n, k, t, G = ler_instancia_alwabp(caminho_arquivo)
    
    if n == 0:
        return float('inf'), 0, "ErroLeitura", 0.0
    
    return construir_e_resolver_modelo(n, k, t, G, time_limit)

if __name__ == "__main__":
    arquivo_teste = "instancias/23_wee.txt" 
    print(f"Testando Gurobi com {arquivo_teste}...")
    res = resolver_gurobi(arquivo_teste, time_limit=10)
    print(f"Resultado: {res}")