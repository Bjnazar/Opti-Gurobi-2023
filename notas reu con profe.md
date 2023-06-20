
# Reunión con profe 2023-06-20
## Numeros demasiado grandes
Fijense en estos warnings:
    Warning: Model contains large matrix coefficients
    Warning: Model contains large rhs
        rhs es right hand side

Pasen los precios a millones (números mas chicos).
Esto implica cambiar todas las veces que se mencione plata en el modelo.
Esta linea les va a ser util:
precios = [p/10**6 for p in precios]
