import os
import csv
import time
import math

# Importações para o Google Sheets
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
except ImportError:
    print("AVISO: Bibliotecas do Google Sheets não instaladas. O upload não funcionará.")

try:
    from main import ACO, ler_e_converter_dados
    from solver_gurobi import resolver_gurobi
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    exit()

def enviar_para_google_sheets(nome_arquivo_csv, nome_planilha_google):
    print(f"\n[CLOUD] Iniciando upload para '{nome_planilha_google}'...", end="")
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Tenta carregar credenciais
        if not os.path.exists('minhas_credenciais.json'):
            print(" Erro: Arquivo 'minhas_credenciais.json' não encontrado.")
            return

        creds = ServiceAccountCredentials.from_json_keyfile_name('minhas_credenciais.json', scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo NOME
        spreadsheet = client.open(nome_planilha_google)
        
        # Lê o CSV gerado
        with open(nome_arquivo_csv, 'r', encoding='utf-8') as file:
            csv_content = file.read()
            
        # Envia (Importa) para a primeira aba
        # Nota: Isso SOBRESCREVE o conteúdo da aba 1
        client.import_csv(spreadsheet.id, csv_content)
        
        print(" Sucesso! Planilha atualizada.")
        
    except Exception as e:
        print(f" Falha no upload: {e}")

def extrair_numero_instancia(nome_arquivo):
    try:
        return int(nome_arquivo.split('_')[0])
    except:
        return 0 

def carregar_otimos_da_pasta(caminho_pasta):
    arquivo_optimos = os.path.join(caminho_pasta, 'optimos.txt')
    valores_otimos = []
    
    if os.path.exists(arquivo_optimos):
        with open(arquivo_optimos, 'r') as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        valores_otimos.append(int(float(linha)))
                    except ValueError:
                        pass 
    return valores_otimos

def rodar_benchmark_final(pasta_raiz='instancias', arquivo_saida='resultado_final_benchmark.csv'):
    
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminho_raiz = os.path.join(diretorio_script, pasta_raiz)
    
    if not os.path.exists(caminho_raiz):
        print(f"Erro: Pasta raiz '{caminho_raiz}' não encontrada.")
        return

    subpastas = [f for f in os.listdir(caminho_raiz) if os.path.isdir(os.path.join(caminho_raiz, f))]
    subpastas.sort()

    print(f"--- INICIANDO BENCHMARK EM {len(subpastas)} CLASSES DE INSTÂNCIAS ---\n")

    with open(arquivo_saida, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        header = [
            'Classe', 'Instancia', 
            'Otimo_Conhecido',
            'ACO_Ciclo', 'ACO_Tempo(s)', 'ACO_Gap_Real(%)',
            'Gurobi_Ciclo', 'Gurobi_Tempo(s)', 'Gurobi_Status', 'Gurobi_Gap_Interno(%)',
            'Gap_Relativo_ACO_vs_Gurobi(%)'
        ]
        writer.writerow(header)

        for pasta in subpastas:
            if pasta == 'geral': continue

            caminho_completo_pasta = os.path.join(caminho_raiz, pasta)
            
            # --- DEFINIÇÃO DE PARÂMETROS CAMPEÕES ---
            if pasta == 'hes':
                p_alpha_trab, p_beta_trab = 0.0, 2.5
                p_alpha_tar, p_beta_tar   = 2.0, 1.0
            elif pasta == 'ros':
                p_alpha_trab, p_beta_trab = 0.5, 3.0
                p_alpha_tar, p_beta_tar   = 1.0, 2.0
            elif pasta == 'ton':
                p_alpha_trab, p_beta_trab = 0.0, 2.0
                p_alpha_tar, p_beta_tar   = 0.0, 1.5
            else:
                p_alpha_trab, p_beta_trab = 1.0, 3.0
                p_alpha_tar, p_beta_tar   = 1.0, 2.0

            lista_otimos = carregar_otimos_da_pasta(caminho_completo_pasta)
            tem_gabarito = len(lista_otimos) > 0

            # Filtro Corrigido (Aceita arquivos sem extensão .txt)
            arquivos = [
                f for f in os.listdir(caminho_completo_pasta) 
                if os.path.isfile(os.path.join(caminho_completo_pasta, f)) 
                and f != 'optimos.txt' 
                and not f.startswith('.')
            ]
            arquivos.sort(key=extrair_numero_instancia)

            print(f"\n>>> Classe: {pasta.upper()} ({len(arquivos)} arquivos)")
            print(f"    Params: Trab({p_alpha_trab}, {p_beta_trab}) | Tar({p_alpha_tar}, {p_beta_tar})")

            for index, nome_instancia in enumerate(arquivos):
                caminho_instancia = os.path.join(caminho_completo_pasta, nome_instancia)
                
                otimo_real = None
                if tem_gabarito and index < len(lista_otimos):
                    otimo_real = lista_otimos[index]

                print(f"   > {nome_instancia} (Opt: {otimo_real if otimo_real else '?'}) ... ", end="", flush=True)

                dados = ler_e_converter_dados(caminho_instancia)
                if dados is None: 
                    print("Erro Leitura")
                    continue
                
                try:
                    t_tar_trab, grafo, precedencia, lb_calc, c_alvo, t_med_trab, fatiadas, grafoR,orderStrength = dados
                except ValueError:
                    print("Erro no retorno dos dados.")
                    continue

                # 1. ACO
                start = time.time()
                aco_ciclo = ACO(
                    t_tar_trab, grafo, precedencia, lb_calc, c_alvo, t_med_trab, 
                    fatiadas, grafoR,orderStrength,
                    alpha_trab=p_alpha_trab, beta_trab=p_beta_trab,
                    alpha_tar=p_alpha_tar, beta_tar=p_beta_tar,
                    numeroFormigas=200, nIteracoesSemMelhoria=300
                )
                tempo_aco = time.time() - start

                # 2. Gurobi (Limite 1h = 3600s)
                # Se quiser pular o Gurobi para teste rápido, comente e ponha gur_ciclo = float('inf')
                gur_ciclo, gur_tempo, gur_status, gur_gap_int = resolver_gurobi(caminho_instancia, time_limit=600)
                
                # 3. Gaps
                gap_aco = "-"
                gap_relativo = "-"

                base_comparacao = otimo_real if otimo_real else (gur_ciclo if gur_ciclo != float('inf') else None)

                if base_comparacao and aco_ciclo != float('inf'):
                    val = ((aco_ciclo - base_comparacao) / base_comparacao) * 100
                    gap_aco = f"{val:.2f}"
                
                if aco_ciclo != float('inf') and gur_ciclo != float('inf') and gur_ciclo > 0:
                    diff = aco_ciclo - gur_ciclo
                    val_rel = (diff / gur_ciclo) * 100
                    gap_relativo = f"{val_rel:.2f}"

                print(f"ACO: {aco_ciclo} | Gurobi: {gur_ciclo} [{gur_status}]")

                s_aco = f"{aco_ciclo:.1f}" if aco_ciclo != float('inf') else "INF"
                s_gur = f"{gur_ciclo:.1f}" if gur_ciclo != float('inf') else "INF"
                s_opt = str(otimo_real) if otimo_real else "-"
                s_gur_gap = f"{gur_gap_int:.2f}" if isinstance(gur_gap_int, (int, float)) else str(gur_gap_int)

                writer.writerow([
                    pasta, nome_instancia, 
                    s_opt,
                    s_aco, f"{tempo_aco:.2f}", gap_aco,
                    s_gur, f"{gur_tempo:.2f}", gur_status, s_gur_gap,
                    gap_relativo
                ])

    print(f"\n--- FIM. Resultados salvos em '{arquivo_saida}' ---")
    
    # 4. Enviar para Google Sheets (Último passo)
    enviar_para_google_sheets(arquivo_saida, 'TrabalhoPm') # Mude 'TrabalhoPm' para o nome da sua planilha

if __name__ == "__main__":
    rodar_benchmark_final('instancias')