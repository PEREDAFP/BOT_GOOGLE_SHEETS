from guizero import App, Text, PushButton, TextBox, Slider
from random import randrange

#Valores globales...UFFF
valor = randrange(1,100)


#Funciones
def comprobamos():
    global valor
    print(valor)
    if int(introducido.value) > valor:
        resultado.value = "Te has pasado"
    elif int(introducido.value) < valor:
        resultado.value = "Te has quedado corto"
    else:
        resultado.value ="Acertaste...Sigue con el siguiente"
        recalcula()
        introducido.value ="0"

def recalcula():
    global valor
    valor = randrange(1,int(rango.value))

#Vebtaba
app = App("Adivina el número")
app.width = 250
app.height = 200

title = Text(app, "Pulsa el botón")

rango = Slider(app, start=2, end=100, command=recalcula)
button = PushButton(app, comprobamos, text="Comprobamos")
resultado = Text(app, text="")
introducido = TextBox(app, "0")




app.display()
