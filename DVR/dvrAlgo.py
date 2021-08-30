import sys
import asyncio
import logging
from getpass import getpass
from slixmpp.xmlstream.asyncio import asyncio

import slixmpp
import time
import json

'''
Tomado de:https://slixmpp.readthedocs.io/en/slix-1.6.0/getting_started/echobot.html
https://github.com/fritzy/SleekXMPP/tree/develop/examples'''

class dvrAlgo(slixmpp.ClientXMPP):
    def __init__(self, jid, password, nid, neighborNames):
        super().__init__(jid, password)
        self.add_event_handler('session_start', self.start)
        self.add_event_handler("message", self.message)
        self.table = {}
        self.nid = nid
        self.neighborNames = neighborNames

    def BellmanFord(self, table2, sender):
        for i in table2:
            if i in self.table:
                if i != self.id and i != sender:
                    if self.table[i] > self.table[sender] + table2[i]:
                        self.table[i] = self.table[sender] + table2[i]
            else:
                self.table[i] = self.table[sender] + table2[i]
        return print(self.table)

    async def sendEcho(self, to):
        msg = {}
        msg['type'] = 'sendEcho'
        msg['Nodo fuente'] = self.jid
        msg['Nodo destino'] = to
        msg['time'] = time.time()
        self.send_message(mto=to, mbody=json.dumps(msg), mtype='normal')
        self.get_roster()
        await asyncio.sleep(1)

    async def respondEcho(self, to):
        #Responder a un mensaje echo
        msg = {}
        msg['type'] = 'responseEcho'
        msg['Nodo fuente'] = self.jid
        msg['Nodo destino'] = to
        msg['time'] = time.time()
        try:
            self.send_message(mto=to, mbody=json.dumps(msg), mtype='normal')
        except:
            print('ERROR')
        self.get_roster()
        await asyncio.sleep(1)

    async def privateChat(self):
        #Mandar un mensaje privado
        uName = input("Ingrese nombre: ")
        mssg = input("Ingrese mensaje: ")
        try:
            self.send_message(mto=uName, mbody=mssg, mtype='chat')
            self.get_roster()
            await asyncio.sleep(1)
            print("Mensaje enviado")
        except:
            print("ERROR")
    
    async def message(self, msg):
        if msg['type'] in ('chat'):
            print("\nMensaje recibido de %s:\n   %s\n" % (msg['from'], msg['body']))
        elif msg['type'] in ('normal'):
            payload = json.loads(msg['body'])
            if payload['type'] == 'responseEcho':
                distance = time.time() - payload['time']
                for i in self.neighborNames:
                    if self.neighborNames[i] == payload['Nodo fuente']:
                        self.table[i] = distance
                        print("Tabla")
                        print(self.table)
            elif payload['type'] == 'sendEcho':
                await self.respondEcho(payload['Nodo fuente'])
    
    async def start(self, event):
        self.send_presence()
        self.get_roster()
        await asyncio.sleep(1)
        print("\nBienvenido, " + self.jid)
        sigue = True
        while sigue == True:
            opc2 =  int(input("\nSeleccione:\n1. Enviar mensaje a vecinos \n2. Mensaje Privado\n3. Salir\n0. Notificaciones\n"))
            if opc2 == 0:
                self.get_roster()
                await asyncio.sleep(1)
            elif opc2 == 1:
                for i in self.neighborNames:
                    await self.sendEcho(self.neighborNames[i])
            elif opc2 == 2:
                await self.privateChat()
            elif opc2 == 3:
                print("se salio del progrma")
                self.disconnect()
                sigue = False
