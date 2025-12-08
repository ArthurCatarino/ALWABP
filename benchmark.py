import os
import csv
import time
import statistics

# --- IMPORTAÇÕES ---
try:
    # Apenas importamos o ACO Puro e o Solver Gurobi
    from main import ACO as ACO_Puro, ler_e_converter_dados
    from solver_gurobi import resolver_gurobi
except ImportError as e:
    print(f"ERRO CRÍTICO: Faltam arquivos necessários (main.py ou solver_gurobi.py). {e}")
    exit()

# Parâmetros Globais
N_ITERACOES_MEDIA = 5
TEMPO_LIMITE_POR_EXECUCAO = 300  # 10 Minutos

def extrair_numero_instancia(nome_arquivo):
    try:
        return int(nome_arquivo.split('_')[0])
    except:
        return 0 

def calcular_estatisticas(resultados_runs, otimo_referencia):
    """
    Processa uma lista de dicionários com resultados de várias runs.
    Espera: [{'sf': float, 'si': float, 'time': float}, ...]
    Retorna médias formatadas.
    """
    validos = [r for r in resultados_runs if r['sf'] != float('inf')]
    
    if not validos:
        return "INF", "INF", "INF", "INF", "INF"

    # Extrai listas
    vals_si = [r['si'] for r in validos]
    vals_sf = [r['sf'] for r in validos]
    vals_time = [r['time'] for r in validos]
    
    # 1. SI (Solução Inicial) e SF (Solução Final) Médias
    avg_si = statistics.mean(vals_si)
    avg_sf = statistics.mean(vals_sf)
    avg_time = statistics.mean(vals_time)

    # 2. Desvio % (Melhoria da Inicial para Final): 100 * (SI - SF) / SI
    melhorias = []
    for r in validos:
        if r['si'] != float('inf') and r['si'] > 0:
            imp = 100 * (r['si'] - r['sf']) / r['si']
            melhorias.append(imp)
        else:
            melhorias.append(0.0)
    avg_imp = statistics.mean(melhorias)

    # 3. Desvio % do Ótimo (Gap): 100 * (SF - Opt) / Opt
    gaps = []
    if otimo_referencia and otimo_referencia != float('inf') and otimo_referencia > 0:
        for r in validos:
            gap = 100 * (r['sf'] - otimo_referencia) / otimo_referencia
            gaps.append(gap)
        avg_gap = statistics.mean(gaps)
    else:
        avg_gap = float('inf')

    # Formatação
    s_si = f"{avg_si:.1f}" if avg_si != float('inf') else "INF"
    s_sf = f"{avg_sf:.1f}"
    s_imp = f"{avg_imp:.2f}"
    s_gap = f"{avg_gap:.2f}" if avg_gap != float('inf') else "-"
    s_time = f"{avg_time:.2f}"

    return s_si, s_sf, s_imp, s_gap, s_time

def rodar_benchmark_comparativo(pasta_raiz='instancias', arquivo_saida='resultado_comparativo_puro.csv'):
    
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminho_raiz = os.path.join(diretorio_script, pasta_raiz)
    
    if not os.path.exists(caminho_raiz):
        print(f"Erro: Pasta '{caminho_raiz}' não encontrada.")
        return

    subpastas = [f for f in os.listdir(caminho_raiz) if os.path.isdir(os.path.join(caminho_raiz, f))]
    subpastas.sort()

    print(f"--- INICIANDO BENCHMARK (ACO PURO vs GUROBI) ---")
    print(f"--- Média de {N_ITERACOES_MEDIA} execuções por instância ---")
    
    with open(arquivo_saida, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # Cabeçalho Simplificado (Sem Híbrido)
        header = [
            'Classe', 'Instancia',
            'Gurobi_Opt', 'Gurobi_Time', # Referência
            
            # ACO Puro
            'Puro_SI_Avg', 'Puro_SF_Avg', 
            'Puro_Imp_SI_SF(%)', 'Puro_Gap_Opt(%)', 'Puro_Time'
        ]
        writer.writerow(header)

        for pasta in subpastas:
            if pasta == 'geral': continue

            caminho_completo_pasta = os.path.join(caminho_raiz, pasta)
            
            # Params
            if pasta == 'hes': p_alpha, p_beta = 0.0, 2.5
            elif pasta == 'ros': p_alpha, p_beta = 0.5, 3.0
            else: p_alpha, p_beta = 1.0, 3.0

            arquivos = [f for f in os.listdir(caminho_completo_pasta) 
                        if os.path.isfile(os.path.join(caminho_completo_pasta, f)) 
                        and not f.startswith('.')]
            arquivos.sort(key=extrair_numero_instancia)

            print(f"\n>>> CLASSE: {pasta.upper()}")

            for nome_instancia in arquivos:
                caminho_instancia = os.path.join(caminho_completo_pasta, nome_instancia)
                print(f" > {nome_instancia} | ", end="", flush=True)

                dados = ler_e_converter_dados(caminho_instancia)
                if not dados: continue
                t_tar_trab, grafo, precedencia, lb_calc, c_alvo, t_med_trab, fatiadas, grafoR, os_val = dados

                # 1. Gurobi (Referência Ótima)
                gur_ciclo, gur_tempo, _, _ = resolver_gurobi(caminho_instancia, time_limit=TEMPO_LIMITE_POR_EXECUCAO)
                print(f"Ref: {gur_ciclo:.1f} | ", end="", flush=True)

                # 2. ACO Puro
                runs_puro = []
                for _ in range(N_ITERACOES_MEDIA):
                    start = time.time()
                    try:
                        # Certifique-se que o main.py retorna (SF, SI) e aceita tempo_limite
                        val_sf, val_si = ACO_Puro(
                            t_tar_trab, grafo, precedencia, lb_calc, c_alvo, t_med_trab, 
                            fatiadas, grafoR, os_val,
                            alpha_trab=p_alpha, beta_trab=p_beta, alpha_tar=1.0, beta_tar=2.0,
                            numeroFormigas=100, nIteracoesSemMelhoria=150,
                            tempoLimite=TEMPO_LIMITE_POR_EXECUCAO # Verifique se no seu main.py é tempo_limite ou tempoLimite
                        )
                    except ValueError:
                        # Caso o main.py ainda retorne apenas um valor
                        val_sf = float('inf')
                        val_si = float('inf')
                    except TypeError:
                         # Caso o nome do argumento de tempo esteja diferente
                         print("[Aviso: Verifique o nome do parâmetro de tempo no main.py]")
                         val_sf, val_si = float('inf'), float('inf')

                    end = time.time()
                    runs_puro.append({'sf': val_sf, 'si': val_si, 'time': end - start})
                
                p_si, p_sf, p_imp, p_gap, p_time = calcular_estatisticas(runs_puro, gur_ciclo)
                print(f"Puro: {p_sf}")

                # Escreve Linha
                writer.writerow([
                    pasta, nome_instancia,
                    f"{gur_ciclo:.1f}" if gur_ciclo != float('inf') else "INF", 
                    f"{gur_tempo:.2f}",
                    
                    p_si, p_sf, p_imp, p_gap, p_time
                ])

    print(f"\n--- Benchmark Concluído. Dados em '{arquivo_saida}' ---")

if __name__ == "__main__":
    rodar_benchmark_comparativo()