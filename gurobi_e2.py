from gurobipy import GRB, Model, quicksum
from random import randint, seed
import math

seed(10)

# ------------ Construcción de los datos ------------

# Constantes
num_camiones_electricos = 10
num_camiones_diesel = 10
num_destinos = 10
num_origenes = 10
num_dias = 10
bigM = 10**6

# Construcción de los conjuntos
Camiones = range(num_camiones_diesel + num_camiones_electricos)  # i in I
Destinos = range(num_destinos)  # d in D
Origenes = range(num_origenes)  # o in O
Dias = range(num_dias)  # t in T
Bloques = range(48)  # b in {1,...,48}
Pedidos = lambda d: range(p[d])  # j in {1,...,pd}, no se si este bien, solo una idea

# Construcción de los parametros
V = {i: randint(10, 100) for i in Camiones}  # V_i
A = {i: randint(10, 100) for i in Camiones}  # A_i
E = {i: randint(10, 100) for i in Camiones}  # E_i
Ckm = {i: randint(10, 100) for i in Camiones}  # Ckm_i
Cc = {i: randint(10, 100) for i in Camiones}  # Cc_i
Q = {i: randint(10, 100) for i in Camiones}  # Q_i
Do = {o: randint(10, 100) for o in Origenes}  # Do_o
Dd = {d: randint(10, 100) for d in Destinos}  # Dd_d
Md = {(d, t): randint(10, 100) for d in Destinos for t in Dias}  # Md_dt
p = {d: randint(10, 100) for d in Destinos}  # p_d
tmaxd = randint(10, 100)
tmaxo = randint(10, 100)
Mo = {(o, t): randint(10, 100) for o in Origenes for t in Dias}  # Mo_ot
Cq = randint(10, 100)
Qmax = randint(10, 100)
Ce = randint(10, 100)
G = randint(10, 100)
R = {o: randint(10, 100) for o in Origenes}  # R_o

# ------------ Generar el modelo ------------
model = Model("Entrega 2 Proyecto")
model.setParam("TimeLimit", 60)

# ------------ Instanciar variables de decisión ------------
U = model.addVars(Bloques, Dias, vtype=GRB.INTEGER, name="U_bt")
X = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.INTEGER, name="X_ibtd")
W = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="W_ibto")
M = model.addVars(Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="M_bto")
Y = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.BINARY, name="Y_ibto")
# no se si este bien, solo una idea
variables_z = []
for d in Destinos:
    z = model.addVars(
        Camiones, Bloques, Dias, Pedidos(d), vtype=GRB.BINARY, name=f"Z_ibtj{d}"
    )
    variables_z.append(z)
Z = {
    (i, b, t, j, d): variables_z[d][i, b, t, j]
    for i in Camiones
    for b in Bloques
    for t in Dias
    for d in Destinos
    for j in Pedidos(d)
}
alpha = model.addVars(Camiones, Bloques, Dias, vtype=GRB.BINARY, name="alpha_ibt")
beta = model.addVars(Camiones, vtype=GRB.BINARY, name="beta_i")

model.update()

# ------------ Agregar restricciones ------------


