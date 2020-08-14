from __future__ import print_function
from ortools.linear_solver import pywraplp

import sys
import numpy as np


'''
ordem importa de leitura importa na indexação de periodo e tipo de usinas
para o solver nos retorna o que a espec determina

'''


def readFile(nameFile):
    with open(nameFile, 'r') as file:

        qPeriodo = int(next(file))
        periodos = []
        demanda = []

        qUsinas = 0
        usinas = []

        for x in range(qPeriodo):
            data = [int(i) for i in file.readline().split()]
            periodos.append(data[0])
            demanda.append(data[1])

        qUsinas = int(next(file))

        for x in range(qUsinas):
            usinaAux = [int(i) for i in file.readline().split()]
            usinas.append({'numDisp': usinaAux[0], 'prodMin': usinaAux[1], 'prodMax': usinaAux[2],
                           'custoMin': usinaAux[3], 'custoAdc': usinaAux[4], 'custoLig': usinaAux[5]})

    return {'qPeriodo': qPeriodo, 'periodos': periodos, 'demanda': demanda, 'qUsinas': qUsinas, 'usinas': usinas}


# print(readFile("usinas.txt"))

data = readFile(sys.argv[1])

solver = pywraplp.Solver.CreateSolver('simple_mip_program', 'CBC')

# variaveis de decisão
x = [[[solver.IntVar(0, 1, 'x[%i][%i][%i]' % (i, z, j)) for j in range(data['qPeriodo'])]
      for z in range(data['usinas'][i]['numDisp'])] for i in range(data['qUsinas'])]

p = [[[solver.IntVar(0, solver.infinity(), 'p[%i][%i][%i]' % (i, z, j)) for j in range(data['qPeriodo'])]
      for z in range(data['usinas'][i]['numDisp'])] for i in range(data['qUsinas'])]

e = [[[solver.IntVar(0, solver.infinity(), 'e[%i][%i][%i]' % (i, z, j)) for j in range(data['qPeriodo'])]
      for z in range(data['usinas'][i]['numDisp'])] for i in range(data['qUsinas'])]

o = [[[solver.IntVar(0, 1, 'o[%i][%i][%i]' % (i, z, j)) for j in range(data['qPeriodo'])]
      for z in range(data['usinas'][i]['numDisp'])] for i in range(data['qUsinas'])]


# variaveis de restrições
for i in range(data['qUsinas']):
    for j in range(data['usinas'][i]['numDisp']):
        for z in range(data['qPeriodo']):
            restricao_6 = solver.Add(
                e[i][j][z] >= p[i][j][z] - data['usinas'][i]['prodMin'])

for i in range(data['qUsinas']):
    for j in range(data['usinas'][i]['numDisp']):
        for z in range(data['qPeriodo']):
            restricao_4 = solver.Add(
                p[i][j][z] <= data['usinas'][i]['prodMax'])

for i in range(data['qUsinas']):
    for j in range(data['usinas'][i]['numDisp']):
        for z in range(data['qPeriodo']):
            restricao_3 = solver.Add(
                data['demanda'][z] * x[i][j][z] >= p[i][j][z])

for i in range(data['qUsinas']):
    for j in range(data['usinas'][i]['numDisp']):
        for z in range(1, data['qPeriodo']):
            restricao_5 = solver.Add(o[i][j][z] >= x[i][j][z] - x[i][j][z-1])
restricao_5 = solver.Add(o[i][j][0] >= x[i][j][0] -
                         x[i][j][data['qPeriodo']-1])

for z in range(data['qPeriodo']):
    restricao_2 = solver.Constraint(data['demanda'][z], data['demanda'][z])
    for i in range(data['qUsinas']):
        for j in range(data['usinas'][i]['numDisp']):
            restricao_2.SetCoefficient(p[i][j][z], 1)

# funcao objetivo
objetivo = solver.Objective()
for i in range(data['qUsinas']):
    for j in range(data['usinas'][i]['numDisp']):
        for z in range(data['qPeriodo']):
            coeficienteX = data['usinas'][i]['custoMin'] * data['periodos'][z]
            if(z == 0):
                coeficienteX += data['usinas'][i]['custoLig']
            objetivo.SetCoefficient(
                x[i][j][z], coeficienteX)
            objetivo.SetCoefficient(
                e[i][j][z], data['usinas'][i]['custoAdc'] * data['periodos'][z])
            objetivo.SetCoefficient(o[i][j][z], data['usinas'][i]['custoLig'])


