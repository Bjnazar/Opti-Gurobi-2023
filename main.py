from random import randint, seed
import math
import os
from gurobipy import GRB, Model, quicksum, GurobiError
import pandas as pd

seed(10)

# ------------ Construcción de los datos ------------

# Constantes
N_ELECTRICOS = 20
N_DIESEL = 20
N_DESTINOS = 10
N_ORIGENES = 10
N_DIAS = 10
bigM = 100**9

distancias1 = [0, 28, 366, 644, 101, 392, 306, 356, 171, 360, 363]  # origen
distancias2 = [0, 546, 205, 41, 559, 304, 244, 35, 80, 59, 197]  # destino
tpo_en_bloques1 = [0, 1, 11, 19, 3, 12, 9, 11, 5, 11, 11]  # origen
tpo_en_bloques2 = [0, 16, 6, 2, 16, 9, 7, 1, 3, 2, 6]  # destino
emisiones = [0.002064, 0.002114, 0.001994, 0.001961]


# Construcción de los conjuntos
Camiones = range(1, N_DIESEL + N_ELECTRICOS + 1)  # i in I
Destinos = range(1, N_DESTINOS + 1)  # d in D
Origenes = range(1, N_ORIGENES + 1)  # o in O
Dias = range(1, N_DIAS + 1)  # t in T
Bloques = range(1, 48 + 1)  # b in {1,...,48}
print("Conjuntos construidos")

# Utils
ceil = lambda a: int(a + 1)  # int() trunca floats a la unidad

# Construcción de los parametros
V = {i: 140 for i in Camiones}  # V_i
A = {i: randint(300, 643) for i in Camiones}  # A_i
E = {i: randint(1, 5) for i in Camiones[: N_DIESEL + 1]}  # E_i
for i in range(
    N_DIESEL + 1, N_DIESEL + N_ELECTRICOS + 1
):
    E[i] = 0
Ckm = {i: randint(112, 225) for i in Camiones}  # Ckm_i
Cc = {i: randint(84440000, 277197590) for i in Camiones}  # Cc_i para los diesel


Q = {i: randint(106, 200) for i in Camiones}  # Q_i
Do = [0, 28, 366, 644, 101, 392, 306, 356, 171, 360, 363]  # Do_o
Dd = [0, 546, 205, 41, 559, 304, 244, 35, 80, 59, 197]  # Dd_d
Md = {(d, t): randint(50, 90) for d in Destinos for t in Dias}  # Md_dt
tmaxd = 10
# tmaxo = 10
Mo = {(o, t): randint(40, 60) for o in Origenes for t in Dias}  # Mo_ot
Cq = 20000
Qmax = 10000
Ce = 5000
G = 4760000000  #Ajustar números
R = {o: randint(50, 100) for o in Origenes}  # R_o
Bo = {(i, o): tpo_en_bloques1[o] for o in Origenes for i in Camiones}
Bd = {(i, d): tpo_en_bloques2[d] for d in Destinos for i in Camiones}
print("Parametros construidos")

# ------------ Generar el modelo ------------
model = Model("Entrega 2 Proyecto")
model.setParam("TimeLimit", 30 * 60)

# ------------ Instanciar variables de decisión ------------
U = model.addVars(Bloques, Dias, vtype=GRB.INTEGER, name="U_bt")
X = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.INTEGER, name="X_ibtd")
W = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="W_ibto")
M = model.addVars(Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="M_bto")
Y = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.BINARY, name="Y_ibto")
Z = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.BINARY, name="Z_ibtd")

alpha = model.addVars(Camiones, Bloques, Dias, vtype=GRB.BINARY, name="alpha_ibt")
beta = model.addVars(Camiones, vtype=GRB.BINARY, name="beta_i")

model.update()
print("Variables de decisión instanciadas")

# -------- Zona de prueba de restricciones ----------
# Editar esta lista para correr el modelo con distintas restricciones activas

ls_activas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]


if 1 in ls_activas:
    model.addConstrs(
        (
            bigM * (1 - Y[i, b, t, o]) + A[i] >= Do[o]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for o in Origenes
        ),
        name="R1a",
    )
    model.addConstrs(
        (
            bigM * (1 - Z[i, b, t, d]) + A[i] >= Dd[d]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for d in Destinos
        ),
        name="R1b",
    )

