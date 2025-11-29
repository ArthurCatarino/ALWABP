import math

NUMERO_TAREFAS = 0
NUMERO_TRABALHADORES_E_MAQUINAS = 0

class Estacao:
    def __init__(self,idEstacao):
      self.idEstacao = idEstacao
      self.trabalhadorId = None
      self.tarefas = []
      self.carga = 0

    def limpar(self):
      self.trabalhadorId = None
      self.tarefas = []
      self.carga = []

class Formiga:
    def __init__(self,id):
      self.id = id
      self.estacoes = [Estacao(i) for i in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
      self.tempoDeCiclo = math.inf
    
    def resetar(self):
        self.cmax = float('inf')
        for estacao in self.estacoes:
            estacao.limpar()

    def alocarTrabalhador(self,indiceEstacao,idTrabalhador):
        self.estacoes[indiceEstacao].trabalhadorId = idTrabalhador

    def alocarTarefa(self,indiceEstacao,idTarefa,tempoExecucao):
       self.estacoes[indiceEstacao].tarefas.append(idTarefa)
       self.estacoes[indiceEstacao].carga += tempoExecucao

    def calcularTempoDeCiclo(self):
        maior = 0
        for e in self.estacoes:
            if(e.carga > maior):
                maior = e.carga
        tempoDeCiclo = maior
        return maior 

def ler_e_converter_dados(caminho_arquivo):
    tempoTarefaTrabalhador = []
    try:
        #Copia todo o arquivo do TXT  para um grande array onde cada linha e um elemento
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.readlines()
            conteudo = [x.strip('\n') for x in conteudo]
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return None

    NUMERO_TAREFAS = int(conteudo[0]) #A primeira linha do arquivo e o numero de tarefas
    NUMERO_TRABALHADORES_E_MAQUINAS = len(conteudo[1].split()) #Ve quantos elementos tem na segunda linha do arquivo para definir o numero de maquinas e trabalhadores
    elementosLinha = []
    lowerBound = 0
    tempoMedio = 0
    #Cria a matriz do tempo de cada trabalhador em cada tarefa
    for i in range(NUMERO_TAREFAS):
        elementosLinha = conteudo[i+1].split() #Transforma a string: '1,2,3' em um array ['1','2','2']
        menorDaLinha = math.inf
        tempoMedioTarefa = 0
        trabalhadorApto = 0
        for j in range(len(elementosLinha)): #Transforma todos os elementos de uma linha em inteiros, que sao os tempos de cada trabalhador em cada tarefa
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

    lowerBound = math.ceil(lowerBound/NUMERO_TRABALHADORES_E_MAQUINAS) #Melhor solução no cenario perfeitop
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

    return tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio

def ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo):
  feromonioInicial = 1/C_alvo
  feromoniosTrabalhadorEstacao = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
  feromoniosTrabalhadorTarefas = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
  melhorGlobal = math.inf
  iteracoesSemMelhoria = 0
  formigas = [Formiga(i) for i in range(10)]
  print(formigas)

 # while((iteracoesSemMelhoria < 0) and (melhorGlobal > lowerBound)): 
    
  



nome_do_arquivo = 'instancias/teste'
tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio = ler_e_converter_dados(nome_do_arquivo)
ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio)

