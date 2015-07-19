from __future__ import division
import struct, model, loader, random, servercommands

#                              usrID msgID ts left right jetpack jump suck gun blow MouseX MouseY UsrName ChatMsg
controls_struct=struct.Struct("I     I     f  ?    ?     ?       ?    ?    ?   ?    f      f      10s     50s")

class ControlsFrame(object):
	def __init__(self, datagram):
		self.uid, self.idx, self.departure_ts,\
		self.left, self.right, self.jetpack, self.jump, \
		self.suck, self.gun, self.blow, self.mousex, self.mousey, self.usrname, self.chatmsg = controls_struct.unpack(datagram)

		self.usrname, self.chatmsg = self.usrname.replace('\0',''), self.chatmsg.replace('\0','')
		self.jumped=False
	
	def set_prevframe(self, prevframe):
		self.prevframe=prevframe

		self.jumped = (self.prevframe.jump==0 and self.jump) if self.prevframe else False

class ClientData(object):
	def __init__(self, game, uid, player_entity):
		self.current_idx=-1
		self.current_frame=None
		self.uid=uid
		self.player_entity=player_entity
		self.game=game
		self.outgoing_chat_buffer=[]
		self.dead=False
		self.available_commands=[x for x in dir(servercommands) if not x.startswith("__")]

		self.last_bullet_fired=0

	def process_frame(self, frame):
		if frame.uid==self.uid:
			if frame.idx>self.current_idx:
				if self.current_frame:
					frame.set_prevframe(self.current_frame)
				self.current_frame=frame
				self.current_idx=frame.idx
				
				if frame.chatmsg:
					if frame.chatmsg.startswith("/"):
						self.process_chat_message(frame.chatmsg.replace("/","",1))
					else:
						self.game.post_chat_message(frame.usrname, frame.chatmsg)
				if not self.dead:
					self.player_entity.label=frame.usrname
			else:
				print "Out of order ControlsFrame, "+str(frame.idx)+"<"+str(self.current_idx)

	def update(self, dt):
		if not self.dead:
			if self.current_frame:
				self.act(self.current_frame, dt)
			if self.player_entity.kill:
				self.dead=True
				self.game.post_chat_message("SERVER", self.player_entity.label+" was killed by "+self.player_entity.last_damage)
				self.player_entity=None

	def act(self, frame, dt):
		self.last_bullet_fired+=dt

		if frame.jump and self.player_entity.on_ground:
			self.player_entity.vel_y=-80

		if frame.left:
			self.player_entity.vel_x=-65

		if frame.right:
			self.player_entity.vel_x=65

		if frame.gun and self.player_entity.energy>=loader.assets("gun")["fire_cost"] and self.last_bullet_fired>loader.assets("gun")["fire_cooldown"]:
			e=model.Entity.from_json(self.game, None, loader.assets("gunbullet1"))
			mult=loader.assets("gun")["bullet_speed"]/(abs(frame.mousex-self.player_entity.x)+abs(frame.mousey-self.player_entity.y))
			e.vel_x=(frame.mousex-self.player_entity.x)*mult
			e.vel_y=(frame.mousey-self.player_entity.y)*mult
			e.x, e.y = self.player_entity.rect.center
			e.parent=self.player_entity.eid
			self.game.entities[e.eid]=e
			self.player_entity.energy-=loader.assets("gun")["fire_cost"]
			self.last_bullet_fired=0

		self.player_entity.joulegun_target=0
		if frame.suck or frame.blow:
			mouse_target=None
			for e in self.game.entities.values():
				if e.rect.collidepoint((frame.mousex, frame.mousey)):
					if isinstance(e, model.JouledEntity):
						mouse_target=e

			flow_rate=20*dt
			if mouse_target:
				# if frame.suck and mouse_target.energy>=flow_rate and self.player_entity.energy<=self.player_entity.energy_max:
				# 	mouse_target.energy-=flow_rate
				# 	self.player_entity.energy+=flow_rate
				# 	self.player_entity.sucking=True
				# 	self.player_entity.joulegun_target=mouse_target.eid

				# if frame.blow and self.player_entity.energy>=flow_rate and mouse_target.energy<=mouse_target.energy_max:
				# 	mouse_target.energy+=flow_rate
				# 	self.player_entity.energy-=flow_rate
				# 	self.player_entity.sucking=False
				# 	self.player_entity.joulegun_target=mouse_target.eid

				if frame.suck and mouse_target.energy>0 and self.player_entity.energy<self.player_entity.energy_max:
					mouse_target.energy-=flow_rate
					self.player_entity.energy+=flow_rate
					self.player_entity.sucking=True
					self.player_entity.joulegun_target=mouse_target.eid

					if mouse_target.energy<0:
						self.player_entity.energy+=mouse_target.energy
						mouse_target.energy=0
					if self.player_entity.energy>self.player_entity.energy_max:
						mouse_target.energy+=self.player_entity.energy-self.player_entity.energy_max

				elif frame.blow and self.player_entity.energy>0 and mouse_target.energy<mouse_target.energy_max:
					mouse_target.energy+=flow_rate
					self.player_entity.energy-=flow_rate
					self.player_entity.sucking=False
					self.player_entity.joulegun_target=mouse_target.eid

					if self.player_entity.energy<0:
						mouse_target.energy+=self.player_entity.energy
						self.player_entity.energy=0
					if mouse_target.energy>mouse_target.energy_max:
						self.player_entity.energy+=mouse_target.energy-mouse_target.energy_max

		self.player_entity.jetpacking=False
		if frame.jetpack:
			rate = loader.assets("jetpack")["accel"]*dt
			cost = rate*loader.assets("jetpack")["ratio"]
			if self.player_entity.energy>=cost:
				self.player_entity.jetpacking=True
				self.player_entity.energy-=cost
				self.player_entity.vel_y-=rate
				

	def process_chat_message(self, message):
		cmd=message.split(" ")[0]
		if cmd in self.available_commands:
			getattr(servercommands, cmd)(self, message)
		else:
			self.outgoing_chat_buffer.append(["[ERROR] Command not found", "SERVER"])