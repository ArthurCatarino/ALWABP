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
    
    def removerTarefa(self, indiceEstacao, idTarefa, tempoExecucao):
        self.estacoes[indiceEstacao].tarefas.remove(idTarefa)
        self.estacoes[indiceEstacao].carga -= tempoExecucao

        if self.estacoes[indiceEstacao].carga < 0.0001:  #Evita erros de ponto flutuante
            self.estacoes[indiceEstacao].carga = 0

def calcular_order_strength(matrizAdjacencia):
    #Algoritmo de Floyd-Warshall (ou Fechamento Transitivo), descobre as conexões indiretas: Se A->B e B->C, então marca A->C
    for k in range(NUMERO_TAREFAS):
        for i in range(NUMERO_TAREFAS):
            for j in range(NUMERO_TAREFAS):
                if matrizAdjacencia[i][k] and matrizAdjacencia[k][j]:
                    matrizAdjacencia[i][j] = 1
                    
    totalRelacoes = sum(sum(linha) for linha in matrizAdjacencia)

    #Calcula qual o numero maxino de relações dado pela formiga (n(n-1))/2
    maxPossivel = (NUMERO_TAREFAS * (NUMERO_TAREFAS - 1)) / 2 

    if maxPossivel == 0: return 0 # Evita divisão por zero
    
    os = totalRelacoes / maxPossivel
    return os

def auditar_solucao(formiga, grafo, tempoTarefaTrabalhador, num_tarefas):
    print(f"\n--- AUDITORIA DA FORMIGA {formiga.id} (Ciclo: {formiga.tempoDeCiclo}) ---")
    
    erros = 0
    tarefas_alocadas = set()
    mapa_tarefa_estacao = {}

    # 1. Verifica integridade das tarefas e trabalhadores
    for estacao in formiga.estacoes:
        trab_id = estacao.trabalhadorId
        
        if trab_id is None:
            # Estação vazia é permitida, mas vamos avisar
            continue
            
        for t in estacao.tarefas:
            # Checa duplicidade
            if t in tarefas_alocadas:
                print(f"[ERRO] Tarefa {t} alocada mais de uma vez!")
                erros += 1
            tarefas_alocadas.add(t)
            mapa_tarefa_estacao[t] = estacao.idEstacao
            
            # Checa capacidade do trabalhador
            tempo = tempoTarefaTrabalhador[t][trab_id] # CUIDADO COM OS ÍNDICES [Tarefa][Trab]
            if tempo == math.inf:
                print(f"[ERRO] Trab {trab_id} na Est {estacao.idEstacao} NÃO sabe fazer tarefa {t}!")
                erros += 1

    # 2. Verifica se todas as tarefas foram feitas
    if len(tarefas_alocadas) != num_tarefas:
        print(f"[ERRO] Total de tarefas: {num_tarefas}. Alocadas: {len(tarefas_alocadas)}.")
        erros += 1

    # 3. Verifica Precedência (O ERRO DEVE ESTAR AQUI)
    # Para cada tarefa, verifica se seus filhos estão em estações >=
    for pai in range(num_tarefas):
        if pai not in mapa_tarefa_estacao: continue # Se não foi alocada, já deu erro acima
        
        estacao_pai = mapa_tarefa_estacao[pai]
        
        for filho in grafo[pai]:
            if filho in mapa_tarefa_estacao:
                estacao_filho = mapa_tarefa_estacao[filho]
                
                if estacao_pai > estacao_filho:
                    print(f"[ERRO PRECEDÊNCIA] Pai {pai} (Est {estacao_pai}) está DEPOIS do Filho {filho} (Est {estacao_filho})")
                    erros += 1

    # 4. Recalcula o Tempo na Unha (Para ver se a soma está certa)
    cmax_calculado = 0
    for estacao in formiga.estacoes:
        trab_id = estacao.trabalhadorId
        carga_real = 0
        for t in estacao.tarefas:
            carga_real += tempoTarefaTrabalhador[t][trab_id]
        
        if abs(carga_real - estacao.carga) > 0.1:
            print(f"[ERRO SOMA] Est {estacao.idEstacao}: Diz {estacao.carga}, mas soma real é {carga_real}")
            erros += 1
        
        if carga_real > cmax_calculado:
            cmax_calculado = carga_real

    if erros == 0:
        print(">> SOLUÇÃO VÁLIDA E VERIFICADA! O Gurobi está errado ou mal configurado.")
    else:
        print(f">> SOLUÇÃO INVÁLIDA! Encontrados {erros} erros.")

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

    tempoMedioDeCadaTrabalhador = [tempoMedioDeCadaTrabalhador[i]/tarefasValidasDoTrab[i] for i in range(len(tempoMedioDeCadaTrabalhador)) if tarefasValidasDoTrab[i] > 0]
    
    #Cria grafo de precedencia das tarefas (Tarefa -> filhos) e o inverso dele (Tarefa -> pais)
    grafoR = [[]for _ in range(NUMERO_TAREFAS)]
    grafo = [[] for _ in range(NUMERO_TAREFAS)]
    matrizAdjacencia = [[0]*NUMERO_TAREFAS for _ in range(NUMERO_TAREFAS)]
    precedencia = [0]*NUMERO_TAREFAS
    indice = NUMERO_TAREFAS+1
    while(conteudo[indice] != '-1 -1'):
        linha = conteudo[indice].split()
        linha[0] = int(linha[0])
        linha[1] = int(linha[1])
        grafo[linha[0]-1].append(linha[1]-1)
        grafoR[linha[1]-1].append(linha[1]-1)
        matrizAdjacencia[linha[0]-1][linha[1]-1] = 1
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
    orderStrenght = calcular_order_strength(matrizAdjacencia)
    return tempoTarefaTrabalhador,grafo,precedencia,lowerBound,tempoMedio,tempoMedioDeCadaTrabalhador,tarefasFatiadas,grafoR,orderStrenght
   
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

