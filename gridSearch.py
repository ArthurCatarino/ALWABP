import os
import time
import math
import copy

try:
    from main import ACO, ler_e_converter_dados
except ImportError:
    print("ERRO CRÍTICO: Arquivo 'main.py' não encontrado.")
    exit()

# --- CONFIGURAÇÕES DO TUNING ---

# Ponto de partida (Valores iniciais razoáveis)
CONFIG_INICIAL = {
    'alpha_trab': 1.0, 
    'beta_trab': 3.0, 
    'alpha_tar': 1.0, 
    'beta_tar': 2.0
}

# Parâmetros do algoritmo de busca (Hill Climbing)
PASSO_INICIAL = 0.5       # Começa testando variações grandes (ex: 1.0 -> 1.5)
PASSO_MINIMO = 0.2        # Se o passo for menor que isso, encerra (precisão suficiente)
LIMITES_PARAM = (0.0, 5.0) # Não testa valores negativos nem absurdamente altos

# Configuração "Turbo" para o teste ser rápido
# Usamos menos formigas/iterações apenas para descobrir a tendência
NUM_FORMIGAS_TESTE = 15
MAX_ITERACOES_TESTE = 80
QTD_RODADAS_POR_INSTANCIA = 1  # Roda 3x e tira a média para eliminar o fator sorte

