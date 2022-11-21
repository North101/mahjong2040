import socket

from mahjong2040.packets import (ConfirmWindServerPacket,
                                 NotEnoughPlayersServerPacket, Packet,
                                 SelectWindClientPacket,
                                 SelectWindServerPacket, send_msg)
from mahjong2040.shared import GamePlayerTuple, GameState, Wind

from .base import ServerState
from .game import GameServerState
from .shared import GamePlayer


class GameSetupServerState(ServerState):
  def __init__(self, server):
    super().__init__(server)

    self.players: list[socket.socket] = []
    self.ask_next_wind()

  def ask_next_wind(self):
    wind = len(self.players)
    packet = SelectWindServerPacket(wind).pack()
    for client in self.clients:
      if client not in self.players:
        send_msg(client, packet)

  def on_client_disconnect(self, client: socket.socket):
    super().on_client_disconnect(client)

    if client in self.clients:
      if not self.enough_players():
        return self.to_lobby()
    elif client in self.players:
      player_index = self.players.index(client)
      self.players.remove(client)
      if not self.enough_players():
        return self.to_lobby()

      if player_index < len(self.players):
        self.players = []

      self.ask_next_wind()

  def on_client_packet(self, client: socket.socket, packet: Packet):
    if isinstance(packet, SelectWindClientPacket):
      if packet.wind != len(self.players) and client not in self.players:
        return

      self.players.append(client)
      send_msg(client, ConfirmWindServerPacket(packet.wind).pack())

      if len(self.players) == len(Wind):
        self.child = GameServerState(
            server=self.server,
            game_state=GameState(
                players=GamePlayerTuple(
                    GamePlayer(self.players[0], 25000),
                    GamePlayer(self.players[1], 25000),
                    GamePlayer(self.players[2], 25000),
                    GamePlayer(self.players[3], 25000),
                ),
            ),
        )
      else:
        self.ask_next_wind()

  def enough_players(self):
    return len(self.clients) >= len(Wind)

  def to_lobby(self):
    from .lobby import LobbyServerState

    packet = NotEnoughPlayersServerPacket().pack()
    for client in self.clients:
      send_msg(client, packet)
    self.child = LobbyServerState(self.server)