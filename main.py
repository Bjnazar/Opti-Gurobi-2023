from random import randint, seed
import math
import os
from gurobipy import GRB, Model, quicksum, GurobiError
import pandas as pd

seed(10)

# ------------ Construcción de los datos ------------

# Constantes
N_ELECTRICOS = 8
N_DIESEL = 8
N_DESTINOS = 10
N_ORIGENES = 10
N_DIAS = 5
bigM = 100**9


distancias1 = [28, 366, 644, 101, 392, 306, 356, 171, 360, 363]  # origen
distancias2 = [546, 205, 41, 559, 304, 244, 35, 80, 59, 197]  # destino
tpo_en_bloques1 = [1, 11, 19, 3, 12, 9, 11, 5, 11, 11]  # origen
tpo_en_bloques2 = [16, 6, 2, 16, 9, 7, 1, 3, 2, 6]  # destino

emisiones = [0.002064, 0.002114, 0.001994, 0.001961,0.002064, 0.002114, 0.001994, 0.001961,  0, 0 , 0 , 0 , 0, 0 , 0 , 0 ]
autonomias = [644, 483, 563, 523,644, 483, 563, 523,643, 150, 150, 250,643, 150, 150, 250]
precios = [19900000,158852500,277197590,84440000,19900000,158852500,277197590,84440000,118000000,95000000,90000000,138000000,118000000,95000000,90000000,138000000]
precios_km = [800,820,774,761,800,820,774,761,113,170,170,226,113,170,170,226]
capacidades = [120,119,202,63,120,119,202,63,106,129,120,183,106,129,120,183]
bloques_origenes = [1,11,19,3,12,9,11,5,11,11]
bloques_destinos = [16,6,2,16,9,7,1,3,2,6]



# Construcción de los conjuntos
Camiones = range(1, N_DIESEL + N_ELECTRICOS + 1)  # i in I
Destinos = range(1, N_DESTINOS + 1)  # d in D
Origenes = range(1, N_ORIGENES + 1)  # o in O
Dias = range(1, N_DIAS + 1)  # t in T
Bloques = range(1, 48 + 1)  # b in {1,...,48}
print("Conjuntos construidos")


# Construcción de los parametros
V = {i: 140 for i in Camiones}  # V_i

tmaxd = 10
Cq = 20000
Qmax = 10000
Ce = 5000
G = 47600000000  #Ajustar números


A = dict(zip(list(Camiones), autonomias))
E = dict(zip(list(Camiones), emisiones))
Ckm = dict(zip(list(Camiones), precios_km))
Cc = dict(zip(list(Camiones), precios))
Q = dict(zip(list(Camiones), capacidades))
Do = [28, 366, 644, 101, 392, 306, 356, 171, 360, 363]
Dd = [ 546, 205, 41, 559, 304, 244, 35, 80, 59, 197]
Md = {(1, 1): 53, (1, 2): 54, (1, 3): 78, (1, 4): 52, (1, 5): 59, (2, 1): 81, (2, 2): 76, (2, 3): 63, (2, 4): 80, (2, 5): 56, (3, 1): 54, (3, 2): 70, (3, 3): 53, (3, 4): 57, (3, 5): 77, (4, 1): 67, (4, 2): 81, (4, 3): 63, (4, 4): 88, (4, 5): 70, (5, 1): 58, (5, 2): 74, (5, 3): 70, (5, 4): 81, (5, 5): 60, (6, 1): 77, (6, 2): 79, (6, 3): 71, (6, 4): 72, (6, 5): 76, (7, 1): 53, (7, 2): 53, (7, 3): 67, (7, 4): 62, (7, 5): 79, (8, 1): 53, (8, 2): 71, (8, 3): 62, (8, 4): 64, (8, 5): 62, (9, 1): 85, (9, 2): 76, (9, 3): 90, (9, 4): 82, (9, 5): 63, (10, 1): 89, (10, 2): 74, (10, 3): 83, (10, 4): 74, (10, 5): 72}
R = {1: 48, 2: 57, 3: 81, 4: 33, 5: 111, 6: 102, 7: 100, 8: 29, 9: 105, 10: 106}  # el origen que está más cerca ofrece menos
Bo = {(i, o):tpo_en_bloques1[o - 1] for o in Origenes for i in Camiones}
Bd = {(i, d): tpo_en_bloques2[d - 1] for d in Destinos for i in Camiones}

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

model.addConstrs(
        (
            bigM * (1 - Y[i, b, t, o]) + A[i] >= Do[o - 1]  # ojo porque la posicion de la lista va desde el 0
            for i in Camiones
            for t in Dias
            for b in Bloques
            for o in Origenes
        ),
        name="R1a",
    )
