'''
Este script es un bot Telegram que muestra los alumnos de un determinado
grupo del IES que se encuentran en cuarentena covid19villaverde


Obtiene esa información de una hoja de cálculo google con una estructura similar a la hoja
de cálculo DATOSCOVID19.ods
'''

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import telebot
TOKEN = "AQUÍ EL TOKEN DE TU API TELEGRAM"
bot = telebot.TeleBot(TOKEN)


class HojaGoogle():
    def __init__(self, credenciales, libro):
        scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/spreadsheets',
                      'https://www.googleapis.com/auth/drive.file',
                      'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credenciales, scope)
        try:
            self.conexion = gspread.authorize(creds)
        except:
            print("Se ha producido un error...comprueba algo...claro")

        self.libro = self.conexion.open(libro)
        self.hoja_activa = None


    def hoja(self, hoja):
        self.hoja_activa = self.libro.worksheet(hoja)

    def modifica_celda(self, celda, valor):
        self.hoja_activa.update_acell(celda, valor)

    def devuelve_celda(self,fila, columna):
        return  self.hoja_activa.cell(fila, columna).value

    def devuelve_lista_alumnos_curso_cuarentena(self, curso):
        '''
        Genera una lista con los alumnos del grupo seleccionado
        que tienen en blanco la columna de incorporación
        Lo que indica que no pueden incorporarse
        '''
        lista = list()
        fila = 5
        columna_curso = 3
        columna_incorporacion = 7
        grupo = self.devuelve_celda(fila, columna_curso)
        while (grupo != ""):
            if (grupo == curso) and (self.devuelve_celda(fila, columna_incorporacion)==""):
                lista.append(self.devuelve_celda(fila, columna_curso + 1))
            fila += 1
            grupo = self.devuelve_celda(fila, columna_curso)
        return lista


@bot.message_handler(commands=['start','ayuda','help'])
def send_welcome(message):
    texto = '''
    Este es el bot de pruebas COVID 19
    Basta con introducir el grupo de clase y se enviará la lista de alumnos que aún no han terminado
    de pasar la devuelve_lista_alumnos_curso_cuarentena.
    Recuerda que los nombres no aparecerán completos y necesitarás la lista para saber de qué número estamos hablando
    '''
    bot.reply_to(message, texto)

@bot.message_handler(func= lambda message: True, content_types=['text'])
def enviamos_informacion(message):
    HOJA='ELNOMBREDELAHOJASOBRELAQUEVAMOSATRABAJAR'
    GRUPO = message.text
    envio = ""
    try:
        libro = HojaGoogle('FICHEROcredenciales.json', 'NOMBREDELAHOJADECÁLCULO')
        libro.hoja(HOJA)
        lista = libro.devuelve_lista_alumnos_curso_cuarentena(GRUPO)
        if len(lista) == 0:
            envio = "No hay resultado para " + message.text
        else:
            for i in lista:
                envio += i + "; "
    except:
        envio =  "Hemos superado la cuota de peticiones a google Api. Inténtalo pasados 100 segundos. Gracias"

    bot.send_message(message.chat.id,"Los alumnos que no pueden estar en clase son: "+ envio)


def main(args):
    bot.polling()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