def agregar_restricciones(ls_activas):
    # R1
    if 1 in ls_activas:
        b_p = lambda o, i: math.ceil(Do[o] / (2 * V[i]))
        model.addConstrs(
            (
                Y[i, b, t, o] == Y[i, b - b_p(o, i), t, o]
                for i in Camiones
                for o in Origenes
                for b in Bloques[b_p(o, i) :]
                for t in Dias
            ),
            name="R1a",
        )

        model.addConstrs(
            (b_p(o, i) <= 47 for i in Camiones for o in Origenes), name="R1b"
        )

    # R2
    if 2 in ls_activas:
        b_pp = lambda d, i: math.ceil(Dd[d] / (2 * V[i]))
        model.addConstrs(
            (
                Z[i, b, t, j, d] >= alpha[i, b - b_pp(d, i), t]
                for i in Camiones
                for d in Destinos
                for b in Bloques[b_pp(d, i) :]
                for t in Dias
                for j in Pedidos(d)
            ),
            name="R2a",
        )

        model.addConstrs(
            (b_pp(d, i) <= 47 for i in Camiones for d in Destinos), name="R2b"
        )

    # R3
    if 3 in ls_activas:
        r3a_sum1 = lambda b, t: quicksum(
            W[i, b, t, o] for o in Origenes for i in Camiones
        )
        r3a_sum2 = lambda t: quicksum(Md[d, t] for d in Destinos)
        model.addConstrs(
            (
                U[1, t + 1] == U[48, t] + r3a_sum1(b, t) - r3a_sum2(t)
                for b in Bloques
                for t in Dias[:-1]
            ),
            name="R3a",
        )

        r3b_sum1 = lambda b, t: quicksum(
            W[i, b, t, o] for o in Origenes for i in Camiones
        )
        r3b_sum2 = lambda b, t: quicksum(
            X[i, b, t, d] for d in Destinos for i in Camiones
        )
        model.addConstrs(
            (
                U[b + 1, t] == U[b, t] + r3b_sum1(b, t) - r3b_sum2(b, t)
                for b in Bloques[:-1]
                for t in Dias
            ),
            name="R3b",
        )

        r3c_sum1 = quicksum(W[i, 1, 1, o] for o in Origenes for i in Camiones)
        r3c_sum2 = quicksum(X[i, 1, 1, d] for d in Destinos for i in Camiones)
        model.addConstr(U[1, 1] == r3c_sum1 - r3c_sum2, name="R3c")

    # R4
    if 4 in ls_activas:
        model.addConstrs((U[48, t - 1] == U[1, t] for t in Dias[1:]), name="R4")

    # R5
    if 5 in ls_activas:
        r5_sum1 = lambda i, b, t: quicksum(
            Z[i, b, t, j, d] for d in Destinos for j in Pedidos(d)
        )
        r5_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] for o in Origenes)
        model.addConstrs(
            (
                alpha[i, b, t] + r5_sum1(i, b, t) + r5_sum2(i, b, t) <= 1
                for i in Camiones
                for b in Bloques
                for t in Dias
            ),
            name="R5",
        )

    # R6
    if 6 in ls_activas:
        # en el word sale para esta restricción que esta pendiente modificarla
        model.addConstrs(
            (
                quicksum(W[i, b, t, o] for i in Camiones for b in Bloques) <= Mo[o, t]
                for t in Dias
                for o in Origenes
            ),
            name="R6a",
        )

        # en esta restricción asumi que la variable x que
        #  aparece en el word es un error de tipeo de la variable Z
        model.addConstrs(
            (
                quicksum(Z[i, b, t, j, d] for i in Camiones) == Md[d, t]
                for t in Dias
                for b in Bloques
                for d in Destinos
                for j in Pedidos(d)
            ),
            name="R6b",
        )

    # R7
    if 7 in ls_activas:
        model.addConstrs(
            (
                Z[i, b, t, j, d] <= Q[i]
                for i in Camiones
                for t in Dias
                for b in Bloques
                for d in Destinos
                for j in Pedidos(d)
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
    if 8 in ls_activas:
        r8_sum1 = lambda i, b, t: quicksum(
            Z[i, b, t, j, d] * Dd[d] for d in Destinos for j in Pedidos(d)
        )
        r8_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
        r8_sum3 = lambda t, b: quicksum(
            beta[i] * Cc[i]
            + 2 * (Ckm[i] + E[i] * Ce) * r8_sum1(i, b, t)
            + r8_sum2(i, b, t)
            for i in Camiones
        )
        model.addConstr(
            quicksum(U[b, t] * Cq + r8_sum3(t, b) for t in Dias for b in Bloques) <= G,
            name="R8",
        )

    # R9
    if 9 in ls_activas:
        model.addConstrs((U[b, t] <= Qmax for b in Bloques for t in Dias), name="R9")

    # R10
    # esta restricción esta distinta en el word, pero segun yo al convertir la
    # sumatoria de destintos en un cuantificador afuera, no altera la restricción. Lo hice para facilitar el código.
    if 10 in ls_activas:
        model.addConstrs(
            (
                quicksum(
                    Z[i, b, t, j, d] for i in Camiones for b in Bloques for t in Dias
                )
                >= 1
                for d in Destinos
                for j in Pedidos(d)
            ),
            name="R10",
        )

    # R11
    if 11 in ls_activas:
        model.addConstrs(
            (
                Y[i, b, t, o] * (b + Do[o] * (V[i] ** -1)) <= tmaxo
                for i in Camiones
                for b in Bloques
                for t in Dias
                for o in Origenes
            ),
            name="R11a",
        )

        model.addConstrs(
            (
                Z[i, b, t, j, d] * (b + Dd[d] * (V[i] ** -1)) <= tmaxd
                for i in Camiones
                for b in Bloques
                for t in Dias
                for d in Destinos
                for j in Pedidos(d)
            ),
            name="R11b",
        )

    # R12
    # quedan pendientes R12c y R12d que no las entendí bien en el word, mas que nada el indice b
    if 12 in ls_activas:
        model.addConstrs(
            (
                (1 - Z[i, b, t, j, d]) >= alpha[i, b, t]
                for i in Camiones
                for b in Bloques
                for t in Dias
                for d in Destinos
                for j in Pedidos(d)
            ),
            name="R12a",
        )

        model.addConstrs(
            (
                (1 - Y[i, b, t, o]) >= alpha[i, b, t]
                for i in Camiones
                for b in Bloques
                for t in Dias
                for o in Origenes
            ),
            name="R12b",
        )

    # R13
    if 13 in ls_activas:
        model.addConstrs(
            (
                quicksum(alpha[i, b, t] for b in Bloques for t in Dias)
                <= bigM * beta[i]
                for i in Camiones
            ),
            name="R13",
        )

    # R14
    if 14 in ls_activas:
        model.addConstrs(
            (
                M[b, t, o]
                == R[o] + M[b, t - 1, o] - quicksum(W[i, b, t, o] for i in Camiones)
                for o in Origenes
                for b in Bloques
                for t in Dias[1:]
            ),
            name="R14",
        )

    # R15
    # Las restricciones de la naturaleza de las variables las establece gurobi
    #  al crear las variables y definir sus respectivos tipos de datos


# ------------ Función objetivo ------------
fo_sum1 = lambda t, b, i: quicksum(
    Z[i, b, t, j, d] * Dd[d] for d in Destinos for j in Pedidos(d)
)
fo_sum2 = lambda t, b, i: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
objetivo = quicksum(
    2 * E[i] * (fo_sum1(t, b, i) + fo_sum2(t, b, i))
    for t in Dias
    for b in Bloques
    for i in range(num_camiones_diesel)
)
model.setObjective(objetivo, GRB.MINIMIZE)

# ------------ Optimización del modelo ------------
model.optimize()

# ------------ Manejo de soluciones ------------
model.printAttr("X")