model.addConstrs(
    (
        bigM * (1 - Z[i, b, t, d]) + A[i] >= Dd[d - 1]
        for i in Camiones
        for t in Dias
        for b in Bloques
        for d in Destinos
    ),
    name="R1b",
)
print("R1 agregada")

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
print("R2 agregada")

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
        for o in Origenes
        for b in Bloques[Bo[i, o] + 1:]
        for t in Dias

    ),
    name="R3c",
)
print("R3 agregada")

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
print("R4 agregada")

model.addConstrs((U[48, t - 1] == U[1, t] for t in Dias[1:]), name="R5a")
# No se realizan despachos de pedidos en el primer bloque
model.addConstrs(
    (Z[i, 1, t, d] == 0 for d in Destinos for i in Camiones for t in Dias),
    name="R5b",
)
print("R5 agregada")


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
print("R6 agregada")


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
print("R7 agregada")


r8_sum1 = lambda i, b, t: quicksum(
    Z[i, b, t, d] * Dd[d - 1] for d in Destinos  # for j in Pedidos
)
r8_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] * Do[o - 1] for o in Origenes)
r8_sum3 = lambda t, b: quicksum(
    beta[i] * Cc[i]
    + 2 * (Ckm[i] + E[i] * Ce) * (r8_sum1(i, b, t) + r8_sum2(i, b, t))
    for i in Camiones
)
model.addConstr(
    quicksum(U[b, t] * Cq + r8_sum3(t, b) for t in Dias for b in Bloques) <= G,
    name="R8",
)
print("R8 agregada")


model.addConstrs((U[b, t] <= Qmax for b in Bloques for t in Dias), name="R9")
print("R9 agregada")


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
print("R10 agregada")


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
        for t in Dias
        for d in Destinos
        for b in range(1,(48-2*Bd[i,d]))
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
        for t in Dias
        for d in Destinos
        for b in range(1,(48-2*Bo[i,o]))
    ),
    name="R11d",
)
print("R11 agregada")


model.addConstrs(
    (
        quicksum(alpha[i, b, t] for b in Bloques for t in Dias)
        <= bigM * beta[i]
        for i in Camiones
    ),
    name="R12",
)
print("R12 agregada")


model.addConstrs(
    (
        M[b, t, o]
        == R[o] + M[b - 1, t , o] - quicksum(W[i, b - 1, t, o] for i in Camiones)
        for b in Bloques[1:]  # b ∈{2,…,48}
        for o in Origenes
        for t in Dias
    ),
    name="R13",
)
print("R13 agregada")


model.addConstrs(
    (
        bigM * Y[i, b - Bo[i, o], t, o] >= W[i, b, t, o]
        for i in Camiones
        for o in Origenes
        for t in Dias
        for b in range(Bo[i, o] + 1, 48)
        # Propuesta: for b in Bloques[Bo[i, o] + 1, 48]
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

model.addConstrs(
    (
        bigM * alpha[i, b, t] >= W[i, b, t, o] 
        for i in Camiones 
        for t in Dias 
        for b in Bloques 
        for o in Origenes),
    name="Rj1"
    )

model.addConstrs(
    (
        bigM * alpha[i, b, t] >= X[i, b, t, d] 
        for i in Camiones 
        for t in Dias 
        for b in Bloques 
        for d in Destinos
        ),
    name="Rj2"
    )

"""model.addConstrs(
    (
        W[i, b2, t, o] <= bigM * (1 - Y[i, b1, t, o])
        for i in Camiones
        for t in Dias
        for o in Origenes
        for b1 in range(1, 48 - 2 * Bo[i, o])
        for b2 in range(b1, b1 + Bo[i, o])

    ),
    name="R14e"
)

model.addConstrs(
    (
        X[i, b2, t, d] <= bigM * (1 - Z[i, b1, t, d])
        for i in Camiones
        for t in Dias
        for d in Destinos
        for b1 in range(1, 48 - 2 * Bd[i, d])
        for b2 in range(b1, b1 + Bd[i, d])

    ),
    name="R14f"
)"""


print("R14 agregada")


model.addConstrs((M[1, 1, o] == R[o] for o in Origenes), name="R15")
print("R15 agregada")


model.addConstrs(
    (alpha[i, 1, t] == 0 for i in Camiones for t in Dias),
    name="R17a",
)
print("R17 agregada")


# ------------ Función objetivo ------------
fo_sum1 = lambda t, b, i: quicksum(
    Z[i, b, t, d] * Dd[d - 1] for d in Destinos  # for j in Pedidos
)
fo_sum2 = lambda t, b, i: quicksum(Y[i, b, t, o] * Do[o - 1] for o in Origenes)
objetivo = quicksum(
    2 * E[i] * (fo_sum1(t, b, i) + fo_sum2(t, b, i))
    for t in Dias
    for b in Bloques
    for i in Camiones
)
model.setObjective(objetivo, GRB.MINIMIZE)

print("Optimizando...")
model.optimize()

for i in range(model.SolCount):
    model.Params.SolutionNumber = i
    model.write(f"{i}.sol")

model.printAttr("X")

