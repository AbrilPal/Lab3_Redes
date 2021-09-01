import json
import asyncio
import numpy as np
from nodo import Nodo
from time import time
from asyncio import sleep
from aioconsole import aprint
from slixmpp.basexmpp import BaseXMPP
from xml.etree import ElementTree as ET
from scipy.sparse.csgraph import shortest_path


DEAD = 20

class LSR(Nodo):
  def __init__(self, userid, password, entity, asoc_nodes = None):
    super().__init__(userid, password)
    self.LSA_seqnum = 0
    self.LSA = {}
    self.entity = entity
    self.basexmpp = BaseXMPP()
    self.topo = {}
    self.all_nodes = [self.entity]
    self.ady_matrix = []
    self.neighbors = asoc_nodes
    self.neighbors_niknames = self.neighbors.keys() if self.neighbors != None else []
    self.build_topo_package()
    self.short_matrix = None
    self.static_neighbors = self.neighbors_niknames


  def send_hello(self, hto, hfrom):
    self.send_message(hto, "<hello>", mfrom=hfrom)
    print("Mandando hello al vecino")

  def eco(self, eco_to, eco_from):
    self.send_message(
      mto=eco_to,
      mbody="<eco time='%f'></eco>" % time(),
      mfrom=eco_from
    )
      

  def build_topo_package(self):
    self.LSA['node'] = self.entity
    self.LSA['seq'] = self.LSA_seqnum
    self.LSA['age'] = None
    self.LSA['weights'] = {}
    print("Vecinos", self.neighbors_niknames)
    for node in self.neighbors_niknames:
      self.LSA['weights'][node] = 5
    self.topo[self.LSA['node']] = self.LSA
      

  def update_topo_package(self, node, weight):
    self.LSA['weights'][node] = weight
  

  def send_topo_package(self, to):
    self.LSA_seqnum += 1
    self.LSA['seq'] = self.LSA_seqnum
    self.LSA['age'] = time()
    self.topo[self.LSA['node']] = self.LSA
    lsa_json = json.dumps(self.LSA)
    self.send_message(to, "<pack lsa='%s'></pack>" % lsa_json, mfrom=self.boundjid)
      
  
  def shortest_path(self):
    path = []
    return path.reverse()

  def dijkstra(self):
    if len(self.ady_matrix) >= 1:
      D, Pr = shortest_path(
        self.ady_matrix, 
        directed=True, 
        method='D', 
        return_predecessors=True)
      self.short_matrix = Pr

  async def update_tables(self):
    while True:
      for router in self.neighbors_niknames:
        self.eco(self.neighbors[router], self.boundjid)
      await asyncio.sleep(5)
      for router in self.neighbors_niknames:
        self.send_topo_package(self.neighbors[router])
      self.dijkstra()
              

  def get_nickname(self, userid):
    key_list = list(self.neighbors.keys())
    if userid not in self.neighbors.values():
      return 
    val_list = list(self.neighbors.values())
    return key_list[val_list.index(userid)]


  def init_listener(self):
    self.loop.create_task(self.update_tables())

  def flood(self, to, package):
    self.send_message(to, "<pack lsa='%s'></pack>" % package, mfrom=self.boundjid)

  def send_msg(self, to, msg):
    path = self.get_shortest_path(to)
    print("%s: el camino mas corto: %s" %(self.entity,path))
    if len(path) > 1:
      self.send_message(
        mto=self.neighbors[path[1]],
        mbody="<msg chat='%s' to='%s' ></msg>" %(msg, to),
        mfrom=self.boundjid
      )



  def update_ady_matrix(self):
    length = len(self.all_nodes)
    self.ady_matrix = np.zeros((length, length), dtype=np.float16)
    for row_node in self.all_nodes:
      for col_node in self.topo[row_node]['weights'].keys():
        row = self.all_nodes.index(row_node)
        if col_node in self.all_nodes:
          col = self.all_nodes.index(col_node)
        else:
          return
        self.ady_matrix[row][col] = self.topo[row_node]['weights'][col_node]

  def parse_path(self, path):
    return [self.all_nodes[i] for i in path]
    
  
  def get_shortest_path(self, destiny): #should be a character
    _from = self.all_nodes.index(self.entity)
    destiny = self.all_nodes.index(destiny)
    path = [destiny]
    k = destiny
    while self.short_matrix[_from, k] != -9999:
      path.append(self.short_matrix[_from, k])
      k = self.short_matrix[_from, k]
    return self.parse_path(path[::-1]) 
        

  async def message(self, msg):
    if msg['type'] in ('normal', 'chat'):
      if msg['body'][:7] in ("<hello>"):
        msg.reply(self.boundjid).send()
        print("Recibido hello del vecino, enviando respuesta")
      elif msg['body'][1:4] == "eco":
        xml_parse = ET.fromstring(msg['body'])
        timestamp = float(xml_parse.attrib['time'])
        if self.is_offline:
          timestamp -= 100
        msg.reply("<a_eco time='%s'></a_eco>" % str(timestamp)).send()
      elif msg['body'][1:6] == "a_eco":
        pack_from = msg['from'].bare
        node_entity = self.get_nickname(pack_from)
        end_time = time()
        msg_parse = ET.fromstring(msg['body'])
        start_time = float(msg_parse.attrib['time'])
        delta_time = (end_time - start_time) / 2
        delta_time = round(delta_time, 1)
        self.update_topo_package(node_entity, delta_time)
      elif msg['body'][1:5] == "pack":
        parse = ET.fromstring(msg['body'])
        pack_json = parse.attrib['lsa']
        lsa = json.loads(pack_json)
        n_entity = lsa['node']
        if lsa['node'] not in self.topo.keys():
          self.topo[lsa['node']] = lsa
          for neighbor in self.neighbors_niknames:
            if neighbor != n_entity:
              self.flood(self.neighbors[neighbor], json.dumps(lsa))
          if lsa['node'] not in self.all_nodes:
            self.all_nodes.append(lsa['node'])
            self.all_nodes.sort()
          self.update_ady_matrix() 
        else:
          try:
            d_time = float(lsa['age']) - float(self.topo[lsa['node']]['age']) 
          except TypeError as e:
            pass
          if self.topo[lsa['node']]['seq'] >= lsa['seq']:
            if d_time > DEAD:
              self.topo[lsa['node']] = lsa
              for neighbor in self.neighbors_niknames:
                if neighbor != n_entity:
                  self.flood(self.neighbors[neighbor], json.dumps(lsa))
            else:
              pass
          else:
            self.topo[lsa['node']] = lsa
            for neighbor in self.neighbors_niknames:
              if neighbor != n_entity:
                self.flood(self.neighbors[neighbor], json.dumps(lsa))
            self.update_ady_matrix()
        # print("Esta es la topologia por el momento: \n", self.ady_matrix)

      elif msg['body'][1:4] == "msg":
        msg_parse = ET.fromstring(msg['body'])
        bare_msg = msg_parse.attrib['chat']
        msg_to = msg_parse.attrib['to']
        if msg_to != self.entity:
          self.send_msg(msg_to, bare_msg)
        else:
          print("Mensajes recibidos: %s" % bare_msg)
      else:
        pass