def alocaTrabalhadoresAEstacoes(formiga,tempoMedioDeCadaTrabalhador,feromoniosTE,tarefasFatiadas,tempoTarefaTrabalhador,alpha,beta,orderStrength):
   #Sorteia um trabalhador para cada estação, com a probabilidade baseada num balanço de Feromonios depositados na escolha e o tempo medio de um trabalhador.
   opcoes = list(range(NUMERO_TRABALHADORES_E_MAQUINAS))

   for i in range(NUMERO_TRABALHADORES_E_MAQUINAS):
      tempoMedio = tempoMedioT(tempoTarefaTrabalhador,tarefasFatiadas,i)
      scores = []
      soma = 0
      for trabalhador in opcoes:
         tau = feromoniosTE[trabalhador][i]
         hPosicional = orderStrength*1/(tempoMedio[trabalhador]) #Da um peso na heuristica global e posicional pelo OS do grafo
         hGlobal = (1-orderStrength)*(1/tempoMedioDeCadaTrabalhador[trabalhador])
         eta = hPosicional+hGlobal
         p = (tau**alpha)*(eta**beta)
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

def alocaTarefas(formiga,feromoniosTarefas,C_alvo,precedencia,grafo,tempoTarefaTrabalhador,alpha,beta):
    tarefas = []
    precedenciaLocal = precedencia[:]
    tarefasFeitas = 0
    cargaAlocadaEstimada = 0
    def getTempo(trabId,traId):
        return tempoTarefaTrabalhador[traId][trabId]


    for iEstacao, e in enumerate(formiga.estacoes):
        ehUltima = (iEstacao == len(formiga.estacoes) - 1) #Flag pra saber se e a ultima tarefa
        estacoes_restantes = NUMERO_TRABALHADORES_E_MAQUINAS - iEstacao

        if estacoes_restantes > 0:
            cargaRestante = C_alvo - cargaAlocadaEstimada
            C_alvoDinamico = cargaRestante/ estacoes_restantes
        else:
            C_alvoDinamico = math.inf

        #C_alvoDinamico = C_alvoDinamico*1.10 # Relaxa o limite de carga

        while(tarefasFeitas < NUMERO_TAREFAS):
            if not ehUltima and e.carga >= C_alvoDinamico: #Se nao for a ultima e ja tiver ultrapassado a carga media, va pra proxima estação
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
            cargaAlocadaEstimada += tempoFinal

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
        adicionado = 100/f.tempoDeCiclo
        
        for e in f.estacoes:
            mTE[e.trabalhadorId][e.idEstacao] += adicionado
        
        for t in e.tarefas:
            mT[e.idEstacao][t] += adicionado