objetivo.SetMinimization()
status = solver.Solve()


# qual o custo total diário.
if status == pywraplp.Solver.OPTIMAL:
    print('Solution:')
    print('Objective value =', solver.Objective().Value(), "\n")

# quantas unidades de cada tipo vão estar ligadas em cada período

    print('Unidades de Usinas ligadas em cada periodo\n')
    for z in range(data['qPeriodo']):
        print('Periodo: %i\n' % z)
        for i in range(data['qUsinas']):
            count = 0
            for j in range(data['usinas'][i]['numDisp']):
                if(x[i][j][z].solution_value() == 0):
                    continue
                count += x[i][j][z].solution_value()
            print("Usinas Tipo %i: %i" % (i+1, count))

        print('\n')

    # quanto cada uma das unidades ligadas deve produzir em cada período
    print('Produção de uma unidade por periodo\n')
    for z in range(data['qPeriodo']):
        print('Periodo: %i\n' % z)
        for i in range(data['qUsinas']):
            print('Usinas Do Tipo %i' % (i+1))
            for j in range(data['usinas'][i]['numDisp']):
                if(x[i][j][z].solution_value() == 0):
                    continue
                prodPeriodo = p[i][j][z].solution_value()
                print('Unidade: %i' % (j+1), 'Produziu:',
                p[i][j][z].solution_value())
            print('\n')
    
    # quais são os custos por tipo de usina (separado por custo fixo, custo adicional e custo de ligação)
    print('Custos por tipo de Usina\n')
    for i in range(data['qUsinas']):
        print('Usinas Do Tipo %i' % (i+1))
        custo_min = 0
        custo_lig = 0
        custo_adc = 0
        for j in range(data['usinas'][i]['numDisp']):
            for z in range(data['qPeriodo']):
                if(x[i][j][z].solution_value() == 0):
                    continue
                custo_min += x[i][j][z].solution_value() * data['usinas'][i]['custoMin'] * data['periodos'][z]
                custo_adc += e[i][j][z].solution_value() * data['usinas'][i]['custoAdc'] * data['periodos'][z]
                custo_lig += o[i][j][z].solution_value() * data['usinas'][i]['custoLig'] 
            custo_lig += (x[i][j][0].solution_value() * data['usinas'][i]['custoLig'])
        print('Custo Minimo: ', custo_min)
        print('Custo Adicional: ', custo_adc)
        print('Custo Ligação: ',  custo_lig, "\n")

    # print('\n')
    # print('Custo Adicional Por Tipo de Usina')

    # for z in range(data['qPeriodo']):
    #     for i in range(data['qUsinas']):
    #         print('Usinas Do Tipo %i' % (i+1))
    #         custo_adc = 0
    #         for j in range(data['usinas'][i]['numDisp']):
    #             if(x[i][j][z].solution_value() == 0):
    #                 continue
    #             custo_adc += e[i][j][z].solution_value() * data['usinas'][i]['custoAdc'] * data['periodos'][z]
    #         print('Custo Adicional: ', custo_adc)

    # print('\n')
    # print('Custo de Ligação Por Tipo de Usina')

    # for z in range(data['qPeriodo']):
    #     for i in range(data['qUsinas']):
    #         print('Usinas Do Tipo %i' % (i+1))
    #         custo_lig = 0
    #         for j in range(data['usinas'][i]['numDisp']):
    #             if(x[i][j][z].solution_value() == 0):
    #                 continue
    #             custo_lig += o[i][j][z].solution_value() * data['usinas'][i]['custoLig'] + (x[i][j][0].solution_value() * data['usinas'][i]['custoLig'])
    #         print('Custo Ligação: ',  custo_lig)

else:
    print('The problem does not have an optimal solution.')

print('\nAdvanced usage:')
print('Problem solved in %f milliseconds' % solver.wall_time())
print('Problem solved in %d iterations' % solver.iterations())

file = open('PFM.lp', 'w')
file.write(solver.ExportModelAsLpFormat(False))
file.close()
