import asyncio
import logging
import slixmpp
from aioconsole import aprint
import xml.etree.ElementTree as ET
from slixmpp.exceptions import IqError, IqTimeout


class Nodo(slixmpp.ClientXMPP):
  def __init__(self, userid, password, nickname=None, newUserid=False, t_keys=None):
    super().__init__(userid, password)
    if not nickname:
      self.nick = userid.split('@')[0]
    else:
      self.nick = nickname
    
    self.connected_event = asyncio.Event()
    self.topo_keys = t_keys

    self.add_event_handler('session_start', self.sessionStart)
    self.add_event_handler('message', self.message)
    self.add_event_handler('register', self.registrar)
    self.add_event_handler('got_offline', self.node_disconnected)
    
    self.register_plugin('xep_0030')
    self.register_plugin('xep_0045')
    self.register_plugin('xep_0004')
    self.register_plugin('xep_0060')
    self.register_plugin('xep_0199')

    if newUserid:
      self.register_plugin('xep_0077')
      self.register_plugin('xep_0004')
      self.register_plugin('xep_0066')
      self['xep_0077'].force_registration = True
    self.is_offline = False

  async def registrar(self, iq):
    resp = self.Iq()
    resp['type'] = 'set'
    resp['register']['username'] = self.boundjid.user
    resp['register']['password'] = self.password

    try:
      await resp.send()
      logging.info("Account created for %s!" % self.boundjid)
    except IqError as e:
      logging.error("Could not register account: %s" % e.iq['error']['text'])
      self.disconnect()
    except IqTimeout:
      logging.error("No response from server.")
      self.disconnect()

  async def sessionStart(self, event):
    try:
      self.send_presence()
      await self.get_roster()
      self.connected_event.set()
    except IqError as err:
      print('Error: %s' % err.iq['error']['condition'])
    except IqTimeout:
      print('Error: Request timed out')

  
  async def message(self, msg):
    if msg['type'] in ('normal', 'chat'):
      await aprint("\n{}".format(msg['body']))

  def node_disconnected(self, e):
    print('El siguiente nodo {} esta fuera de servicio'.format(e['from'].bare))
      
