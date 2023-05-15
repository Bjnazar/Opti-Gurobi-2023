from gurobipy import GRB, Model, quicksum
from random import randint, seed

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
Pedidos = lambda p_d: range(p_d) # j in {1,...,pd}, no creo q este bien, solo una idea

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
Z = model.addVars(Camiones, Bloques, Dias, Pedidos(d), Destinos, vtype=GRB.BINARY, name="Z_ibtjd") # no creo q este bien, solo una idea
# falta alpha_ibt
# falta beta_i

model.update()

# ------------ Agregar restricciones ------------
model.addConstrs(
  ( U[48,t-1] == U[1,t] for t in Dias[1:]), name="R4"
)
# faltan el resto de las restricciones

# ------------ Función objetivo ------------
objetivo = quicksum( 2*E[i]*(quicksum( ) + quicksum()) for t in Dias for b in Bloques for i in range(num_camiones_diesel)) #**
model.setObjective(objetivo, GRB.MINIMIZE)

# ------------ Optimización del modelo ------------
model.optimize()

# ------------ Manejo de soluciones ------------
model.printAttr('X')