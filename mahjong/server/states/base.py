import select
import socket
from typing import Tuple

from mahjong.packets import *
from mahjong.poll import *
from mahjong.shared import *

if TYPE_CHECKING:
  from mahjong.server import Server


class ClientMixin:
  client: socket.socket

  def send_packet(self, packet: Packet):
    send_msg(self.client, packet.pack())


class ServerState:
  def __init__(self, server: 'Server'):
    self.server = server

  @property
  def state(self):
    return self.server.state

  @state.setter
  def state(self, state: 'ServerState'):
    self.server.state = state

  @property
  def poll(self):
    return self.server.poll

  def on_server_data(self, server: socket.socket, event: int):
    if event & select.POLLIN:
      client, address = server.accept()
      self.on_client_connect(client, address)
      self.poll.register(client, select.POLLIN,
                         self.server.on_client_data)

  def on_client_data(self, client: socket.socket, event: int):
    if event & select.POLLHUP:
      self.on_client_disconnect(client)
    elif event & select.POLLIN:
      packet = read_packet(client)
      if packet is not None:
        self.on_client_packet(client, packet)

  def on_client_connect(self, client: socket.socket, address: Tuple[str, int]):
    pass

  def on_client_disconnect(self, client: socket.socket):
    self.poll.unregister(client)
    client.close()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    pass
