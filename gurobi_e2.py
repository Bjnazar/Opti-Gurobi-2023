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

# Construcción de los conjuntos
Camiones = range(num_camiones_diesel + num_camiones_electricos) # i in I
Destinos = range(num_destinos) # d in D
Origenes = range(num_origenes) # o in O
Dias = range(num_dias) # t in T
Bloques = range(48) # b in {1,...,48}
Pedidos = lambda d: range(p[d]) # j in {1,...,pd}, no se si este bien, solo una idea

# Construcción de los parametros
V = { i : randint(10, 100) for i in Camiones } # V_i
A = { i : randint(10, 100) for i in Camiones } # A_i
E = { i : randint(10, 100) for i in Camiones } # E_i
Ckm = { i : randint(10, 100) for i in Camiones } # Ckm_i
Cc = { i : randint(10, 100) for i in Camiones } # Cc_i
Q = { i : randint(10, 100) for i in Camiones } # Q_i
Do = { o : randint(10, 100) for o in Origenes } # Do_o
Dd = { d : randint(10, 100) for d in Destinos } # Dd_d
Md = { (d,t) : randint(10, 100) for d in Destinos for t in Dias } # Md_dt
p = { d : randint(10, 100) for d in Destinos } # p_d
tmaxd = randint(10, 100)
tmaxo = randint(10, 100)
Mo = { (o,t) : randint(10, 100) for o in Origenes for t in Dias } # Mo_ot
Cq = randint(10, 100)
Qmax = randint(10, 100)
Ce = randint(10, 100)
G = randint(10, 100)

# ------------ Generar el modelo ------------
model = Model("Entrega 2 Proyecto")
model.setParam("TimeLimit", 60)

# ------------ Instanciar variables de decisión ------------
U = model.addVars(Bloques, Dias, vtype=GRB.INTEGER, name="U_bt")
X = model.addVars(Camiones, Bloques, Dias, Destinos, vtype=GRB.INTEGER, name="X_ibtd")
W = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.INTEGER, name="W_ibto")
Y = model.addVars(Camiones, Bloques, Dias, Origenes, vtype=GRB.BINARY, name="Y_ibto")
# no se si este bien, solo una idea
variables_z = []
for d in Destinos:
  z = model.addVars(Camiones, Bloques, Dias, Pedidos(d), vtype=GRB.BINARY, name=f"Z_ibtj{d}") 
  variables_z.append(z)
Z = { 
  (i,b,t,j,d) : variables_z[d][i,b,t,j] for i in Camiones for b in Bloques for t in Dias for d in Destinos for j in Pedidos(d)
}
alpha = model.addVars(Camiones, Bloques, Dias, vtype=GRB.BINARY, name="alpha_ibt")
beta = model.addVars(Camiones, vtype=GRB.BINARY, name="beta_i")

model.update()

# ------------ Agregar restricciones ------------
# R1
b_p = lambda o,i: math.ceil(Do[o]/(2*V[i]))
model.addConstrs(
  ( Y[i,b,t,o] == Y[i,b-b_p(o,i),t,o] for i in Camiones for o in Origenes for b in Bloques[b_p(o,i):] for t in Dias), 
  name="R1a"
)
model.addConstrs(
  ( b_p(o,i) <= 47 for i in Camiones for o in Origenes), 
  name="R1b"
)

# R2
b_pp = lambda d,i: math.ceil(Dd[d]/(2*V[i]))
model.addConstrs(
  ( Z[i,b,t,j,d] >= alpha[i,b-b_pp(d,i),t] for i in Camiones for d in Destinos for b in Bloques[b_pp(d,i):] for t in Dias for j in Pedidos(d)), 
  name="R2a"
)
model.addConstrs(
  ( b_pp(d,i) <= 47 for i in Camiones for d in Destinos), 
  name="R2b"
)

# R3

# R4
model.addConstrs(
  ( U[48,t-1] == U[1,t] for t in Dias[1:]), name="R4"
)

# R5

# R6

# R7

# R8

# R9
model.addConstrs(
  ( U[b,t] <= Qmax for b in Bloques for t in Dias), name="R9"
)

# R10

# R11

# R12

# R13

# R14 
# Las restricciones de la naturaleza de las variables las establece gurobi
#  al crear las variables y definir sus respectivos tipos de datos 

# faltan el resto de las restricciones

# ------------ Función objetivo ------------
fo_sum1 = lambda t,b,i: quicksum(Z[i,b,t,j,d]*Dd[d] for d in Destinos for j in Pedidos(d))
fo_sum2 = lambda t,b,i: quicksum(Y[i,b,t,o]*Do[o] for o in Origenes)
objetivo = quicksum(2*E[i]*( fo_sum1(t,b,i) + fo_sum2(t,b,i) ) for t in Dias for b in Bloques for i in range(num_camiones_diesel))
model.setObjective(objetivo, GRB.MINIMIZE)

# ------------ Optimización del modelo ------------
model.optimize()

# ------------ Manejo de soluciones ------------
model.printAttr('X')