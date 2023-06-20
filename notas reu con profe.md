
# Reunión con profe 2023-06-20
## Numeros demasiado grandes
Fijense en estos warnings:
- Warning: Model contains large matrix coefficients
- Warning: Model contains large rhs (rhs es right hand side)

Pasen los precios a millones (números mas chicos).
Esto implica cambiar todas las veces que se mencione plata en el modelo.

Esta linea les va a ser util:
precios = [p/10**6 for p in precios]

## R14 
### Pero hay que revisar los índices
Indicio de bug: encontramos que se estaba asignando carga en el bloque 48
### Algunas W quedaron libres


## Conviene guardar cosas que se demoren en computar (ex. restricciones)
- TODO: Milan: pickling de restricciones
- También sería buena idea usar jupyter notebook. Hecho pr Berni en reunión.

## Trucos para imprimir soluciones
- Para binarias, poner un if > 0.5 para que se impriman solo las que hayan quedado asignadas con 1.

## Las restricciones que relacionan X con Z y W con Y probablemente tienen problemas de indices