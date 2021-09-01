import json
import asyncio
import logging
import getpass
from LSR import LSR
from nodo import Nodo
from aioconsole import ainput
from optparse import OptionParser
from aioconsole.stream import aprint


def jsonDict(file):
	with open(file) as jsonFile:
		return json.load(jsonFile)

def getData(node, file):
	info = jsonDict(file)
	if info['type'] == 'topo':
		return info['config'][node]
	elif info['type'] == 'users':
		return info['config']
	else:
		return -1

def keys(file):
	info = jsonDict(file)
	return list(info['config'].keys())

async def main(nodo : LSR):
  for router in nodo.neighbors_niknames:
    nodo.send_presence_subscription(nodo.neighbors[router], nodo.boundjid)

  nodo.init_listener()


  is_connected = True
  while is_connected:
    print("-"*40) 
    print(
    """

    Menu:
    1.  Enviar mensaje
    2.  Salir

    """
    )
    opt = int( await ainput("Escoje una opcion: \n"))
    if opt == 1:
      dest = await ainput("Escribe el userid destinatario: ")
      msg = await ainput("Cual es el mensaje que desea enviar? ")
      nodo.send_msg(
        dest,
        msg
      )
    elif opt == 2:
      nodo.is_offline = True
      print("Disconnecting ...")
      await asyncio.sleep(10)
      is_connected = False
      nodo.disconnect()
    else:
      pass

        


if __name__ == "__main__":

  optp = OptionParser()

  t_k = keys("topo.txt")

  # para debbuging
  optp.add_option('-d', '--debug', help='set loggin to DEBUG', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
  # para debbuging
  optp.add_option("-u", "--userid", dest="userid", help="userid to use")
  # para debbuging
  optp.add_option("-p", "--password", dest="password", help="password to use")
  # para debbuging
  optp.add_option("-n", "--new", dest="newUserid", help="is registering a new user", action='store_const', const=True, default=False)
  # para debbuging
  optp.add_option("-r", "--router", dest="router", help="router nickname")
  # para debbuging
  optp.add_option("-a", "--algorithm", dest="algorithm", help="algorithm to use")

  opts, args = optp.parse_args()

  if opts.userid is None:
    opts.userid = input("Ingrese userid con @alumchat.xyz: ")
  if opts.password is None:
    opts.password = getpass.getpass("Ingrese una password: ")
  if opts.router is None:
    opts.router = input("Router a escoger: ")
  if opts.algorithm is None:
    opts.algorithm = input("Algorithm a escoger (unica opcion lsr): ")

  logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')


  assignedNode = opts.router
  topo = getData(assignedNode,'topo.txt')
  users = getData(assignedNode,'users.txt')
  print(topo)
  print(users)
  assignedNodes = {}
  for i in topo:
    assignedNodes[i] = users[i] 

  if opts.algorithm == 'lsr':
    nodo = LSR(opts.userid, opts.password, assignedNode, assignedNodes)
  else:
    nodo = None

  if nodo != None:
    try:
      if opts.newUserid:
        print("Proceso de registro de usuario")
      print("Proceso de conexion a la alumchat.xyz")
      nodo.connect() 
      nodo.loop.run_until_complete(nodo.connected_event.wait())
      nodo.loop.create_task(main(nodo))
      nodo.process(forever=False)
    except Exception as e:
      print("Error:", e)
    finally:
      nodo.disconnect()
  else:
    print("Algoritmo no es correcto")
