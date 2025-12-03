import math
import random
import copy
import os
import csv
import time

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
        self.tempoDeCiclo = float('inf')
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
        self.tempoDeCiclo = maior
        return maior 

def ordenaTopologicamente(grafo,precedencia):
    contador = NUMERO_TAREFAS
    lista = []
    while(contador > 0):
        for i in range(NUMERO_TAREFAS):
            if precedencia[i] == 0:
                lista.append(i)
                contador -= 1
                precedencia[i] = -1
                for j in grafo[i]:
                    precedencia[j] -= 1
    return lista

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
    tarefasValidasDoTrab = [0]*NUMERO_TRABALHADORES_E_MAQUINAS 
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
                tarefasValidasDoTrab[j] += 1
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

    tempoMedioDeCadaTrabalhador = [tempoMedioDeCadaTrabalhador[i]/tarefasValidasDoTrab[i] for i in range(len(tempoMedioDeCadaTrabalhador)) if tarefasValidasDoTrab[i] > 0]
    
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
    lista = ordenaTopologicamente(grafo,precedencia[:])

    tamanhoBloco = NUMERO_TAREFAS//NUMERO_TRABALHADORES_E_MAQUINAS
    tarefasFatiadas = [] # A ideia e deixar as tarefas com menos precedencias pras primeiras maquinas.
    resto = NUMERO_TAREFAS%NUMERO_TRABALHADORES_E_MAQUINAS
    inicio = 0
    for i in range(NUMERO_TRABALHADORES_E_MAQUINAS):
        tamanhoAtual = tamanhoBloco +(1 if i < resto else 0)
        fim = inicio + tamanhoAtual
        lote = lista[inicio:fim]
        tarefasFatiadas.append(lote)
        inicio = fim
            
    return tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador,tarefasFatiadas
   
def sorteia(scores,soma,candidatos):
    if soma == 0:
       return candidatos[0]
   
    sorteio = random.uniform(0,soma)
    acumulado = 0
    for i in range(len(candidatos)):
        acumulado += scores[i]
        if acumulado >= sorteio:
            return candidatos[i]
        return candidatos[-1] #Segurança caso haja algum erro de float que bagunce a variavel de acumulação

def tempoMedioT(tempoTarefaTrabalhador,tarefasFatiadas,estacao):
    tempos = [0] * NUMERO_TRABALHADORES_E_MAQUINAS
    divide = [NUMERO_TRABALHADORES_E_MAQUINAS] * NUMERO_TAREFAS
    for tarefa in tarefasFatiadas[estacao]:
        for i in range(NUMERO_TRABALHADORES_E_MAQUINAS):
            if tempoTarefaTrabalhador[tarefa][i] == math.inf:
                divide[i] -= 1
            else:
                tempos[i]+= tempoTarefaTrabalhador[tarefa][i]
    tempos = [tempos[i]/divide[i] for i in range(NUMERO_TRABALHADORES_E_MAQUINAS)]
    return tempos

def alocaTrabalhadoresAEstacoes(formiga,tempoMedioDeCadaTrabalhador,feromoniosTE,tarefasFatiadas,tempoTarefaTrabalhador):
   #Sorteia um trabalhador para cada estação, com a probabilidade baseada num balanço de Feromonios depositados na escolha e o tempo medio de um trabalhador.
   alpha = 1
   beta = 2
   opcoes = list(range(NUMERO_TRABALHADORES_E_MAQUINAS))

   for i in range(NUMERO_TRABALHADORES_E_MAQUINAS):
      tempoMedio = tempoMedioT(tempoTarefaTrabalhador,tarefasFatiadas,i)
      scores = []
      soma = 0
      for trabalhador in opcoes:
         tau = feromoniosTE[trabalhador][i]**alpha
         eta = (1/tempoMedio[trabalhador])**beta
         p = tau*eta
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
    alpha = 1
    beta = 3.0
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
            else:
                formiga.calcularTempoDeCiclo()

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

def depositarFeromonios(formigas,mTE,mT):
    for f in formigas: 
        adicionado = 1/f.tempoDeCiclo
        
        for e in f.estacoes:
            mTE[e.trabalhadorId][e.idEstacao] += adicionado
        
        for t in e.tarefas:
            mT[e.idEstacao][t] += adicionado

