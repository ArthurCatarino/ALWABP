import os

# Caminho para a pasta que deu erro no seu print
caminho_hes = os.path.join('instancias', 'hes')

print(f"--- DIAGNÓSTICO DA PASTA: {os.path.abspath(caminho_hes)} ---")

if not os.path.exists(caminho_hes):
    print("ERRO CRÍTICO: A pasta 'hes' nem sequer existe!")
else:
    arquivos = os.listdir(caminho_hes)
    print(f"Arquivos encontrados ({len(arquivos)}):")
    for f in arquivos:
        print(f" - '{f}'") # As aspas mostram se tem espaço em branco escondido

    print("\n--- TENTANDO LER 'optimos.txt' ---")
    caminho_arquivo = os.path.join(caminho_hes, 'optimos.txt')
    
    if os.path.exists(caminho_arquivo):
        print("SUCESSO: Arquivo encontrado!")
        try:
            with open(caminho_arquivo, 'r') as f:
                linhas = f.readlines()
                print(f"Lido com sucesso. Tem {len(linhas)} linhas.")
                print(f"Primeira linha: '{linhas[0].strip()}'")
                
                # Teste de conversão
                try:
                    valor = int(float(linhas[0].strip()))
                    print(f"Conversão numérica OK: {valor}")
                except:
                    print("ERRO: A primeira linha não é um número válido!")
        except Exception as e:
            print(f"Erro ao abrir o arquivo: {e}")
    else:
        print("FALHA: O arquivo 'optimos.txt' NÃO foi encontrado pelo Python.")
        
        # Checa se é o erro da extensão dupla
        if 'optimos.txt.txt' in arquivos:
            print("AVISO: Encontrei um 'optimos.txt.txt'. Renomeie para tirar o .txt extra!")