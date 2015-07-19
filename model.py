from __future__ import division
import struct, loader, pygame, random, util

#    						 eid typeid static collide x y width height xvel yvel label art
entity_struct=struct.Struct("I   I      ?      ?       I I I     I      i    i    10s   15s")
entity_struct_maxsize=128

def construct_entity(game, typeid, datagram=None, eid=None):
	return typeid_mapping[typeid](game, eid, datagram)

class Entity(object):
	def __init__(self, game, eid=None, datagram=None):
		self.game=game
		self.eid=eid if eid else random.randint(0,99999)

		self.x=0
		self.y=0
		self.art="NONE"
		self.label=""
		self.vel_x=0
		self.vel_y=0
		self.width=0
		self.height=0
		self.typeid=0
		self.collide=True

		self.on_ground=True

		self.lock=util.ContextManagerLock()

		self.static=False

		self.kill=False
		self.missedframe=0

		self._init()
		
		if datagram:
			self.recv_data(datagram)

	def _init(self):pass
	def _update(self, dt):pass
	def _render(self):pass

	@staticmethod
	def from_json(game, eid, data):
		self = construct_entity(game, data["typeid"], eid=eid)

		for k, v in data.iteritems():
			setattr(self, k, str(v) if type(v)==unicode else v)

		return self

	def load_additional(self, datagram):
		pass

	def pack_additional(self):
		return ""

	@property
	def rect(self):
		return pygame.Rect(self.x, self.y, self.width, self.height)

	def recv_data(self, datagram):
		with self.lock:
			self.eid, _, self.static, self.collide, self.x, self.y, self.width, self.height, self.vel_x, self.vel_y, self.label, self.art = entity_struct.unpack(datagram[:entity_struct.size])
			self.art=self.art.replace('\0','')
			self.label=self.label.replace('\0','')
			self.load_additional(datagram[entity_struct.size:])

	def pack_data(self):
		assert len(self.art)<16, "Art asset "+self.art+" has too long of a name. Must be under 16 chars"
		if self.x<0:self.x=0
		if self.y<0:self.y=0
		# print repr((self.eid, self.x, self.y, self.width, self.height, self.vel_x, self.vel_y, str(self.art)))
		# import time
		# time.sleep(0.5)
		return entity_struct.pack(self.eid, [k for k in typeid_mapping.keys() if typeid_mapping[k]==type(self)][0],
			self.static, self.collide, self.x, self.y, self.width, self.height, self.vel_x, self.vel_y, 
			str(self.label), str(self.art))+self.pack_additional()

	def update(self, dt):
		with self.lock:
			if not self.static:
				self.on_ground=False
				self.colliding=False
				self.x+=self.vel_x*dt

				tr=self.rect
				for entity in self.game.entities.values():
					if entity.rect.colliderect(tr) and entity.eid!=self.eid and entity.collide:
						if self.vel_x>0:
							tr.right=entity.rect.left
						if self.vel_x<0:
							tr.left=entity.rect.right
						self.x = tr.left
						self.vel_x=0
						self.colliding=entity.eid

				self.y+=self.vel_y*dt

				tr=self.rect
				for entity in self.game.entities.values():
					if entity.rect.colliderect(tr) and entity.eid!=self.eid and entity.collide:
						if self.vel_y>0:
							tr.bottom=entity.rect.top
							self.on_ground=True
						if self.vel_y<0:
							tr.top=entity.rect.bottom
						self.y = tr.top
						self.vel_y=0
						self.colliding=entity.eid

				self._update(dt)

	def render(self):
		with self.lock:
			if self.art!="NONE":self.game.graphics.blit(loader.assets(self.art), (self.x, self.y))
			if self.label: self.game.graphics.blit(pygame.font.SysFont('monospace', 13, bold=True).render(self.label, 1, (255,255,255) if self.eid !=self.game.player else (0,255,0)), (self.x, self.y-28))
			self._render()