def melhoriaSwap(formiga, grafo, grafoPredecessores, tempoTarefaTrabalhador):

    mapaTarefas = {}
    for i_est, estacao in enumerate(formiga.estacoes):
        for t in estacao.tarefas:
            mapaTarefas[t] = i_est

    def tarefaPesadaAleatoria(lista_tarefas, trabalhadorId, tempoTarefaTrabalhador, top_n=5):
        tarefasOrdenadas = sorted(lista_tarefas, key=lambda t: tempoTarefaTrabalhador[t][trabalhadorId], reverse=True)
        corte = min(len(tarefasOrdenadas), top_n)
        elite_pesada = tarefasOrdenadas[:corte]
        return random.choice(elite_pesada), tarefasOrdenadas
    
    def trocaPermitida(tarefaEstacaoPesada, tarefaTroca, estacaoPesadaId, estacaoTrocaId, grafo, grafoPredecessores):
        # Não permite troca se houver dependência direta entre as tarefas
        # ou se a troca violar a ordem de precedência da tarefa de troca
        for pai in grafoPredecessores[tarefaTroca]:
            if pai == tarefaEstacaoPesada:
                return False
            estacaoPai = mapaTarefas[pai+1] 
            if estacaoPai > estacaoPesadaId:
                return False
        
        # Não permite troca se houver dependência direta entre as tarefas
        # ou se a troca violar a ordem de precedência da tarefa de troca
        for filho in grafo[tarefaTroca]:
            if filho == tarefaEstacaoPesada:
                return False
            estacaoFilho = mapaTarefas[filho+1]
            if estacaoFilho < estacaoPesadaId:
                return False
        
        # Não permite troca se violar a ordem de precedência da tarefa da estação pesada
        for pai in grafoPredecessores[tarefaEstacaoPesada]:
            estacaoPai = mapaTarefas[pai+1] 
            if estacaoPai > estacaoTrocaId:
                return False

        # Não permite troca se violar a ordem de precedência da tarefa da estação pesada
        for filho in grafo[tarefaEstacaoPesada]:
            estacaoFilho = mapaTarefas[filho+1]
            if estacaoFilho < estacaoTrocaId:
                return False

        return True
    
    def calcularCarga(tarefas, trabalhadorId, tempoTarefaTrabalhador):
        carga = 0
        for t in tarefas:
            carga += tempoTarefaTrabalhador[t][trabalhadorId]
        
        return carga
    
    estacaoComMaisCarga = None
    carga = 0
    for i,e in enumerate(formiga.estacoes):
        if carga < e.carga:
            estacaoComMaisCarga = e
            indiceEstacaoComMaisCarga = i
            carga = e.carga
    
    loopsSemMelhoria = 0
    while(loopsSemMelhoria < 10):
        houveTroca = False
        for i, e in enumerate(formiga.estacoes):
            if i == indiceEstacaoComMaisCarga:
                continue

            melhoria = True
            while(melhoria):
                tarefaEstacaoComMaisCarga, tarefas1 = tarefaPesadaAleatoria(estacaoComMaisCarga.tarefas, estacaoComMaisCarga.trabalhadorId, tempoTarefaTrabalhador)
                tarefaParaTrocar, tarefas2 = tarefaPesadaAleatoria(e.tarefas, e.trabalhadorId, tempoTarefaTrabalhador)
                if trocaPermitida(tarefaEstacaoComMaisCarga-1, tarefaParaTrocar-1, estacaoComMaisCarga, i, formiga, grafo, grafoPredecessores):
                    tarefas1.remove(tarefaEstacaoComMaisCarga)
                    tarefas1.append(tarefaParaTrocar)
                    carga1 = calcularCarga(tarefas1, estacaoComMaisCarga.trabalhadorId, tempoTarefaTrabalhador)

                    tarefas2.remove(tarefaParaTrocar)
                    tarefas2.append(tarefaEstacaoComMaisCarga)
                    carga2 = calcularCarga(tarefas2, e.trabalhadorId, tempoTarefaTrabalhador)        

                    if carga1 < estacaoComMaisCarga.carga and carga2 < estacaoComMaisCarga.carga:
                        cargaTarefa1 = tempoTarefaTrabalhador[tarefaEstacaoComMaisCarga][estacaoComMaisCarga.trabalhadorId]
                        cargaTarefa2 = tempoTarefaTrabalhador[tarefaParaTrocar][e.trabalhadorId]

                        formiga.removerTarefa(indiceEstacaoComMaisCarga, tarefaEstacaoComMaisCarga, cargaTarefa1)
                        formiga.removerTarefa(i, tarefaParaTrocar, cargaTarefa2)
                        
                        cargaTarefa1 = tempoTarefaTrabalhador[tarefaEstacaoComMaisCarga][e.trabalhadorId]
                        cargaTarefa2 = tempoTarefaTrabalhador[tarefaParaTrocar][estacaoComMaisCarga.trabalhadorId]

                        formiga.alocarTarefa(indiceEstacaoComMaisCarga, tarefaParaTrocar, cargaTarefa2)
                        formiga.alocarTarefa(i, tarefaEstacaoComMaisCarga, cargaTarefa1)
                        houveTroca = True
                        mapaTarefas[tarefaEstacaoComMaisCarga] = i
                        mapaTarefas[tarefaParaTrocar] = indiceEstacaoComMaisCarga
                    else:
                        melhoria = False

                else:
                    melhoria = False
            
        
        if not houveTroca: 
            loopsSemMelhoria += 1
        else:
            loopsSemMelhoria = 0
            carga = 0
            for i,e in enumerate(formiga.estacoes):
                if carga < e.carga:
                    estacaoComMaisCarga = e
                    indiceEstacaoComMaisCarga = i
                    carga = e.carga
    
def ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador,tarefasFatiadas):
    feromonioInicial = 1/C_alvo
    feromoniosTE = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Trabalhador][Estacao]
    feromoniosTarefas = [[feromonioInicial for _ in range(NUMERO_TAREFAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Estacao][Tarefa]
    melhorGlobal = math.inf
    iteracoesSemMelhoria = 0
    formigas = [Formiga(i) for i in range(200)]
    melhorFormigaGlobal = None

    while((iteracoesSemMelhoria < 200) and (melhorGlobal > lowerBound)):
        melhorFormigaLocal = None
        for f in formigas:
            f.resetar() #Reseta a formiga para a nova iteração
            alocaTrabalhadoresAEstacoes(f,tempoMedioDeCadaTrabalhador,feromoniosTE,tarefasFatiadas,tempoTarefaTrabalhador)
            alocaTarefas(f,feromoniosTarefas,C_alvo,precedencia,grafo,tempoTarefaTrabalhador)
            #printaSolução(f)
            #Algoritmo de melhoria para a solução de cada formiga entra aqui

            if  melhorFormigaLocal is None or f.tempoDeCiclo < melhorFormigaLocal.tempoDeCiclo:
                melhorFormigaLocal = f 

        #print(melhorFormigaLocal.tempoDeCiclo)
        if melhorFormigaLocal.tempoDeCiclo < melhorGlobal:
            #print(f"Solução melhorada de: {melhorGlobal} pra {melhorFormigaLocal.tempoDeCiclo}")
            melhorGlobal = melhorFormigaLocal.tempoDeCiclo
            melhorFormigaGlobal = copy.deepcopy(melhorFormigaLocal)
            iteracoesSemMelhoria = 0
        else:
            iteracoesSemMelhoria += 1
        
        evaporacao(feromoniosTE,feromoniosTarefas)
        if melhorFormigaGlobal is not None:
            formigasValidas = [f for f in formigas if f.tempoDeCiclo < math.inf]
            formigasValidas.sort(key=lambda x:x.tempoDeCiclo)
            qtdFormigas = max(1,int(len(formigas)*0.10)) #Pega as 10% melhores formigas
            melhoresFormigas = formigasValidas[:qtdFormigas]
            depositarFeromonios(melhoresFormigas,feromoniosTE,feromoniosTarefas)


    return melhorGlobal

def exe(nomeArquivo):
   tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador, tarefasFatiadas = ler_e_converter_dados(nomeArquivo)
   return ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador,tarefasFatiadas)

if __name__ == "__main__":
    nome_do_arquivo = 'instancias/2_hes'
    dados = ler_e_converter_dados(nome_do_arquivo)

    if dados:
        tempoTarefaTrabalhador, grafo, precedencia, lowerBound, tempoMedio, tempoMedioDeCadaTrabalhador,tarefasFatiadas = dados
        print(f"Iniciando ACO isolado... LB={lowerBound}")
        res = ACO(tempoTarefaTrabalhador, grafo, precedencia, lowerBound, tempoMedio, tempoMedioDeCadaTrabalhador,tarefasFatiadas)
        print(f"Resultado Final: {res}")

#Pontos para aprimorar:

# Usar uma estrategia mais inteligente no peso da heuristica de alocar o trabalhador a estação. Sugestao se a estação e inicial e provavel que tarefas que nao dependem de ninguem ou que dependem de poucos, sejam executadas nelas, logo um trabalhador que realiza bem essas tarefas seria uma escolha melhor