def carregar_dataset_da_pasta(caminho_pasta):
    """
    Lê todas as instâncias e o gabarito de uma pasta e carrega na RAM.
    """
    dataset = []
    
    # 1. Carrega Gabarito (optimos.txt)
    arquivo_optimos = os.path.join(caminho_pasta, 'optimos.txt')
    lista_otimos = []
    
    if os.path.exists(arquivo_optimos):
        with open(arquivo_optimos, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lista_otimos.append(int(float(line)))
                    except ValueError:
                        pass

    # 2. Lista Arquivos de Instância
    arquivos = [
        f for f in os.listdir(caminho_pasta) 
        if os.path.isfile(os.path.join(caminho_pasta, f)) 
        and f != 'optimos.txt' 
        and not f.startswith('.')
    ]
    
    # Ordenação numérica (1_hes antes de 10_hes) para bater com o gabarito
    def extrair_num(n): 
        try: return int(n.split('_')[0])
        except: return 0
    arquivos.sort(key=extrair_num)

    # 3. Lê e armazena os dados
    for i, nome_arq in enumerate(arquivos):
        caminho_completo = os.path.join(caminho_pasta, nome_arq)
        
        dados_brutos = ler_e_converter_dados(caminho_completo)
        if dados_brutos is None: continue
        
        # Tenta casar com o ótimo
        otimo_real = lista_otimos[i] if i < len(lista_otimos) else None
        
        dataset.append({
            'nome': nome_arq,
            'otimo': otimo_real,
            'dados': dados_brutos # Tupla com os 8 valores do main
        })
    
    return dataset

def avaliar_configuracao(dataset, config):
    """
    Roda o ACO para todo o dataset usando a 'config' passada.
    Roda N vezes por instância e retorna o GAP MÉDIO GLOBAL.
    """
    soma_gaps_global = 0
    total_validos = 0
    
    # Se dataset vazio, retorna gap infinito
    if not dataset: return 100.0

    for item in dataset:
        # Desempacota os dados lidos
        # Certifique-se que a ordem bate com o return do seu ler_e_converter_dados
        t_tar, grafo, prec, lb, c_alvo, t_med, fatiadas, grafoR,os = item['dados']
        otimo = item['otimo']
        
        soma_gap_instancia = 0
        rodadas_validas_instancia = 0
        
        # --- LOOP DE REPETIÇÃO (Para reduzir ruído aleatório) ---
        for _ in range(QTD_RODADAS_POR_INSTANCIA):
            
            # Chama o ACO com os parâmetros sendo testados
            ciclo = ACO(
                t_tar, grafo, prec, lb, c_alvo, t_med, fatiadas, grafoR,os,
                alpha_trab=config['alpha_trab'], beta_trab=config['beta_trab'],
                alpha_tar=config['alpha_tar'], beta_tar=config['beta_tar'],
                numeroFormigas=NUM_FORMIGAS_TESTE,
                nIteracoesSemMelhoria=MAX_ITERACOES_TESTE
            )
            
            # Calcula Gap desta rodada
            gap_rodada = 100.0 # Penalidade se der Inf ou erro
            
            if otimo and ciclo != float('inf'):
                gap_rodada = ((ciclo - otimo) / otimo) * 100
                if gap_rodada < 0: gap_rodada = 0 # Caso o ACO supere o ótimo anotado
                rodadas_validas_instancia += 1
            elif ciclo != float('inf'):
                # Se não tem ótimo mas achou solução, assume gap 0 (neutro) ou ignora
                # Para tuning, penalizamos levemente para forçar a buscar otimos conhecidos
                gap_rodada = 50.0 
                rodadas_validas_instancia += 1
            
            soma_gap_instancia += gap_rodada

        # Média da Instância
        if rodadas_validas_instancia > 0:
            media_gap_instancia = soma_gap_instancia / QTD_RODADAS_POR_INSTANCIA
        else:
            media_gap_instancia = 100.0 # Falhou em todas as tentativas
        
        soma_gaps_global += media_gap_instancia
        total_validos += 1
            
    # Retorna a média de todas as instâncias da pasta
    return soma_gaps_global / max(1, total_validos)

def otimizar_pasta(nome_pasta, caminho_pasta):
    print(f"\n{'='*60}")
    print(f"OTIMIZANDO PASTA: {nome_pasta.upper()}")
    print(f"{'='*60}")
    
    dataset = carregar_dataset_da_pasta(caminho_pasta)
    if not dataset: 
        print("  Pasta vazia ou sem arquivos válidos.")
        return

    print(f"  Dataset: {len(dataset)} instâncias carregadas.")
    print(f"  Config: {NUM_FORMIGAS_TESTE} formigas, {MAX_ITERACOES_TESTE} iterações, {QTD_RODADAS_POR_INSTANCIA} repetições.")

    # Estado Inicial
    config_atual = CONFIG_INICIAL.copy()
    melhor_gap = avaliar_configuracao(dataset, config_atual)
    print(f"  [Base] Start: {config_atual} -> Gap Médio: {melhor_gap:.2f}%")
    
    passo = PASSO_INICIAL
    
    # Loop do Hill Climbing
    while passo >= PASSO_MINIMO:
        melhorou_neste_passo = False
        print(f"\n  --> Explorando vizinhança com passo +/- {passo}...")
        
        # Lista de parâmetros para tentar mexer
        parametros = list(config_atual.keys())
        
        for param in parametros:
            valor_original = config_atual[param]
            
            # --- TENTATIVA 1: AUMENTAR VALOR ---
            teste_up = config_atual.copy()
            teste_up[param] = round(valor_original + passo, 2)
            
            if teste_up[param] <= LIMITES_PARAM[1]:
                gap_up = avaliar_configuracao(dataset, teste_up)
                
                # Se melhorou, atualiza imediatamente (First Improvement)
                if gap_up < melhor_gap:
                    print(f"    [UP] Melhoria! {param}: {valor_original} -> {teste_up[param]} (Gap: {gap_up:.2f}%)")
                    melhor_gap = gap_up
                    config_atual = teste_up
                    melhorou_neste_passo = True
                    continue # Pula para o próximo parâmetro ou reinicia loop

            # --- TENTATIVA 2: DIMINUIR VALOR (Só se não subiu) ---
            teste_down = config_atual.copy()
            teste_down[param] = round(valor_original - passo, 2)
            
            if teste_down[param] >= LIMITES_PARAM[0]:
                gap_down = avaliar_configuracao(dataset, teste_down)
                
                if gap_down < melhor_gap:
                    print(f"    [DOWN] Melhoria! {param}: {valor_original} -> {teste_down[param]} (Gap: {gap_down:.2f}%)")
                    melhor_gap = gap_down
                    config_atual = teste_down
                    melhorou_neste_passo = True

        # Decisão do Passo
        if not melhorou_neste_passo:
            print(f"  [Travou] Nenhuma melhoria com passo {passo}. Refinando busca...")
            passo = passo / 2.0 # Diminui o passo (Zoom In)
        else:
            print(f"  [Sucesso] Melhora encontrada. Mantendo passo {passo} para nova rodada.")
            
    print(f"\n*** CAMPEÃO FINAL PARA {nome_pasta.upper()} ***")
    print(f"Params: {config_atual}")
    print(f"Gap Estimado: {melhor_gap:.2f}%")
    print("-" * 60)
    return config_atual

def rodar_tuning_inteligente(pasta_raiz='instancias'):
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminho_raiz = os.path.join(diretorio_script, pasta_raiz)
    
    if not os.path.exists(caminho_raiz):
        print(f"Pasta '{caminho_raiz}' não encontrada.")
        return

    subpastas = [f for f in os.listdir(caminho_raiz) if os.path.isdir(os.path.join(caminho_raiz, f))]
    subpastas.sort()
    
    # Filtra pasta geral se quiser
    if 'geral' in subpastas: subpastas.remove('geral')
    
    resultados = {}
    
    for pasta in subpastas:
        res = otimizar_pasta(pasta, os.path.join(caminho_raiz, pasta))
        if res:
            resultados[pasta] = res

    # Exibe Resumo Final
    print("\n\n=== RESUMO DOS MELHORES PARÂMETROS ===")
    for pasta, cfg in resultados.items():
        print(f"Pasta '{pasta}': A_Tr={cfg['alpha_trab']}, B_Tr={cfg['beta_trab']} | A_Tar={cfg['alpha_tar']}, B_Tar={cfg['beta_tar']}")

if __name__ == "__main__":
    rodar_tuning_inteligente('instancias')