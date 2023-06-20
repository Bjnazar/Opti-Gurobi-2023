from random import randint

# Constantes
N_ELECTRICOS = 8
N_DIESEL = 8
N_DESTINOS = 10
N_ORIGENES = 10
N_DIAS = 5
bigM = 10**5

distancias1 = [28, 366, 644, 101, 392, 306, 356, 171, 360, 363]  # origen
distancias2 = [546, 205, 41, 559, 304, 244, 35, 80, 59, 197]  # destino
tpo_en_bloques1 = [1, 11, 19, 3, 12, 9, 11, 5, 11, 11]  # origen
tpo_en_bloques2 = [16, 6, 2, 16, 9, 7, 1, 3, 2, 6]  # destino

emisiones = [0.002064, 0.002114, 0.001994, 0.001961, 0.002064, 0.002114, 0.001994, 0.001961,  0, 0, 0, 0, 0, 0, 0, 0]
autonomias = [644, 483, 563, 523, 644, 483, 563, 523, 643, 150, 150, 250, 643, 150, 150, 250]
precios = [19900000,158852500,277197590,84440000,19900000,158852500,277197590,84440000,118000000,95000000,90000000,138000000,118000000,95000000,90000000,138000000]
costos_km = [800,820,774,761,800,820,774,761,113,170,170,226,113,170,170,226]
capacidades = [120,119,202,63,120,119,202,63,106,129,120,183,106,129,120,183]
bloques_origenes = [1,11,19,3,12,9,11,5,11,11]
bloques_destinos = [16,6,2,16,9,7,1,3,2,6]

Camiones = range(1, N_DIESEL + N_ELECTRICOS + 1)  # i in I
Destinos = range(1, N_DESTINOS + 1)  # d in D
Origenes = range(1, N_ORIGENES + 1)  # o in O
Dias = range(1, N_DIAS + 1)  # t in T
Bloques = range(1, 48 + 1)  # b in {1,...,48}

V = {i: 140 for i in Camiones}  # V_i
A = dict(zip(list(Camiones), autonomias))
E = dict(zip(list(Camiones), emisiones))
Ckm = dict(zip(list(Camiones), costos_km))
Cc = dict(zip(list(Camiones), precios))
Q = dict(zip(list(Camiones), capacidades))
Do = [28, 366, 644, 101, 392, 306, 356, 171, 360, 363]
Dd = [ 546, 205, 41, 559, 304, 244, 35, 80, 59, 197]
Md = {(1, 1): 53, (1, 2): 54, (1, 3): 78, (1, 4): 52, (1, 5): 59, (2, 1): 81, (2, 2): 76, (2, 3): 63, (2, 4): 80, (2, 5): 56, (3, 1): 54, (3, 2): 70, (3, 3): 53, (3, 4): 57, (3, 5): 77, (4, 1): 67, (4, 2): 81, (4, 3): 63, (4, 4): 88, (4, 5): 70, (5, 1): 58, (5, 2): 74, (5, 3): 70, (5, 4): 81, (5, 5): 60, (6, 1): 77, (6, 2): 79, (6, 3): 71, (6, 4): 72, (6, 5): 76, (7, 1): 53, (7, 2): 53, (7, 3): 67, (7, 4): 62, (7, 5): 79, (8, 1): 53, (8, 2): 71, (8, 3): 62, (8, 4): 64, (8, 5): 62, (9, 1): 85, (9, 2): 76, (9, 3): 90, (9, 4): 82, (9, 5): 63, (10, 1): 89, (10, 2): 74, (10, 3): 83, (10, 4): 74, (10, 5): 72}
R = {1: 48, 2: 57, 3: 81, 4: 33, 5: 111, 6: 102, 7: 100, 8: 29, 9: 105, 10: 106}  # el origen que está más cerca ofrece menos
Bo = {(i, o):bloques_origenes[o - 1] for o in Origenes for i in Camiones}
Bd = {(i, d): bloques_destinos[d - 1] for d in Destinos for i in Camiones}
tmaxd = 10
Cq = 20000
Qmax = 500
Ce = 5000
G = 47600000000  #Ajustar números

# R = {o: randint(50, 130) if Do[o - 1] > 300 else randint(20, 50) for o in Origenes}