# R2
# Relación entre alpha (camión ocupado) con Z e Y (camión parte)
if 2 in ls_activas:
    Bloques_para_b0_bd = {}
    Bloques_para_b0_bo = {}
    for i in Camiones:
        for b1 in Bloques[:-2]:
            for d in Destinos:
                final = b1 + 2 * Bd[(i, d)]
                if final > 48:
                    Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1 + 1 :]
                else:  # No estoy seguro de estos indices
                    Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1 + 1 : final]
            for o in Origenes:
                final = b1 + 2 * Bo[(i, o)]
                if final > 48:
                    Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1 + 1 :]
                else:
                    Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1 + 1 : final]
    model.addConstrs(
        (
            alpha[i, b0, t] >= Z[i, b1, t, d]
            for i in Camiones
            for t in Dias
            for d in Destinos
            for b1 in Bloques[:-2]
            for b0 in Bloques_para_b0_bd[(b1, i, d)]
        ),
        name="R2a",
    )
    model.addConstrs(
        (
            alpha[i, b0, t] >= Y[i, b1, t, o]
            for i in Camiones
            for t in Dias
            for o in Origenes
            for b1 in Bloques[:-2]
            for b0 in Bloques_para_b0_bo[(b1, i, o)]
        ),
        name="R2b",
    )

# R3
# Cada camión que parte debe volver el mismo día
if 3 in ls_activas:
    model.addConstrs(
        (
            b + 2 * Bd[i, d] <= 48 + bigM * (1 - Z[i, b, t, d])
            for i in Camiones
            for d in Destinos
            for b in Bloques
            for t in Dias
        ),
        name="R3a",
    )
    model.addConstrs(
        (
            b + 2 * Bo[i, o] <= 48 + bigM * (1 - Y[i, b, t, o])
            for i in Camiones
            for b in Bloques
            for t in Dias
            for o in Origenes
        ),
        name="R3b",
    )
    model.addConstrs(
        (
            bigM * Y[i, b - Bo[i, o], t, o] >= W[i, b, t, o]
            for i in Camiones
            for b in Bloques[Bo[i, o] + 1:]
            for t in Dias
            for o in Origenes
        ),
        name="R3c",
    )

# R4
# Conservación de flujo inventario
if 4 in ls_activas:
    r4a_sum1 = lambda t: quicksum(
        W[i, b, t, o] for o in Origenes for i in Camiones for b in Bloques
    )
    r4a_sum2 = lambda t: quicksum(Md[d, t] for d in Destinos)
    model.addConstrs(
        (
            U[1, t + 1] == U[48, t] + r4a_sum1(t) - r4a_sum2(t)
            # for b in Bloques
            for t in Dias[:-1]
        ),
        name="R4a",
    )

    Camiones_r4b_bo = lambda b, o: [i for i in Camiones if b > Bo[(i, o)]]
    Camiones_r4b_bd = lambda b, d: [i for i in Camiones if b > Bd[(i, d)]]
    r4b_sum1 = lambda b, t: quicksum(
        W[i, b - Bo[(i, o)], t, o] for o in Origenes for i in Camiones_r4b_bo(b, o)
    )
    r4b_sum2 = lambda b, t: quicksum(
        X[i, b - Bd[(i, d)], t, d] for d in Destinos for i in Camiones_r4b_bd(b, d)
    )
    model.addConstrs(
        (
            U[b + 1, t] == U[b, t] + r4b_sum1(b, t) - r4b_sum2(b, t)
            for b in Bloques[:-1]
            for t in Dias
        ),
        name="R4b",
    )

    r4c_sum1 = quicksum(W[i, 1, 1, o] for o in Origenes for i in Camiones)
    r4c_sum2 = quicksum(X[i, 1, 1, d] for d in Destinos for i in Camiones)
    model.addConstr(U[1, 1] == r4c_sum1 - r4c_sum2, name="R4c")

# R5
# Conservación de inventario entre el último bloque de un día y
## el primer bloque del día siguiente
if 5 in ls_activas:
    model.addConstrs((U[48, t - 1] == U[1, t] for t in Dias[1:]), name="R5a")
    # No se realizan despachos de pedidos en el primer bloque
    model.addConstrs(
        (Z[i, 1, t, d] == 0 for d in Destinos for i in Camiones for t in Dias),
        name="R5b",
    )

