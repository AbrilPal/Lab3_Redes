import slixmpp
import logging
from getpass import getpass
from argparse import ArgumentParser
from slixmpp.exceptions import IqError, IqTimeout
import asyncio

import json

from numpy import inf


# Muestra en consola e DEBUG
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

def jsonDict(archivo):
  with open(archivo) as jsonFile:
    return json.load(jsonFile)

def getData(node, archivo):
  info = jsonDict(archivo)
  if info['type'] == 'topo':
    return info['config'][node]
  elif info['type'] == 'users':
    return info['config']
  else:
    return -1

def keys(archivo):
  info = jsonDict(archivo)
  return list(info['config'].keys())

class Client(slixmpp.ClientXMPP):
  # Empieza lo bueno
  def __init__(self, userid, password,  t_keys=None):
    slixmpp.ClientXMPP.__init__(self, userid, password)
    self.userid = userid
    self.password = password
    self.connected_event = asyncio.Event()
    # self.topo_keys = t_keys


    self.add_event_handler("session_start", self.sessionStart)
    self.add_event_handler("register", self.registrar)
    self.add_event_handler("message", self.message)
    # self.add_event_handler("got_online", self.node_connected)
    self.add_event_handler("got_offline", self.node_disconnected)

    self.register_plugin('xep_0030')
    self.register_plugin('xep_0045')
    self.register_plugin('xep_0004')
    self.register_plugin('xep_0060')
    self.register_plugin('xep_0199')

  async def sessionStart(self, e):
    try:
      self.send_presence()
      await self.get_roster()
      self.connected_event.set()

    except IqError as e:
      logging.error("Could not register account: %s" % e.iq['error']['condition'])
    except IqTimeout:
      logging.error("No response from server.")

    loginStart = True
    while loginStart:
      print("""
      
      Submenu

      1.  Nombre del nodo asignado al carnet
      8.  Eliminar la cuenta
      9.  Salir de la sesion
      
      
      """)
      loginOption = int(input("Que opcion desea realizar? "))

      if loginOption == 1:
        wantedNode = input("Escriba el nodo: ")
        topologia = getData(wantedNode, "topologia.txt")
        print(topologia)
        usuarios = getData(wantedNode, "usuarios.txt")
        print(usuarios)

      elif loginOption == 8:
        self.register_plugin('xep_0030') 
        self.register_plugin('xep_0004')
        self.register_plugin('xep_0077')
        self.register_plugin('xep_0199')
        self.register_plugin('xep_0066')

        eliminar = self.Iq()
        eliminar['type'] = 'set'
        eliminar['from'] = self.boundjid.user
        eliminar['register']['remove'] = True
        print('*************Eliminado******************')
        eliminar.send()
        
        self.disconnect()

      elif loginOption == 9:
        self.disconnect()
        loginStart = False

      else:
        print("Por favor escoje una opcion del menu")




  async def registrar(self, iq):
    resp = self.Iq()
    resp['type'] = 'set'
    resp['register']['username'] = self.boundjid.user
    resp['register']['password'] = self.password

    try:
      await resp.send()
      logging.info("Account created for %s!" % self.boundjid)

      print("\n\n\n\n\n SE R E G I S T R O")

    except IqError as e:
      logging.error("Could not register account: %s" % e.iq['error']['text'])
      self.disconnect()
    except IqTimeout:
      logging.error("No response from server.")
      self.disconnect()


  async def message(self, msg):
    if msg['type'] in ('normal', 'chat'):
      await print("\n{}".format(msg['body']))
  
  def node_connected(self, e):
    pass

  def node_disconnected(self, e):
    print("\n{}".format(e['from'].bare))

  


def registrar(userid, password):
  cliente = Client(userid, password)
  cliente.register_plugin("xep_0030")
  cliente.register_plugin("xep_0004")
  cliente.register_plugin("xep_0077")
  cliente.register_plugin("xep_0199")
  cliente.register_plugin("xep_0066")

  cliente["xep_0077"].force_registration = True

  cliente.connect()
  cliente.process(forever=False)


  
def iniciarSesion(userid, password):
  cliente = Client(userid, password)
  cliente.register_plugin("xep_0030")
  cliente.register_plugin("xep_0199")

  cliente.connect()
  cliente.process(forever=False)



start = True

while start:
  print("""
  Bienvenido!

  0. Registrar
  1. Iniciar Sesion
  2. Salir del proyecto
  
  """)
  firstOption = int(input("Que opcion desea realizar? "))
  if firstOption == 0:

    userid = input("Ingrese userid con @alumchat.xyz: ")
    password = input("Ingrese una password: ")

    registrar(userid, password)
    


  elif firstOption == 1:

    userid = input("Ingrese userid con @alumchat.xyz: ")
    password = input("Ingrese una password: ")
    iniciarSesion(userid, password)

    



  elif firstOption == 2:
    print("Hasta pronto!")
    start = False


  else:
    print("Por favor escoje una opcion del menu")






