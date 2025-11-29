import math

NUMERO_TAREFAS = 0
NUMERO_TRABALHADORES_E_MAQUINAS = 0

def ler_e_converter_dados(caminho_arquivo):
    tempoTarefaTrabalhador = []
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.readlines()
            conteudo = [x.strip('\n') for x in conteudo]
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None

    NUMERO_TAREFAS = int(conteudo[0])
    NUMERO_TRABALHADORES_E_MAQUINAS = len(conteudo[1].split())
    elementosLinha = []
    lowerBound = 0
    tempoMedio = 0
    #Cria a matriz do tempo de cada trabalhador em cada tarefa
    for i in range(NUMERO_TAREFAS):
        elementosLinha = conteudo[i+1].split()
        menorDaLinha = math.inf
        tempoMedioTarefa = 0
        trabalhadorApto = 0
        for j in range(len(elementosLinha)):
            if elementosLinha[j] == 'Inf':
                elementosLinha[j] = math.inf
            else:
                trabalhadorApto += 1
                elementosLinha[j] = int(elementosLinha[j])
                if(elementosLinha[j] < menorDaLinha):
                    menorDaLinha = elementosLinha[j]
                tempoMedioTarefa += elementosLinha[j]
                
        tempoTarefaTrabalhador.append(elementosLinha)
        lowerBound += menorDaLinha
        tempoMedio += tempoMedioTarefa/trabalhadorApto

    lowerBound = math.ceil(lowerBound/NUMERO_TRABALHADORES_E_MAQUINAS)
    tempoMedio = (tempoMedio/NUMERO_TRABALHADORES_E_MAQUINAS)
    #Cria grafo de precedencia das tarefas
    grafo = [[] for _ in range(NUMERO_TAREFAS)]
    precedencia = [0]*NUMERO_TAREFAS

    indice = NUMERO_TAREFAS+1
    while(conteudo[indice] != '-1 -1'):
        linha = conteudo[indice].split()
        linha[0] = int(linha[0])
        linha[1] = int(linha[1])
        grafo[linha[0]-1].append(linha[1]-1)
        precedencia[linha[1]-1] += 1
        indice = indice+1

    print("a")
    return tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio



nome_do_arquivo = 'instancias/teste'

tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio = ler_e_converter_dados(nome_do_arquivo)
print(tempoTarefaTrabalhador)

