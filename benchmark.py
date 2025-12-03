import os
import csv
import time
import math
import gspread
from oauth2client.service_account import ServiceAccountCredentials

try:
    # Importa do main.py (ACO e Leitura para o ACO)
    from main import ACO, ler_e_converter_dados
    
    # Importa do solver_gurobi.py (Função Wrapper)
    from solver_gurobi import resolver_gurobi
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Verifique se 'main.py' e 'solver_gurobi.py' estão na mesma pasta.")
    exit()

def rodar_comparativo_final(nome_pasta_instancias, arquivo_saida='resultados_finais.csv'):
    
    # Truque para pegar o caminho correto independente de onde você roda o script
    diretorio_script = os.path.dirname(os.path.abspath(__file__))
    caminho_instancias = os.path.join(diretorio_script, nome_pasta_instancias)
    
    if not os.path.exists(caminho_instancias):
        print(f"Erro: Pasta '{caminho_instancias}' não encontrada.")
        return

    # Filtra arquivos validos
    arquivos = [
        f for f in os.listdir(caminho_instancias) 
        if os.path.isfile(os.path.join(caminho_instancias, f)) and not f.startswith('.')
    ]
    arquivos.sort()

    if not arquivos:
        print("Nenhum arquivo encontrado na pasta.")
        return

    print(f"--- INICIANDO BENCHMARK (Limite Gurobi: 10min) ---\n")

    with open(arquivo_saida, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # CABEÇALHO COMPLETO
        header = [
            'Instancia', 
            'ACO_Ciclo', 'ACO_Tempo(s)',
            'Gurobi_Ciclo', 'Gurobi_Tempo(s)', 
            'Gurobi_Status', 'Gurobi_Gap_Interno(%)', # Colunas novas
            'Gap_Relativo_ACO_vs_Gurobi(%)' # Comparação final
        ]
        writer.writerow(header)

        for nome_instancia in arquivos:
            caminho_completo = os.path.join(caminho_instancias, nome_instancia)
            print(f"> Processando: {nome_instancia}")

            # ---------------------------
            # 1. Executar ACO
            # ---------------------------
            print("  [ACO] ...", end="", flush=True)
            
            # Leitura específica para o ACO (formato do main.py)
            dados = ler_e_converter_dados(caminho_completo)
            if dados is None: 
                print(" Erro Leitura ACO")
                continue
            
            t_tarefa_trab, grafo, precedencia, lb, c_alvo, t_medio_trab = dados
            
            start_aco = time.time()
            # Roda a formiga
            aco_ciclo = ACO(t_tarefa_trab, grafo, precedencia, lb, c_alvo, t_medio_trab)
            end_aco = time.time()
            aco_tempo = end_aco - start_aco
            
            # Formatação visual
            s_aco = f"{aco_ciclo:.1f}" if aco_ciclo != math.inf else "INF"
            print(f" Ciclo: {s_aco} ({aco_tempo:.2f}s)")

            # ---------------------------
            # 2. Executar Gurobi
            # ---------------------------
            print("  [Gurobi] ...", end="", flush=True)
            
            # Chama a função do arquivo solver_gurobi.py
            # Ela retorna 4 valores agora: Obj, Tempo, Status, GapInterno
            g_ciclo, g_tempo, g_status, g_gap_interno = resolver_gurobi(caminho_completo, time_limit=600)
            
            # Formatação visual
            s_gur = f"{g_ciclo:.1f}" if g_ciclo != float('inf') else "INF"
            print(f" Ciclo: {s_gur} [{g_status} Gap:{g_gap_interno:.2f}%]")

            # ---------------------------
            # 3. Cálculos de Métricas
            # ---------------------------

            # Gap Relativo (Quanto o ACO perdeu ou ganhou do Gurobi)
            # (ACO - Gurobi) / Gurobi
            gap_relativo = "-"
            if aco_ciclo != math.inf and g_ciclo != float('inf') and g_ciclo > 0:
                diff = aco_ciclo - g_ciclo
                val_gap = (diff / g_ciclo) * 100
                gap_relativo = f"{val_gap:.2f}"

            # Escreve linha na planilha
            writer.writerow([
                nome_instancia,
                s_aco, f"{aco_tempo:.4f}",
                s_gur, f"{g_tempo:.4f}",
                g_status, f"{g_gap_interno:.4f}",
                gap_relativo
            ])

    print(f"\n--- FIM. Resultados salvos em '{arquivo_saida}' ---")

def enviar_para_google_sheets(nome_arquivo_csv, nome_planilha_google):
    print("  -> Sincronizando com Google Sheets...", end="")
    
    # Define o escopo
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Carrega credenciais
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('minhas_credenciais.json', scope)
        client = gspread.authorize(creds)
    except Exception as e:
        print(f" Erro nas credenciais: {e}")
        return

    try:
        # 1. Abre a PLANILHA (O arquivo inteiro)
        spreadsheet = client.open(nome_planilha_google)
        
        # 2. Lê o CSV que você gerou
        with open(nome_arquivo_csv, 'r', encoding='utf-8') as file:
            csv_content = file.read()
            
        # 3. Manda o CSV para o ID da Planilha (Spreadsheet ID), e não da aba
        client.import_csv(spreadsheet.id, csv_content)
        
        print(" Sucesso!")
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f" Erro: Planilha '{nome_planilha_google}' não encontrada! Verifique o nome ou se compartilhou com o robô.")
    except Exception as e:
        print(f" Erro ao sincronizar: {e}")

if __name__ == "__main__":
    rodar_comparativo_final('instancias')
    enviar_para_google_sheets('resultados_finais.csv','TrabalhoPm')