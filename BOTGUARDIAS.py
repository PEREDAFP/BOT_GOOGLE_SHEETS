'''
Script de control bot Telegram que permite a los profesores de un IES
obtener en una sesión determinada los servicios de guardia que deben atender.

Los profesores podrán seleccionar a qué guardia acuden

Los datos se obtienen y modifican de una hoja de cálculo google similar a ControlGuardias.ods
'''


import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

#La parte Google
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
        self.fecha = datetime.datetime.now().strftime("%d/%m/%Y")


    def hoja(self, hoja):
        self.hoja_activa = self.libro.worksheet(hoja)

    def modifica_celda(self, celda, valor):
        self.hoja_activa.update_acell(celda, valor)

    def devuelve_celda(self,fila, columna):
        return  self.hoja_activa.cell(fila, columna).value

    def devuelve_lista_guardias_pendientes(self):
        '''
        Genera una lista con las guardias del día y la hora
        pendientes
        En cada entrada
        [fila,orden,sesión,observaciones]
        '''
        lista = list()
        fila = 7
        columna_fecha = 3
        columna_sesion = 4
        columna_orden = 5
        columna_observaciones = 6
        columna_resuelto = 8
        valor = self.devuelve_celda(fila, columna_fecha)
        while (valor != ""):
            if (valor == self.fecha) and (self.devuelve_celda(fila, columna_resuelto)==""):
                lista.append([fila, self.devuelve_celda(fila, columna_orden),self.devuelve_celda(fila, columna_sesion),self.devuelve_celda(fila, columna_observaciones)])
            fila += 1
            valor = self.devuelve_celda(fila, columna_fecha)
        return lista

#Ahora viene la parte Telegram

TOKEN = "TOKEN TELEGRAM"
bot = telebot.TeleBot(TOKEN)
user_dict = {}

class Profesor:
    def __init__(self, name, lista):
        self.name = name
        self.sesion = ""
        self.listaguardias = lista



@bot.message_handler(commands=['help', 'start', 'guardia'])
def send_welcome(message):
    msg = bot.reply_to(message, """\
        Introduce tu nombre y apellidos:
            """)
    bot.register_next_step_handler(msg, process_pedir_nombre)

@bot.message_handler(commands=['help'])
def send_ayuda(message):
    msg = bot.reply_to(message, """\n
    Este bot permite que introduzcas la guardia en la que realizas la sustitución
    Basta con seguir los pasos que van apareciendo para

""")


def process_pedir_nombre(message):
    LIBRO = 'Nombre del libro'
    HOJA = 'Nombre de la hoja dentro del libro'
    try:
        libro = HojaGoogle('credenciales.json', LIBRO)
        libro.hoja(HOJA)
        lista = libro.devuelve_lista_guardias_pendientes()
    except:
        envio =  "Hemos superado la cuota de peticiones a google Api. Inténtalo pasados 100 segundos. Gracias"

    try:
        chat_id = message.chat.id
        name = message.text
        user = Profesor(name, lista)
        user_dict[chat_id] = user

        #Si existen guardias hacemos esto
        if len(user.listaguardias) > 0:
            msg = bot.reply_to(message, '¿Estás de guardia ahora?(S/N)')
            bot.register_next_step_handler(msg, process_pedir_sesion)
        else:
            msg = bot.reply_to(message, 'De momento, todo está traquilo. Muchas gracias')

    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_pedir_sesion(message):
    try:
        chat_id = message.chat.id
        eleccion = message.text
        user = user_dict[chat_id]
        if eleccion.lower() != 's':
            msg = bot.reply_to(message, 'Adióssss.Saludos')
            return
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        #Creamos la botonera con las sesiones pendientes
        for i in user.listaguardias:
            #[fila,orden,sesión,observaciones]
            markup.add("{}###Sesión {} Observaciones: {}".format(i[1], i[2],i[3]))

        #Añadimos la sesión con Orden 0 para que pueda ser elegida por profesores cuya hora de guardia
        #no coincida con ninguna de las sesiones con sustitución pendiente
        markup.add("{}###Sesión {} Observaciones: {}".format(0, "0", "No hay ninguna sesión que coincida con mis horas de guardia"))

        msg = bot.reply_to(message, 'Elige la sesión:', reply_markup=markup)
        bot.register_next_step_handler(msg, process_paso_final)
    except Exception as e:
        bot.reply_to(message, 'oooops sesión')


def process_paso_final(message):
    #try:
        #Obtenemos el orden, para obtener la fila, que nos permitirá grabar en la hoja
        chat_id = message.chat.id
        sesion = message.text
        #Leemos el mensaje que nos ha enviado y separamos por las tres almohadillas
        sesion_orden = sesion.split('###')[0]
        user = user_dict[chat_id]
        if sesion_orden == '0':
            bot.send_message(chat_id, 'Gracias {}. \n En tu hora de guardia no hay ninguna incidencia'.format(user.name))
        else:
            #[fila,orden,sesión,observaciones]
            fila = list(filter (lambda i: i[1] == sesion_orden.strip(), user.listaguardias))[0][0]

            celda_sustitucion = 'G' + str(fila)
            celda_resuelto = 'H'+ str(fila)
            try:
                #Ahora lo hacemos con la hoja de cálculo...igual existe
                #TODO: ¿Se puede hacer de otra forma sin duplicar tanto código?
                LIBRO = 'Control Guardias'
                HOJA = 'Control'
                libro = HojaGoogle('credenciales.json', LIBRO)
                libro.hoja(HOJA)
                lista = libro.modifica_celda(celda_sustitucion, user.name)
                lista = libro.modifica_celda(celda_resuelto, 'S')
            except:
                envio =  "Hemos superado la cuota de peticiones a google Api. Inténtalo pasados 100 segundos. Gracias"
            bot.send_message(chat_id, 'Gracias {}. \n Has elegido la guardia {}'.format(user.name,sesion))
    #except Exception as e:
        #bot.reply_to(message, 'oooops final')


def main(args):
    # Los datos se guardan en  "./.handlers-saves/step.save".
    # Si hubiera un bloqueo y no se avanza en el bot...hay que eliminar ete directorio
    bot.enable_save_next_step_handlers(delay=2)
    bot.load_next_step_handlers()
    bot.polling()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