def shift(formiga,grafo,grafoR,tempoTarefaTrabalhador):
    melhorou = False
    while True:
        movimentoRealizado = False
        mapaTarefa = {}
        maior = -1
        estacaoGargalo = None
        for e in formiga.estacoes: #Encontra a estacao de maior gargalo
            if e.carga > maior:
                maior = e.carga
                estacaoGargalo = e
            for t in e.tarefas: #Mapeia as tarefas em um dicionaria para checar a precedencia
                mapaTarefa[t] = e.idEstacao

        tarefasOrdenadas = sorted(estacaoGargalo.tarefas,key=lambda t :tempoTarefaTrabalhador[t][estacaoGargalo.trabalhadorId],reverse=True)
        for tarefa in tarefasOrdenadas:
            tempoNaOrigem = tempoTarefaTrabalhador[tarefa][estacaoGargalo.trabalhadorId]
            for eDestino in formiga.estacoes:
                if(eDestino.idEstacao == estacaoGargalo.idEstacao): #Pula quando e a propria estação gargalo
                    continue
                
                tempoNoDestino = tempoTarefaTrabalhador[tarefa][eDestino.trabalhadorId]
                if tempoNoDestino == math.inf: #Verifica se o trabalhador sabe fazer a tarefa
                    continue
                
                novaCargaDestomp = eDestino.carga + tempoNoDestino
                if novaCargaDestomp >= estacaoGargalo.carga: #Verifica se a mudança vai diminuir o tempo de ciclo
                    continue

                valido = True
                for filho in grafo[tarefa]: #Todos os sucessores da tarefa devem estar em estações >= a estação destino
                    estacaoFilho = mapaTarefa.get(filho)
                    if estacaoFilho < eDestino.idEstacao:
                        valido = False
                        break

                if not valido: continue

                for pai in grafoR[tarefa]: #Todos os predecessores da tarefa devem estar em estações <= a estação destino
                    estacaoPai = mapaTarefa.get(pai)
                    if estacaoPai > eDestino.idEstacao:
                        valido = False
                        break
                if not valido: continue

                formiga.removerTarefa(estacaoGargalo.idEstacao,tarefa,tempoNaOrigem)
                formiga.alocarTarefa(eDestino.idEstacao,tarefa,tempoNoDestino)
                movimentoRealizado = True
                melhorou = True
                break #Tenta mudar algo denovo agora na nova maior estação
        if not movimentoRealizado:
                break
    if melhorou:
        formiga.calcularTempoDeCiclo()

    return melhorou
        
def ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador,tarefasFatiadas,grafoR,orderStrenght,alpha_trab, beta_trab, alpha_tar, beta_tar,numeroFormigas=200,nIteracoesSemMelhoria=200,):
    feromonioInicial = 1/C_alvo
    feromoniosTE = [[feromonioInicial for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Trabalhador][Estacao]
    feromoniosTarefas = [[feromonioInicial for _ in range(NUMERO_TAREFAS)] for _ in range(NUMERO_TRABALHADORES_E_MAQUINAS)] #Matriz [Estacao][Tarefa]
    melhorGlobal = math.inf
    iteracoesSemMelhoria = 0
    formigas = [Formiga(i) for i in range(numeroFormigas)]
    melhorFormigaGlobal = None

    while((iteracoesSemMelhoria < nIteracoesSemMelhoria) and (melhorGlobal > lowerBound)):
        melhorFormigaLocal = None
        for f in formigas:
            f.resetar() #Reseta a formiga para a nova iteração
            alocaTrabalhadoresAEstacoes(f,tempoMedioDeCadaTrabalhador,feromoniosTE,tarefasFatiadas,tempoTarefaTrabalhador,alpha_trab, beta_trab,orderStrenght)
            alocaTarefas(f,feromoniosTarefas,C_alvo,precedencia,grafo,tempoTarefaTrabalhador,alpha_tar, beta_tar)
            #printaSolução(f)
            #Algoritmo de melhoria para a solução de cada formiga entra aqui
            shift(f,grafo,grafoR,tempoTarefaTrabalhador)
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
            #auditar_solucao(melhorFormigaGlobal, grafo, tempoTarefaTrabalhador, NUMERO_TAREFAS)
    return melhorGlobal

def exe(nomeArquivo):
   tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador, tarefasFatiadas = ler_e_converter_dados(nomeArquivo)
   return ACO(tempoTarefaTrabalhador,grafo,precedencia,lowerBound,C_alvo,tempoMedioDeCadaTrabalhador,tarefasFatiadas)

if __name__ == "__main__":
    nome_do_arquivo = 'instancias/geral/1_ton'
    dados = ler_e_converter_dados(nome_do_arquivo)

    if dados:
        tempoTarefaTrabalhador, grafo, precedencia, lowerBound, tempoMedio, tempoMedioDeCadaTrabalhador,tarefasFatiadas,grafoR,orderStrenght = dados
        print(f"Iniciando ACO isolado... LB={lowerBound}")
        alpha_trab = 1
        beta_trab = 2
        alpha_tarefa = 1
        beta_tarefa = 3
        res = ACO(tempoTarefaTrabalhador, grafo, precedencia, lowerBound, tempoMedio, tempoMedioDeCadaTrabalhador,tarefasFatiadas,grafoR,alpha_trab,beta_trab,alpha_tarefa,beta_tarefa,orderStrenght)
        print(f"Resultado Final: {res}")

