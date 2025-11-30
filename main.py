import math
import random
import copy

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
      self.carga = 0

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
   
def sorteia(scores,soma,candidatos):
   sorteio = random.uniform(0,soma)
   acumulado = 0
   for i in range(len(candidatos)):
      acumulado += scores[i]
      if acumulado >= sorteio:
         return candidatos[i]

def alocaTrabalhadoresAEstacoes(formiga,tempoMedioDeCadaTrabalhador,feromoniosTrabalhadorEstacao):
   #Sorteia um trabalhador para cada estação, com a probabilidade baseada num balanço de Feromonios depositados na escolha e o tempo medio de um trabalhador.
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
      sorteado = sorteia(scores,soma,opcoes)
      opcoes.remove(sorteado)
      formiga.alocarTrabalhador(i,sorteado)

def printaSolução(f):
    print(f"Formiga {f.id}:")
    for e in f.estacoes:
        tarefas_formatadas = ", ".join(str(t) for t in e.tarefas)
        print(f"(Estacao: {e.idEstacao}, Trabalhador {e.trabalhadorId}) - Tarefas: {tarefas_formatadas}")
        f.calcularTempoDeCiclo()
    print(f"Tempo de ciclo: {f.tempoDeCiclo}")

def alocaTarefas(formiga,feromoniosTarefas,C_alvo,precedencia,grafo,tempoTarefaTrabalhador):
    alpha = 0.5
    beta = 0.5
    tarefas = []
    precedenciaLocal = precedencia[:]
    tarefasFeitas = 0

    def getTempo(trabId,traId):
        return tempoTarefaTrabalhador[traId][trabId]

    for iEstacao, e in enumerate(formiga.estacoes):
        ehUltima = (iEstacao == len(formiga.estacoes) - 1) #Flag pra saber se e a ultima tarefa

        while(tarefasFeitas < NUMERO_TAREFAS):

            if not ehUltima and e.carga >= C_alvo: #Se nao for a ultima e ja tiver ultrapassado a carga media, va pra proxima estação
                break

            if ehUltima: #Se for a ultima tarefa, aceita fazer mesmo com tempo infinito
                tarefas = [x for x in range(len(precedenciaLocal)) if precedenciaLocal[x] == 0]
            else: # Seleciona as tarefas podem ser realizadas neste momento
                tarefas = [x for x in range(len(precedenciaLocal)) if precedenciaLocal[x] == 0 and getTempo(e.trabalhadorId,x) != math.inf] 

            if len(tarefas) == 0: #Caso onde nao a nenhuma tarefa disponivel para ser feita 
                break
            
            soma = 0
            scores = [0] * len(tarefas)

            for i in range(len(tarefas)): # Calcula cada score das tarefas POSSIVEIS e acumula tudo em soma
                tarefaId = tarefas[i]
                tempoReal = getTempo(e.trabalhadorId,tarefaId)

                if tempoReal == math.inf:
                    tempoReal = 10000 #Se trabalhador nao for capaz de realizar a tarefa, a solução sera penalizada

                tau = feromoniosTarefas[e.idEstacao][tarefaId]
                eta = (1/tempoReal)
                scores[i] = (tau**alpha) * (eta**beta)
                soma += scores[i]

            sorteado = sorteia(scores,soma,tarefas)
            tempoFinal = getTempo(e.trabalhadorId,sorteado) 
            if tempoFinal == math.inf:
                tempoFinal = 10000
            formiga.alocarTarefa(e.idEstacao,sorteado,tempoFinal)

            precedenciaLocal[sorteado] = -1
            for j in grafo[sorteado]:
                precedenciaLocal[j] = precedenciaLocal[j] -1
            tarefasFeitas += 1

    if tarefasFeitas < NUMERO_TAREFAS: #Se sair do loop e ainda sobrar tarefas, penaliza a formiga
        formiga.tempoDeCiclo = math.inf

def evaporacao(m1,m2):
    rho = 0.1
    for i in range(len(m1)):
        for j in range(len(m1[i])):
            m1[i][j] = (1 - rho) * m1[i][j]

            if m1[i][j] == 0: #Proteção pro feromonio nao chegar em 0
                m1[i][j] = 0.0001

    for i in range(len(m2)):
        for j in range(len(m2[i])):
            m2[i][j] = (1 - rho) * m2[i][j]

            if m2[i][j] == 0: #Proteção pro feromonio nao chegar em 0
                m2[i][j] = 0.0001

def depositarFeromonios(formiga,mTE,mT):
    adicionado = 1/formiga.tempoDeCiclo

    for e in formiga.estacoes:
        mTE[e.trabalhadorId][e.idEstacao] += adicionado
        
        for t in e.tarefas:
            mT[e.idEstacao][t] += adicionado
    
def ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador):
    feromonioInicial = 1/C_alvo
    feromoniosTE = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Trabalhador][Estacao]
    feromoniosTarefas = [[feromonioInicial for _ in range(NUMERO_TAREFAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Estacao][Tarefa]
    melhorGlobal = math.inf
    iteracoesSemMelhoria = 0
    formigas = [Formiga(i) for i in range(10)]
    melhorFormigaGlobal = None

    while((iteracoesSemMelhoria < 10000) and (melhorGlobal > lowerBound)):
        melhorFormigaLocal = None
        for f in formigas:
            f.resetar() #Reseta a formiga para a nova iteração
            alocaTrabalhadoresAEstacoes(f,tempoMedioDeCadaTrabalhador,feromoniosTE)
            alocaTarefas(f,feromoniosTarefas,C_alvo,precedencia,grafo,tempoTarefaTrabalhador)
            #printaSolução(f)
            #Algoritmo de melhoria para a solução de cada formiga entra aqui
            f.calcularTempoDeCiclo()

            if  melhorFormigaLocal is None or f.tempoDeCiclo < melhorFormigaLocal.tempoDeCiclo:
                melhorFormigaLocal = f 

        if melhorFormigaLocal.tempoDeCiclo < melhorGlobal:
            print(f"Solução melhorado de: {melhorGlobal} pra {melhorFormigaLocal.tempoDeCiclo}")
            melhorGlobal = melhorFormigaLocal.tempoDeCiclo
            melhorFormigaGlobal = copy.deepcopy(melhorFormigaLocal)
            iteracoesSemMelhoria = 0
        else:
            iteracoesSemMelhoria += 1
        
        evaporacao(feromoniosTE,feromoniosTarefas)
        if melhorFormigaGlobal is not None:
            depositarFeromonios(melhorFormigaGlobal,feromoniosTE,feromoniosTarefas)


    return melhorGlobal

    

nome_do_arquivo = 'instancias/23_hes'
tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador = ler_e_converter_dados(nome_do_arquivo)
ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador)

