from random import randint, seed

N_ELECTRICOS = 5
N_DIESEL = 5
N_DESTINOS = 3
N_ORIGENES = 3
N_DIAS = 5
bigM = 100**9

distancias1 = [0, 28, 366, 644, 101, 392, 306, 356, 171, 360, 363]  # origen
distancias2 = [0, 546, 205, 41, 559, 304, 244, 35, 80, 59, 197]  # destino
tpo_en_bloques1 = [0, 1, 11, 19, 3, 12, 9, 11, 5, 11, 11]  # origen
tpo_en_bloques2 = [0, 16, 6, 2, 16, 9, 7, 1, 3, 2, 6]  # destino

emisiones = [0.002064, 0.002114, 0.001994, 0.001961,  0.001961, 0 , 0 , 0 , 0 , 0]
autonomias = [370, 650, 300, 200, 400, 370, 400, 300, 644, 200]
bloques_origenes = [11, 19, 3]
bloques_destinos = [6, 2, 7]

demandas = []

Camiones = range(1, N_DIESEL + N_ELECTRICOS + 1)  # i in I
Destinos = range(1, N_DESTINOS + 1)  # d in D
Origenes = range(1, N_ORIGENES + 1)  # o in O
Dias = range(1, N_DIAS + 1)  # t in T
Bloques = range(1, 48 + 1)  # b in {1,...,48}

# Para 5 electricos y 5 diesel, 3 origenes y 3 destinos
# Los primeros 5 son diesel, y los ultimos 5 son eléctricos

A = dict(zip(list(Camiones), autonomias))
E = dict(zip(list(Camiones), emisiones))
Ckm = {1: 217, 2: 168, 3: 147, 4: 211, 5: 152, 6: 166, 7: 130, 8: 117, 9: 122, 10: 124}
Cc = {1: 132430027, 2: 265728443, 3: 198450268, 4: 234935954, 5: 98161793, 6: 88914862, 7: 270097160, 8: 119208589, 9: 267390289, 10: 251585921}
Do = [366, 644, 101]
Dd = [205, 41, 244]
Md = {(1, 1): 63, (1, 2): 70, (1, 3): 65, (1, 4): 69, (1, 5): 57, (2, 1): 76, (2, 2): 58, (2, 3): 69, (2, 4): 82, (2, 5): 53, (3, 1): 51, (3, 2): 76, (3, 3): 66, (3, 4): 69, (3, 5): 85}
Q = {1: 171, 2: 168, 3: 144, 4: 123, 5: 139, 6: 138, 7: 200, 8: 124, 9: 117, 10: 173}
R = {1: 50, 2: 120, 3: 20}  # el origen que está más cerca ofrece menos
Bo = {(i, o):bloques_origenes[o - 1] for o in Origenes for i in Camiones}
Bd = {(i, d): bloques_destinos[d - 1] for d in Destinos for i in Camiones}

# # Muestra los valores de las soluciones
# print("\n"+"-"*10+" Manejo Soluciones "+"-"*10)
# print(f"El valor objetivo es de: {model.ObjVal}")
# for sitio in Sitios:
#     if x[sitio].x != 0:
#         print(f"Se construye un campamento en el sitio {sitio}")
#     if s[sitio].x != 0:
#         print(f"Se asignan {s[sitio].x} personas para vacunarse en el campamento construido en el sitio {sitio}")
#     for localidad in Localidades:
#         if y[localidad, sitio].x != 0:
#             print(f"Se asocia la localidad {localidad} con el campamento ubicado en el sitio {sitio}")

# # ¿Cuál de las restricciones son activas?
# print("\n"+"-"*9+" Restricciones Activas "+"-"*9)
# for constr in model.getConstrs():
#     if constr.getAttr("slack") == 0:
#         print(f"La restriccion {constr} está activa")


# model.printAttr("X")