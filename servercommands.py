import model, random, loader
from util import must_be_alive

@must_be_alive
def fullhp(self, message):
	self.player_entity.hp=self.player_entity.hp_max

@must_be_alive
def fullenergy(self, message):
	self.player_entity.energy=self.player_entity.energy_max

@must_be_alive
def fsp(self, message):
	self.player_entity.x = int(message.split(" ")[1])
	self.player_entity.y = int(message.split(" ")[2])

def respawn(self, message):
	if not self.dead:
		self.outgoing_chat_buffer.append(["[ERROR] You are alive", "SERVER"])
	else:
		self.dead=False
		self.player_entity=model.Entity.from_json(self.game, random.randint(0,9999), loader.assets("player"))
		self.game.entities[self.player_entity.eid]=self.player_entity