class JouledEntity(Entity):
	je_struct=struct.Struct("I I I I I I ? ?")
	def _init(self):
		self.energy = self.energy_max = self.energy_regen = self.joulegun_target = self.hp = self.hp_max = 0
		self.sucking = False
		self.jetpacking = False
		self.last_damage = ""

	def pack_additional(self):
		self.hp=max(0, self.hp)
		return self.je_struct.pack(self.energy, self.energy_max, self.energy_regen, self.joulegun_target, self.hp, self.hp_max, self.sucking, self.jetpacking)

	def load_additional(self, dg):
		self.energy, self.energy_max, self.energy_regen, self.joulegun_target, self.hp, self.hp_max, self.sucking, self.jetpacking = self.je_struct.unpack(dg)

	def _update(self, dt):
		self.vel_y+=52*dt
		self.vel_x+=-5 if self.vel_x>1 else 5
		if abs(self.vel_x)<20:
			self.vel_x=0

		self.energy+=self.energy_regen*dt
		self.round_energy()

		if self.hp<=0:
			self.kill=True



	def round_energy(self):
		if self.energy>self.energy_max:
			self.energy=self.energy_max

	def _render(self):
		if self.energy_max != 0:
			pygame.draw.rect(self.game.graphics, (0,0,255), pygame.Rect(self.x, self.y-16, (self.width/self.energy_max)*self.energy, 8))
			self.game.graphics.blit(pygame.font.SysFont('',12).render(str(int(self.energy))+'/'+str(self.energy_max), True, (255,0,255)), (self.x, self.y-16))
		if self.hp_max != 0:
			pygame.draw.rect(self.game.graphics, (100,0,0), pygame.Rect(self.x, self.y-8, (self.width/self.hp_max)*self.hp, 8))
			self.game.graphics.blit(pygame.font.SysFont('',12).render(str(int(self.hp))+'/'+str(self.hp_max), True, (255,255,0)), (self.x, self.y-8))

		if self.jetpacking:
			self.game.particle_manager.make_jet_trail(1, self.rect.centerx, self.rect.bottom-self.height/4)

		if self.joulegun_target:
			pygame.draw.line(self.game.graphics, (255,0,0) if self.sucking else (0,255,0), self.rect.topleft, self.game.entities[self.joulegun_target].rect.topleft, 3)

class Projectile(Entity):
	p_struct=struct.Struct("I")
	def _init(self):
		self.collide=False
		self.damage=0
		self.knockback_mult=0.1

	def update(self, dt):
		with self.lock:
			if not self.static:
				self.colliding=False
				self.x+=self.vel_x*dt
				self.y+=self.vel_y*dt

				for entity in self.game.entities.values():
					if entity.rect.colliderect(self.rect) and entity.eid!=self.eid and entity.collide:
						if entity.eid!=self.parent:
							self.colliding=True
							self.kill=True
							if isinstance(entity, JouledEntity):
								entity.hp-=self.damage
								entity.last_damage=self.game.entities[self.parent].label
								entity.vel_x+=self.vel_x*self.knockback_mult
								entity.vel_y+=self.vel_y*self.knockback_mult

	def pack_additional(self):
		return self.p_struct.pack(self.parent)

	def load_additional(self, dg):
		self.parent = self.p_struct.unpack(dg)[0]

	def _render(self):
		if self.colliding:
			self.game.particle_manager.make_explosion(100, self.x, self.y)
		self.game.particle_manager.make_blue_trail(8, *self.rect.center)

class CollidesWhenFull(JouledEntity):
	def update(self, dt):
		if self.energy>self.energy_max-0.5:
			self.collide=True
		else:
			self.collide=False

	def _render(self):
		if self.energy_max != 0:
			pygame.draw.rect(self.game.graphics, (0,0,255), pygame.Rect(self.x, self.y-16, (self.width/self.energy_max)*self.energy, 8))
			self.game.graphics.blit(pygame.font.SysFont('',12).render(str(int(self.energy))+'/'+str(self.energy_max), True, (255,0,255)), (self.x, self.y-16))
		if self.collide:
			pygame.draw.rect(self.game.graphics, (255,0,0), self.rect)

class Spikes(Entity):

	def _init(self):
		self.damage=0
		self.collide=False

	def update(self, dt):
		with self.lock:
			for entity in self.game.entities.values():
				if entity.rect.colliderect(self.rect) and entity.eid!=self.eid and entity.collide:
					if isinstance(entity, JouledEntity):
						entity.hp-=self.damage*dt
						entity.last_damage="Spikes"

typeid_mapping={
	0:Entity,
	1:JouledEntity,
	2:Projectile,
	3:CollidesWhenFull,
	4:Spikes
}