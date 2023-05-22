from gurobipy import GRB, Model, quicksum, GurobiError
from random import randint, seed

seed(10)

# ------------ Construcción de los datos ------------

# Constantes
num_camiones_electricos = 4
num_camiones_diesel = 4
num_destinos = 3
num_origenes = 3
num_dias = 10
J = 5
bigM = 100000

# Utils
ceil = lambda a: int(a + 1)  # int() trunca floats a la unidad

# Construcción de los conjuntos
Camiones = range(num_camiones_diesel + num_camiones_electricos) # i in I
Destinos = range(num_destinos) # d in D
Origenes = range(num_origenes) # o in O
Dias = range(num_dias) # t in T
Bloques = range(48) # b in {1,...,48}


# Construcción de los parametros
V = {i: 70 for i in Camiones}  # V_i
A = {i: randint(150, 643) for i in Camiones}  # A_i
E = {i: randint(1, 5) for i in Camiones[: num_camiones_diesel + 1]}  # E_i
for i in range(
    num_camiones_diesel + 1, num_camiones_diesel + num_camiones_electricos + 1):
    E[i] = 0
Ckm = {i: randint(112, 225) for i in Camiones}  # Ckm_i
Cc = {i: randint(84440000, 277197590) for i in Camiones}  # Cc_i para los diesel

Q = {i: randint(106, 200) for i in Camiones}  # Q_i
Do = {o: randint(27, 643) for o in Origenes}  # Do_o
Dd = {d: randint(27, 643) for d in Destinos}  # Dd_d
Md = {(d, t): randint(50, 500) for d in Destinos for t in Dias}  # Md_dt
tmaxd = 7   # TODO: Este no era distinto por cada destino? No sé, alguien más revise porfa. Milan.
tmaxo = 10   # TODO: Este no era distinto por cada origen? No sé, alguien más revise porfa. Milan.
Mo = {(o, t): randint(10, 100) for o in Origenes for t in Dias}  # Mo_ot
Cq = 20000
Qmax = 10000
Ce = 5000
G = 5750000000000
R = {o: randint(10, 100) for o in Origenes}  # R_o
Bo = {(i, o): ceil(Do[o] / V[i]) for i in Camiones for o in Origenes}
Bd = {(i, d): ceil(Dd[d] / V[i]) for i in Camiones for d in Destinos}
print("Parametros construidos")

# ------------ Generar el modelo ------------
try:
    model = Model("Entrega 2 Proyecto")
    model.setParam("TimeLimit", 60)

    # ------------ Instanciar variables de decisión ------------
    # U = model.addVars(Bloques, Dias, vtype=GRB.INTEGER, name="U_bt")
    X = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.INTEGER, name="X_ibtd")
    W = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="W_ibto")
    M = model.addVars(Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="M_bto")
    Y = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.BINARY, name="Y_ibto")
    Z = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.BINARY, name="Z_ibtd") 
    alpha = model.addVars(Camiones, Bloques, Dias, vtype=GRB.BINARY, name="alpha_ibt")
    beta = model.addVars(Camiones, vtype=GRB.BINARY, name="beta_i")


    model.update()

    # ------------ Agregar restricciones ------------
    model.addConstrs(
        (
            bigM * (1 - Y[i, b, t, o]) + A[i] >= 2 * Do[o]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for o in Origenes
        ),
        name="R1a",
    )

    model.addConstrs(
        (
            bigM * (1 - Z[i, b, t, d]) + A[i] >= 2 * Dd[d]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for d in Destinos
        ),
        name="R1b",
    )

    Bloques_para_b0_bd = {}
    Bloques_para_b0_bo = {}
    for i in Camiones:
        for b1 in Bloques[:-2]:
            for d in Destinos:
                final = b1 + 2 * Bd[(i, d)]
                if final > 48:
                    Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1:]
                else:
                    Bloques_para_b0_bd[(b1, i, d)] = Bloques[b1 : final - 1]
            for o in Origenes:
                final = b1 + 2 * Bo[(i, o)]
                if final > 48:
                    Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1:]
                else:
                    Bloques_para_b0_bo[(b1, i, o)] = Bloques[b1 : final - 1]
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


    r6_sum1 = lambda i, b, t: quicksum(
        Z[i, b, t, d] for d in Destinos 
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


    # R7
    # Las demandas de madera en los destinos deben satisfacerse

    model.addConstrs(
        (
            quicksum(X[i, b, t, d] for i in Camiones) <= Md[d, t]
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R7",
    )

    model.addConstrs(
        (
            X[i, b, t, d] <= Q[i]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos
        ),
        name="R8a",
    )
    model.addConstrs(
        (
            W[i, b, t, o] <= Q[i]
            for i in Camiones
            for t in Dias
            for b in Bloques
            for o in Origenes
        ),
        name="R8b",
    )

    r9_sum1 = lambda i, b, t: quicksum(
        Z[i, b, t, d] * Dd[d] for d in Destinos 
    )
    r9_sum2 = lambda i, b, t: quicksum(Y[i, b, t, o] * Do[o] for o in Origenes)
    r9_sum3 = lambda t, b: quicksum(
        beta[i] * Cc[i]
        + 2 * (Ckm[i] + E[i] * Ce) * (r9_sum1(i, b, t) + r9_sum2(i, b, t))
        for i in Camiones
    )
    model.addConstr(
        quicksum(r9_sum3(t, b) for t in Dias for b in Bloques) <= G,
        name="R9",
    )

    model.addConstrs(
        (
            (1 - Z[i, b, t, d]) >= alpha[i, b, t]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for d in Destinos

        ),
        name="R13a",
    )


    model.addConstrs(
        (
            (1 - Y[i, b, t, o]) >= alpha[i, b, t]
            for i in Camiones
            for b in Bloques
            for t in Dias
            for o in Origenes
        ),
        name="R13b",
    )



    model.addConstrs(
        (
            quicksum(alpha[i, b, t] for b in Bloques for t in Dias)
            <= bigM * beta[i]
            for i in Camiones
        ),
        name="R14",
    )


    model.addConstrs(
        (
            M[b, t, o]
            == R[o] + M[b, t - 1, o] - quicksum(W[i, b, t, o] for i in Camiones)
            for b in Bloques
            for o in Origenes
            for t in Dias[1:]
        ),
        name="R15",
    )

    model.update()

    # ------------ Función objetivo ------------
    fo_sum1 = lambda t, b, i: quicksum(
        Z[i, b, t, d] * Dd[d] for d in Destinos 
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
    model.computeIIS()
    model.write("model.ilp")
    model.optimize()

    # ------------ Manejo de soluciones ------------
    # model.printAttr('X')

except GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
