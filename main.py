import math
import random

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
    global NUMERO_TAREFAS
    global NUMERO_TRABALHADORES_E_MAQUINAS
    NUMERO_TAREFAS = int(conteudo[0]) #A primeira linha do arquivo e o numero de tarefas
    NUMERO_TRABALHADORES_E_MAQUINAS = len(conteudo[1].split()) #Ve quantos elementos tem na segunda linha do arquivo para definir o numero de maquinas e trabalhadores
    elementosLinha = []
    tempoMedioDeCadaTrabalhador = [0]*NUMERO_TRABALHADORES_E_MAQUINAS
    quantasTarefasCadaTrabalhadorEIncapaz = [0]*NUMERO_TRABALHADORES_E_MAQUINAS 
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
                quantasTarefasCadaTrabalhadorEIncapaz[j] += 1
            else:
                trabalhadorApto += 1
                elementosLinha[j] = int(elementosLinha[j])
                if(elementosLinha[j] < menorDaLinha):
                    menorDaLinha = elementosLinha[j]
                tempoMedioTarefa += elementosLinha[j]
                tempoMedioDeCadaTrabalhador[j] += elementosLinha[j]
                
        tempoTarefaTrabalhador.append(elementosLinha)
        lowerBound += menorDaLinha 
        tempoMedio += tempoMedioTarefa/trabalhadorApto

    lowerBound = math.ceil(lowerBound/NUMERO_TRABALHADORES_E_MAQUINAS) #Melhor solução no cenario perfeitop
    tempoMedio = (tempoMedio/NUMERO_TRABALHADORES_E_MAQUINAS)

    tempoMedioDeCadaTrabalhador = [tempoMedioDeCadaTrabalhador[i]/NUMERO_TAREFAS - quantasTarefasCadaTrabalhadorEIncapaz[i] for i in range(len(tempoMedioDeCadaTrabalhador))]
    
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

    return tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador
   
def sorteiaTrabalhador(scores,soma,candidatos):
   sorteio = random.uniform(0,soma)
   acumulado = 0
   for i in range(len(candidatos)):
      acumulado += scores[i]
      if acumulado >= sorteio:
         return candidatos[i]

def alocaTrabalhadoresAEstacoes(formiga,tempoMedioDeCadaTrabalhador,feromoniosTrabalhadorEstacao):
   alpha = 0.3
   beta = 0.7
   opcoes = list(range(NUMERO_TRABALHADORES_E_MAQUINAS))
   probabilidade = []
   for i in range(NUMERO_TRABALHADORES_E_MAQUINAS):
      scores = []
      soma = 0
      for j in range(len(opcoes)):
         p = ((feromoniosTrabalhadorEstacao[i][j]**beta) *((1/tempoMedioDeCadaTrabalhador[j])**alpha))
         scores.append(p)
         soma += p
      sorteado = sorteiaTrabalhador(scores,soma,opcoes)
      opcoes.remove(sorteado)
      formiga.alocarTrabalhador(i,sorteado)
      
def ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador):
  feromonioInicial = 1/C_alvo
  feromoniosTrabalhadorEstacao = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
  feromoniosTrabalhadorTarefas = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
  melhorGlobal = math.inf
  iteracoesSemMelhoria = 0
  formigas = [Formiga(i) for i in range(100000)]
  #alocaTrabalhadoresAEstacoes(formigas[0],tempoMedioDeCadaTrabalhador,feromoniosTrabalhadorEstacao)

 # while((iteracoesSemMelhoria < 100) and (melhorGlobal > lowerBound)): 
  for f in formigas:
    alocaTrabalhadoresAEstacoes(f,tempoMedioDeCadaTrabalhador,feromoniosTrabalhadorEstacao)
    print(f"A formiga escolheu as seguintes alocações")
    for i in f.estacoes:
         print(i.idEstacao,i.trabalhadorId)
  



nome_do_arquivo = 'instancias/23_hes'
tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador = ler_e_converter_dados(nome_do_arquivo)
ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador)