# R6
# Cada camión puede estar asignado máximo en cada bloque de tiempo en un día
if 6 in ls_activas:
    r6_sum1 = lambda i, b, t: quicksum(
        Z[i, b, t, d] for d in Destinos  # for j in Pedidos
    )
    r6_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] for o in Origenes)
    model.addConstrs(
        (
            alpha[i, b, t] + r6_sum1(i, b, t) + r6_sum2(i, b, t) <= 1
            for i in Camiones
            for b in Bloques
            for t in Dias
        ),
        name="R6",
    )

# Ra7
# Eliminada por acuerdo de Mildred y Jorge (en base a ayudante) 31-05
# TODO: Renumerar el resto
# Las demandas de madera en los destinos deben satisfacerse
# if 7 in ls_activas:
#     model.addConstrs(
#         (
#             quicksum(X[i, b, t, d] for i in Camiones) <= Md[d, t]
#             for b in Bloques
#             for t in Dias
#             for d in Destinos
#         ),
#         name="R7",
#     )

# R7
# Cada camión puede cargar un máximo de madera
if 7 in ls_activas:
    model.addConstrs(
        (
            X[i, b, t, d] <= Q[i]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R7a",
    )
    model.addConstrs(
        (
            W[i, b, t, o] <= Q[i]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for o in Origenes
        ),
        name="R7b",
    )

# R8
# El costo total no debe pasarse del máximo
if 8 in ls_activas:
    r8_sum1 = lambda i, b, t: quicksum(
        Z[i, b, t, d] * Dd[d] for d in Destinos  # for j in Pedidos
    )
    r8_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
    r8_sum3 = lambda t, b: quicksum(
        beta[i] * Cc[i]
        + 2 * (Ckm[i] + E[i] * Ce) * (r8_sum1(i, b, t) + r8_sum2(i, b, t))
        for i in Camiones
    )
    model.addConstr(
        quicksum(U[b, t] * Cq + r8_sum3(t, b) for t in Dias for b in Bloques) <= G,
        name="R8",
    )

# R9
# Los almacenes de madera de la casa matriz tienen una capacidad máxima
if 9 in ls_activas:
    model.addConstrs((U[b, t] <= Qmax for b in Bloques for t in Dias), name="R9")

# R10
# Los pedidos deben llegar a tiempo
if 10 in ls_activas:
    # TODO: reactivar
    # model.addConstrs(
    #     (
    #         Y[i, b, t, o] * (b + Bo[i,o]) <= tmaxo
    #         for i in Camiones
    #         for b in Bloques
    #         for t in Dias
    #         for o in Origenes
    #     ),
    #     name="R10a",
    # )

    model.addConstrs(
        (
            Z[i, b, t, d] * (b + Bd[i, d]) <= tmaxd
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R10b",
    )

# R11
# Relación de las variables con alfa
# TODO: Revisar bien los limites de las sumatorias en 11c y 11d
if 11 in ls_activas:
    model.addConstrs(
        (
            (1 - Z[i, b, t, d]) >= alpha[i, b, t]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R11a",
    )

    model.addConstrs(
        (
            (1 - Y[i, b, t, o]) >= alpha[i, b, t]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for o in Origenes
        ),
        name="R11b",
    )

    sumc = lambda i, b, t: quicksum(
        alpha[i, b1, t] for b1 in Bloques[b : b + 2 * Bd[i, d]]
    )
    model.addConstrs(
        (
            2 * Bd[i, d] * Z[i, b, t, d] <= sumc(i, b, t)
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R11c",
    )

    sumd = lambda i, b, t: quicksum(
        alpha[i, b1, t] for b1 in Bloques[b : b + 2 * Bd[i, d]]
    )
    model.addConstrs(
        (
            2 * Bo[i, o] * Z[i, b, t, o] <= sumd(i, b, t)
            for i in Camiones
            for b in Bloques
            for t in Dias
            for o in Origenes
        ),
        name="R11d",
    )

# R12
# Relación entre alfa y beta
if 12 in ls_activas:
    model.addConstrs(
        (
            quicksum(alpha[i, b, t] for b in Bloques for t in Dias)
            <= bigM * beta[i]
            for i in Camiones
        ),
        name="R12",
    )

# R13
# Flujo de producción
if 13 in ls_activas:
    model.addConstrs(
        (
            M[b, t, o]
            == R[o] + M[b, t - 1, o] - quicksum(W[i, b, t, o] for i in Camiones)
            for b in Bloques
            for o in Origenes
            for t in Dias[1:]
        ),
        name="R13",
    )

# R14
# Relación carga con inicio del viaje
if 14 in ls_activas:
    model.addConstrs(
        (
            bigM * Y[i, b - Bo[i, o], t, o] >= W[i, b, t, o]
            for i in Camiones
            for o in Origenes
            for t in Dias
            for b in range(Bo[i, o] + 1, 48)
        ),
        name="R14a",
    )

    model.addConstrs(
        (
            Y[i, b - Bo[i, o], t, o] <= W[i, b, t, o]
            for i in Camiones
            for o in Origenes
            for t in Dias
            for b in range(Bo[i, o] + 1, 48)
        ),
        name="R14b",
    )

    model.addConstrs(
        (
            bigM * Z[i, b - Bd[i, d], t, d] >= X[i, b, t, d]
            for i in Camiones
            for d in Destinos
            for t in Dias
            for b in range(Bd[i, d] + 1, 48)
        ),
        name="R14c",
    )

    model.addConstrs(
        (
            Z[i, b - Bd[i, d], t, d] <= X[i, b, t, d]
            for i in Camiones
            for d in Destinos
            for t in Dias
            for b in range(Bd[i, d] + 1, 48)
        ),
        name="R14d",
    )

# R15
# La cantidad de madera ofrecida por cada origen en el primer bloque de cada dia es su tasa de producción diaria
if 15 in ls_activas:
    model.addConstrs((M[0, 0, o] == R[o] for o in Origenes), name="R15")

# R16
# Los camiones eléctricos no emiten CO2
if 16 in ls_activas:
    model.addConstrs(
        (E[i] == 0 for i in Camiones[N_ELECTRICOS:]), name="R16"
    )

# R17
# Los camiones parten desocupados el primer bloque de cada dia
if 17 in ls_activas:
    model.addConstrs(
        (alpha[i, 0, t] == 0 for i in Camiones for t in Dias),
        name="R17a",
    )


# ------------ Función objetivo ------------
fo_sum1 = lambda t, b, i: quicksum(
    Z[i, b, t, d] * Dd[d] for d in Destinos  # for j in Pedidos
)
fo_sum2 = lambda t, b, i: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
objetivo = quicksum(
    2 * E[i] * (fo_sum1(t, b, i) + fo_sum2(t, b, i))
    for t in Dias
    for b in Bloques
    for i in Camiones
)
model.setObjective(objetivo, GRB.MINIMIZE)

# ------------ Optimización del modelo ------------

# Descomentar si es que el modelo es feasible
# model.computeIIS()
# model.write("model.ilp")

print("Optimizando...")
model.optimize()
# ------------ Manejo de soluciones ------------
if model.status == GRB.OPTIMAL:
    model.printAttr("X")
    print("Betas:")
    for i in Camiones:
        print(beta[i])
    print("Alfas:")
    for t in Dias:
        for i in Camiones:
            for b in Bloques:
                print(alpha[i, b, t])
else:
    print("Trata de nuevoo!")




#  DEJÉ LA FUNCIÓN COMO ESTABA, PARA PROBAR SI ES LA FUNCIÓN LA QUE TIENE PROBLEMA CON GUROBI
#  AL AGREGAR LAS RESTRICCIONES
# # ------------ Función agregar restricciones ------------
# def agregar_restricciones(ls_activas):
#     # R1
#     # Autonomía (distancia max de cada recorrido)
#     if 1 in ls_activas:
#         model.addConstrs(
#             (
#                 bigM * (1 - Y[i, b, t, o]) + A[i] >= Do[o]
#                 for i in Camiones
#                 for t in Dias
#                 for b in Bloques
#                 for o in Origenes
#             ),
#             name="R1a",
#         )
#         model.addConstrs(
#             (
#                 bigM * (1 - Z[i, b, t, d]) + A[i] >= Dd[d]
#                 for i in Camiones
#                 for t in Dias
#                 for b in Bloques
#                 for d in Destinos
#             ),
#             name="R1b",
#         )

#     # R2
#     # Relación entre alpha (camión ocupado) con Z e Y (camión parte)
#     if 2 in ls_activas:
#         Bloques_para_b0_bd = {}
#         Bloques_para_b0_bo = {}
#         for i in Camiones:
#             for b1 in Bloques[:-2]:
#                 for d in Destinos:
#                     final = b1 + 2 * Bd[(i, d)]
#                     if final > 48:
#                         Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1 + 1 :]
#                     else:  # No estoy seguro de estos indices
#                         Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1 + 1 : final]
#                 for o in Origenes:
#                     final = b1 + 2 * Bo[(i, o)]
#                     if final > 48:
#                         Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1 + 1 :]
#                     else:
#                         Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1 + 1 : final]
#         model.addConstrs(
#             (
#                 alpha[i, b0, t] >= Z[i, b1, t, d]
#                 for i in Camiones
#                 for t in Dias
#                 for d in Destinos
#                 for b1 in Bloques[:-2]
#                 for b0 in Bloques_para_b0_bd[(b1, i, d)]
#             ),
#             name="R2a",
#         )
#         model.addConstrs(
#             (
#                 alpha[i, b0, t] >= Y[i, b1, t, o]
#                 for i in Camiones
#                 for t in Dias
#                 for o in Origenes
#                 for b1 in Bloques[:-2]
#                 for b0 in Bloques_para_b0_bo[(b1, i, o)]
#             ),
#             name="R2b",
#         )

#     # R3
#     # Cada camión que parte debe volver el mismo día
#     if 3 in ls_activas:
#         model.addConstrs(
#             (
#                 b + 2 * Bd[i, d] <= 48 + bigM * (1 - Z[i, b, t, d])
#                 for i in Camiones
#                 for d in Destinos
#                 for b in Bloques
#                 for t in Dias
#             ),
#             name="R3a",
#         )
#         model.addConstrs(
#             (
#                 b + 2 * Bo[i, o] <= 48 + bigM * (1 - Y[i, b, t, o])
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for o in Origenes
#             ),
#             name="R3b",
#         )

#     # R4
#     # Conservación de flujo inventario
#     if 4 in ls_activas:
#         r4a_sum1 = lambda t: quicksum(
#             W[i, b, t, o] for o in Origenes for i in Camiones for b in Bloques
#         )
#         r4a_sum2 = lambda t: quicksum(Md[d, t] for d in Destinos)
#         model.addConstrs(
#             (
#                 U[1, t + 1] == U[48, t] + r4a_sum1(t) - r4a_sum2(t)
#                 # for b in Bloques
#                 for t in Dias[:-1]
#             ),
#             name="R4a",
#         )

#         Camiones_r4b_bo = lambda b, o: [i for i in Camiones if b > Bo[(i, o)]]
#         Camiones_r4b_bd = lambda b, d: [i for i in Camiones if b > Bd[(i, d)]]
#         r4b_sum1 = lambda b, t: quicksum(
#             W[i, b - Bo[(i, o)], t, o] for o in Origenes for i in Camiones_r4b_bo(b, o)
#         )
#         r4b_sum2 = lambda b, t: quicksum(
#             X[i, b - Bd[(i, d)], t, d] for d in Destinos for i in Camiones_r4b_bd(b, d)
#         )
#         model.addConstrs(
#             (
#                 U[b + 1, t] == U[b, t] + r4b_sum1(b, t) - r4b_sum2(b, t)
#                 for b in Bloques[:-1]
#                 for t in Dias
#             ),
#             name="R4b",
#         )

#         r4c_sum1 = quicksum(W[i, 1, 1, o] for o in Origenes for i in Camiones)
#         r4c_sum2 = quicksum(X[i, 1, 1, d] for d in Destinos for i in Camiones)
#         model.addConstr(U[1, 1] == r4c_sum1 - r4c_sum2, name="R4c")

#     # R5
#     # Conservación de inventario entre el último bloque de un día y
#     ## el primer bloque del día siguiente
#     if 5 in ls_activas:
#         model.addConstrs((U[48, t - 1] == U[1, t] for t in Dias[1:]), name="R5a")
#         # No se realizan despachos de pedidos en el primer bloque
#         model.addConstrs(
#             (Z[i, 1, t, d] == 0 for d in Destinos for i in Camiones for t in Dias),
#             name="R5b",
#         )

#     # R6
#     # Cada camión puede estar asignado máximo en cada bloque de tiempo en un día
#     if 6 in ls_activas:
#         r6_sum1 = lambda i, b, t: quicksum(
#             Z[i, b, t, d] for d in Destinos  # for j in Pedidos
#         )
#         r6_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] for o in Origenes)
#         model.addConstrs(
#             (
#                 alpha[i, b, t] + r6_sum1(i, b, t) + r6_sum2(i, b, t) <= 1
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#             ),
#             name="R6",
#         )

#     # Ra7
#     # Eliminada por acuerdo de Mildred y Jorge (en base a ayudante) 31-05
#     # TODO: Renumerar el resto
#     # Las demandas de madera en los destinos deben satisfacerse
#     # if 7 in ls_activas:
#     #     model.addConstrs(
#     #         (
#     #             quicksum(X[i, b, t, d] for i in Camiones) <= Md[d, t]
#     #             for b in Bloques
#     #             for t in Dias
#     #             for d in Destinos
#     #         ),
#     #         name="R7",
#     #     )

#     # R7
#     # Cada camión puede cargar un máximo de madera
#     if 7 in ls_activas:
#         model.addConstrs(
#             (
#                 X[i, b, t, d] <= Q[i]
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for d in Destinos
#             ),
#             name="R7a",
#         )
#         model.addConstrs(
#             (
#                 W[i, b, t, o] <= Q[i]
#                 for i in Camiones
#                 for t in Dias
#                 for b in Bloques
#                 for o in Origenes
#             ),
#             name="R7b",
#         )

#     # R8
#     # El costo total no debe pasarse del máximo
#     if 8 in ls_activas:
#         r8_sum1 = lambda i, b, t: quicksum(
#             Z[i, b, t, d] * Dd[d] for d in Destinos  # for j in Pedidos
#         )
#         r8_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
#         r8_sum3 = lambda t, b: quicksum(
#             beta[i] * Cc[i]
#             + 2 * (Ckm[i] + E[i] * Ce) * (r8_sum1(i, b, t) + r8_sum2(i, b, t))
#             for i in Camiones
#         )
#         model.addConstr(
#             quicksum(U[b, t] * Cq + r8_sum3(t, b) for t in Dias for b in Bloques) <= G,
#             name="R8",
#         )

#     # R9
#     # Los almacenes de madera de la casa matriz tienen una capacidad máxima
#     if 9 in ls_activas:
#         model.addConstrs((U[b, t] <= Qmax for b in Bloques for t in Dias), name="R9")

#     # R10
#     # Los pedidos deben llegar a tiempo
#     if 10 in ls_activas:
#         # TODO: reactivar
#         # model.addConstrs(
#         #     (
#         #         Y[i, b, t, o] * (b + Bo[i,o]) <= tmaxo
#         #         for i in Camiones
#         #         for b in Bloques
#         #         for t in Dias
#         #         for o in Origenes
#         #     ),
#         #     name="R10a",
#         # )

#         model.addConstrs(
#             (
#                 Z[i, b, t, d] * (b + Bd[i, d]) <= tmaxd
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for d in Destinos
#             ),
#             name="R10b",
#         )

#     # R11
#     # Relación de las variables con alfa
#     # TODO: Revisar bien los limites de las sumatorias en 11c y 11d
#     if 11 in ls_activas:
#         model.addConstrs(
#             (
#                 (1 - Z[i, b, t, d]) >= alpha[i, b, t]
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for d in Destinos
#             ),
#             name="R11a",
#         )

#         model.addConstrs(
#             (
#                 (1 - Y[i, b, t, o]) >= alpha[i, b, t]
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for o in Origenes
#             ),
#             name="R11b",
#         )

#         sumc = lambda i, b, t: quicksum(
#             alpha[i, b1, t] for b1 in Bloques[b : b + 2 * Bd[i, d]]
#         )
#         model.addConstrs(
#             (
#                 2 * Bd[i, d] * Z[i, b, t, d] <= sumc(i, b, t)
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for d in Destinos
#             ),
#             name="R11c",
#         )

#         sumd = lambda i, b, t: quicksum(
#             alpha[i, b1, t] for b1 in Bloques[b : b + 2 * Bd[i, d]]
#         )
#         model.addConstrs(
#             (
#                 2 * Bo[i, o] * Z[i, b, t, o] <= sumd(i, b, t)
#                 for i in Camiones
#                 for b in Bloques
#                 for t in Dias
#                 for o in Origenes
#             ),
#             name="R11d",
#         )

#     # R12
#     # Relación entre alfa y beta
#     if 12 in ls_activas:
#         model.addConstrs(
#             (
#                 quicksum(alpha[i, b, t] for b in Bloques for t in Dias)
#                 <= bigM * beta[i]
#                 for i in Camiones
#             ),
#             name="R12",
#         )

#     # R13
#     # Flujo de producción
#     if 13 in ls_activas:
#         model.addConstrs(
#             (
#                 M[b, t, o]
#                 == R[o] + M[b, t - 1, o] - quicksum(W[i, b, t, o] for i in Camiones)
#                 for b in Bloques
#                 for o in Origenes
#                 for t in Dias[1:]
#             ),
#             name="R13",
#         )

#     # R14
#     # Relación carga con inicio del viaje
#     if 14 in ls_activas:
#         model.addConstrs(
#             (
#                 bigM * Y[i, b - Bo[i, o], t, o] >= W[i, b, t, o]
#                 for i in Camiones
#                 for o in Origenes
#                 for t in Dias
#                 for b in range(Bo[i, o] + 1, 48)
#             ),
#             name="R14a",
#         )

#         model.addConstrs(
#             (
#                 Y[i, b - Bo[i, o], t, o] <= W[i, b, t, o]
#                 for i in Camiones
#                 for o in Origenes
#                 for t in Dias
#                 for b in range(Bo[i, o] + 1, 48)
#             ),
#             name="R14b",
#         )

#         model.addConstrs(
#             (
#                 bigM * Z[i, b - Bd[i, d], t, d] >= X[i, b, t, d]
#                 for i in Camiones
#                 for d in Destinos
#                 for t in Dias
#                 for b in range(Bd[i, d] + 1, 48)
#             ),
#             name="R14c",
#         )

#         model.addConstrs(
#             (
#                 Z[i, b - Bd[i, d], t, d] <= X[i, b, t, d]
#                 for i in Camiones
#                 for d in Destinos
#                 for t in Dias
#                 for b in range(Bd[i, d] + 1, 48)
#             ),
#             name="R14d",
#         )

#     # R15
#     # La cantidad de madera ofrecida por cada origen en el primer bloque de cada dia es su tasa de producción diaria
#     if 15 in ls_activas:
#         model.addConstrs((M[0, 0, o] == R[o] for o in Origenes), name="R15")

#     # R16
#     # Los camiones eléctricos no emiten CO2
#     if 16 in ls_activas:
#         model.addConstrs(
#             (E[i] == 0 for i in Camiones[N_ELECTRICOS:]), name="R16"
#         )

#     # R17
#     # Los camiones parten desocupados el primer bloque de cada dia
#     if 17 in ls_activas:
#         model.addConstrs(
#             (alpha[i, 0, t] == 0 for i in Camiones for t in Dias),
#             name="R17a",
#         )


# def probar_restricciones(r_idx_inicial, r_idx_final):
#     """
#     Esta es para probar si las restricciones tiran error o no.
#     Afortunadamente, ya hemos pasado esa etapa.
#     """
#     print("Probando restricciones...")
#     for ls_una_r in [[idx] for idx in range(r_idx_inicial, r_idx_final + 1)]:
#         try:
#             agregar_restricciones(ls_una_r)
#             print(f"R{ls_una_r[0]} OK")
#         except GurobiError as err:  # Gracias Berni
#             print("Error code " + str(err.errno) + ": " + str(err))
#         except (
#             KeyboardInterrupt
#         ):  # Si no funciona, apretar varias veces Ctrl + C bien seguido
#             os._exit()
#         finally:
#             continue


# # -------- Zona de prueba de restricciones ----------
# # Editar esta lista para correr el modelo con distintas restricciones activas

# ls_activas = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
# agregar_restricciones(ls_activas)
