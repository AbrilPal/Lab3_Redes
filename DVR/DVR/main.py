# Laboratorio 3 - Redes
# Abril Palencia, Cristina Bautista, Isabel Ortiz 
import getpass
from dvrAlgo import dvrAlgo
import logging
from settings import *

if __name__ == '__main__':
    if DEBUG:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        ch.setFormatter(formatter)
        logger.addHandler(ch)

    initialMenu = 0
    while initialMenu != 3:
        try:
            initialMenu = int(input("""
                                        MENU DVR
                                        1. Registrarse 
                                        2. Iniciar sesión con una cuenta existente
                                        3. Salir
                                        
                                    ----->"""))
            if(initialMenu == 1):
                jid = str(input("JID: "))
                password = str(getpass.getpass("Contraseña: "))
                xmpp = dvrAlgo(jid, password, login=False)         
                xmpp.connect()
                xmpp.process(forever=False)

            elif(initialMenu == 2):
                jid = str(input("JID: "))
                password = str(getpass.getpass("Contraseña: "))
                xmpp = dvrAlgo(jid, password)
                xmpp.connect()
                xmpp.process(forever=False)
                if(not xmpp.logged):
                    print("No se pudo iniciar sesión, revisa tus credenciales")
                    xmpp.disconnect()

            elif(initialMenu == 3):
                print("Gracias por utilizar la aplicación!")
            else:
                print("Ingresa una opción correcta")
        except: 
            print("ERROR")
