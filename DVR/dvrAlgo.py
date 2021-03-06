# Laboratorio 3 - Redes
# Abril Palencia, Cristina Bautista, Isabel Ortiz 

import slixmpp
import json
import time
import pandas as pd
import numpy as np
from aioconsole import ainput
from tabulate import tabulate
from utils import get_ID, get_JID, get_neighbors
from settings import ECO_TIMER, TABLE_TIMER

'''
Tomado de: https://slixmpp.readthedocs.io/en/slix-1.6.0/getting_started/echobot.html
        https://github.com/fritzy/SleekXMPP/tree/develop/examples
'''
global interval

class dvrAlgo(slixmpp.ClientXMPP):

    def __init__(self, jid, password, login = True):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.logged = False
        self.jid = jid
        self.names_file = ''
        self.topo_file = ''
        self.nickName = ''
        self.status = 'Activo'
        self.neighbors = list()
        self.neighborsTimeSend = None
        self.table = None
        if not login:
            self.add_event_handler("register", self.register)
        
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data forms
        self.register_plugin('xep_0066') # Out-of-band Data
        self.register_plugin('xep_0077') # In-band Registration
        self.register_plugin('xep_0199') # XMPP Ping
        self.register_plugin('xep_0045') # Mulit-User Chat (MUC)
        self.register_plugin('xep_0085') # Chat State Notifications
        self.register_plugin('xep_0096') # Jabber Search
        self.register_plugin('xep_0059')
        self.register_plugin('xep_0060')
        self.register_plugin('xep_0071')
        self.register_plugin('xep_0128')
        self.register_plugin('xep_0363')

    async def session_start(self, event):
        self.send_presence(pstatus=self.status)
        await self.get_roster()
        
        self.topo_file = str(input("Ingresa el nombre del archivo de la topología de la red: "))
        self.names_file = str(input("Ingresa el nombre del archivo de la asignación de ID con nodo: "))
        
        self.nickName = get_ID(names_file=self.names_file, JID=self.jid)
        self.neighbors = get_neighbors(topology_file=self.topo_file, ID=self.nickName)
        self.neighborsTimeSend = np.zeros(len(self.neighbors))
        
        self.table = pd.DataFrame(index=['neighbour', 'distance'], columns=self.neighbors + [self.nickName])
        self.table.loc['distance'] = np.inf        
        self.table.at['distance', self.nickName] = 0

        self.send_eco()
        self.schedule('send_eco', ECO_TIMER, self.send_eco, repeat=True)
        self.schedule('send_table', TABLE_TIMER, self.send_table, repeat=True)

        self.logged = True
        appMenu = 0
        
        while appMenu != 2:
            try:
                appMenu = int(await ainput(""" 
                                                            MENU DVR
                                        Ingresa el número de la opción que deseas realizar:
                                        1. Enviar un mensaje directo
                                        2. Cerrar Sesión
                                        >"""))
            except: 
                appMenu = 0
                print("Ingresa una opción correcta")                
      
            self.send_presence(pstatus=self.status)
            await self.get_roster()
            
            if(appMenu == 1):
                await self.sendMessage()

            elif(appMenu == 2):
                print("Cerrando sesión...")
            
            elif(appMenu != 0):
                print("Ingresa una opción correcta")
        
        self.cancel_schedule('send_eco')
        self.cancel_schedule('send_table')
        self.disconnect()

    async def register(self, iq):
        msg = self.Iq()
        msg['type'] = 'set'
        msg['register']['username'] = self.boundjid.user
        msg['register']['password'] = self.password
        try:
            await msg.send()
            print("Cuenta creada!")
        except:
            print("Error")
            self.disconnect()

    def message(self, msg):
        if msg['type'] == 'chat':
            message = json.loads(msg['body'])
            if message["recipientNode"] == self.jid:        
                print("NOTIFICACION")
                print(json.dumps(message, indent=4, sort_keys=True))
            else:
                message["jumps"] = message["jumps"] + 1
                message["nodesList"].append(self.jid)
                self.send_message(
                        mto=get_JID(
                            names_file=self.names_file, 
                            ID=self.table[get_ID(names_file=self.names_file, JID=message["recipientNode"])]['neighbour']
                            ),
                        mbody=json.dumps(message),
                        mtype='chat')
        
        elif msg['type'] == 'normal':
            message = json.loads(msg['body'])
            
            if message['type'] == 'ecoSend':
                message['type'] = 'ecoResponse'
                self.send_message(mto=str(msg['from']).split('/')[0],
                            mbody=json.dumps(message),
                            mtype='normal')

            elif message['type'] == 'ecoResponse': 
                if(time.time() - message["sendTime"] > 1):
                    message['type'] = 'ecoSend'
                    message["sendTime"] = time.time()
                    self.send_message(mto=str(msg['from']).split('/')[0],
                                mbody=json.dumps(message),
                                mtype='normal')
                else:   
                    self.table.at['distance', message["recipientNode"]] = (time.time() - message["sendTime"]) / 2
                    self.table.at['neighbour', message["recipientNode"]] = message["recipientNode"]     

            elif message['type'] == 'table':
                table = message["table"]
                senderNode = message["senderNode"]
                for node in table.keys():
                    if node != self.nickName:
                        if node not in self.table.columns:
                            self.table.at['neighbour', node] = ''
                            self.table.at['distance', node] = np.inf
                        d = min((self.table.at['distance', senderNode] + table[node]), self.table.at['distance', node])
                        if d != self.table.at['distance', node]:
                            self.table.at['distance', node] = d
                            self.table.at['neighbour', node] = senderNode
    
    async def sendMessage(self):

        contact = str(await ainput("JID del usuario al que deseas enviar mensaje: "))
        print("Mensaje:")
        message = str(await ainput(">")) 
        try:
            recipientNode = get_ID(names_file=self.names_file, JID=contact)
            if(recipientNode in self.table.columns and self.table[recipientNode]['neighbour'] is not np.nan and self.table[recipientNode]['distance'] is not np.inf):
                msg = {}
                msg["hola"] = self.jid
                msg[" "] = contact
                msg[" "] = 1
                msg[" "] = self.table[recipientNode]['distance']
                msg[" "] = [self.jid]
                msg["message"] = message
                self.send_message(mto=get_JID(names_file=self.names_file, ID=self.table[recipientNode]['neighbour']),
                                mbody=json.dumps(msg),
                                mtype='chat')
            else:
                print("El mensaje no se puede enviar a esa persona.")
        except:
            print("no esta en los nodos")
    
    def send_eco(self):
        for neighbour in self.neighbors:
            msg = {}
            msg[" "] = 'ecoSend'
            msg[" "] = self.nickName
            msg[" "] = neighbour
            msg[" "] = time.time()
            self.send_message(mto=get_JID(names_file=self.names_file, ID=neighbour),
                        mbody=json.dumps(msg),
                        mtype='normal')
    
    def send_table(self):
        for neighbour in self.neighbors:
            msg = {}
            msg[" "] = 'table'
            msg[" "] = self.nickName
            msg[" "] = neighbour
            msg["table"] = self.table.loc['distance'].to_dict()
            self.send_message(mto=get_JID(names_file=self.names_file, ID=neighbour),
                        mbody=json.dumps(msg),
                        mtype='normal') 