from gurobipy import GRB, Model, quicksum, GurobiError
from random import randint, seed, uniform

seed(10)
try:
    m = Model()

    # SETS
    I = range(10)
    J = range(8)

    # PARAMS
    t = {(i, j): uniform(6, 15) for i in I for j in J}  
    c = [randint(10, 20) for i in I]
    b1 = randint(3, 7)
    b2 = randint(3, 7)
    p = randint(3, 7)
    n = 3
    alpha = 10
    beta = 8

    # Coloque aca sus variables
    x = m.addVars(I, J, vtype = GRB.BINARY, name="x_ij")
    y = m.addVars(J, vtype = GRB.BINARY, name="y_j")
    v = m.addVars(I, vtype = GRB.BINARY, name="v_i")
    w = m.addVars(I, vtype = GRB.BINARY, name="w_i")
    z1 = m.addVar(vtype = GRB.CONTINUOUS, name="z1")
    z2 = m.addVar(vtype = GRB.CONTINUOUS, name="z2")

    m.update()

    # Coloque aca sus restricciones
    m.addConstrs((quicksum(x[i, j] for j in J) == 1 for i in I), name="R1")
    m.addConstr((quicksum(y[j] for j in J) == n), name="R2")
    m.addConstrs((x[i, j] <= y[j] for i in I for j in J), name="R3")
    m.addConstrs((x[i, j] >= y[j] - quicksum(y[k] for k in J if t[i, k] < t[i, j]) for i in I for j in J), name="R4")
    m.addConstrs((v[i] <= quicksum(y[j] for j in J if t[i, j] <= alpha) for i in I), name="R5")
    m.addConstrs((w[i] <= quicksum(y[j] for j in J if t[i, j] <= beta) for i in I), name="R6")
    m.addConstr((((quicksum(v[i] for i in I))/10) == 0.85 + z1), name="R7")
    m.addConstr(((quicksum(c[i]*w[i] for i in I)) == (0.9 + z2)*quicksum(c[i] for i in I)), name="R8")
    m.addConstr((z1 >= 0), name="R9")
    m.addConstr((z2 >= 0), name="R10")

    m.update()

    objetivo = b1*z1 + b2*z2 - p*(quicksum((t[i, j] - alpha)*x[i, j] for i in I for j in J if t[i, j] > alpha))
    m.setObjective(objetivo, GRB.MAXIMIZE) # Colocar la FO, RECUERDEN EL MAXIMIZE

    m.optimize()
    m.printAttr('X')

    # Funcion objetivo: 1.137804878049e+00

except GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')