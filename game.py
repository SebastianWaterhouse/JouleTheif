import socket, struct, control, time, thread, pygame, model, random, loader, ui, particles, util

class Game(object):
	def __init__(self, (addr, port), username="", graphics=None):
		self.uid=random.randint(0,9999)
		self.entities={}
		self.graphics=graphics
		self.connect((addr, port), username)
		self.send_message_idx=0
		self.recv_message_idx=0

	def update_entities(self):
		for entity in self.entities.values():
			entity.update()

#                             msgID youare ts entity_structCount chatMsg chatFrom
state_struct = struct.Struct("I     I      l  I                  50s     10s")

class Server(Game):
	def connect(self, server_address, _):
		self.clients={}
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(server_address)

	def post_chat_message(self, username, message):
		for client in self.clients.values():
			client.outgoing_chat_buffer.append([message, username])

	def update_entities_loop(self):
		clock=pygame.time.Clock()
		while True:
			for entity in self.entities.values():
				entity.update(1/clock.get_fps() if clock.get_fps()>10 else 0)
				if entity.kill:
					del self.entities[entity.eid]

			for user in self.clients.values():
				user.update(1/clock.get_fps() if clock.get_fps()>10 else 0)

			clock.tick(40)

	def start_update_loop(self):
		thread.start_new_thread(self.update_entities_loop, ())

	def handle(self, dgram, addr):
		controls=control.ControlsFrame(dgram)
		if controls.uid not in self.clients:
			e=model.Entity.from_json(self, random.randint(0,9999), loader.assets("player"))
			self.entities[e.eid]=e
			self.clients[controls.uid]=control.ClientData(self, controls.uid, e)
			self.post_chat_message("SERVER", "Player "+controls.usrname+" has joined!")
			[self.sock.sendto(d, addr) for d in self.build_message(controls.uid, True)]
			thread.start_new_thread(self.send_loop, (controls.uid, addr))

		self.clients[controls.uid].process_frame(controls)

	def handle_loop(self):
		while True:
			try:
				self.handle(*self.sock.recvfrom(control.controls_struct.size))
			except socket.error as e:
				print e

	def send_loop(self, uid, addr):
		clock=pygame.time.Clock()
		while True:
			clock.tick(20)
			[self.sock.sendto(d, addr) for d in self.build_message(uid)]

	def start_handle_loop(self):
		thread.start_new_thread(self.handle_loop, ())

	def build_message(self, uid, include_static=False):
		buf=[]
		count=0
		for entity in self.entities.values():
			if not entity.static or include_static:
				count+=1
				buf.append(entity.pack_data())

		self.send_message_idx+=1
		buf.insert(0, state_struct.pack(self.send_message_idx, self.clients[uid].player_entity.eid if self.clients[uid].player_entity else 0, time.time(), count, *self.clients[uid].outgoing_chat_buffer.pop() if self.clients[uid].outgoing_chat_buffer else ["",""]))
		return buf

class Client(Game):
	def connect(self, server_address, username):
		self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# self.sock.bind(('localhost', random.randint(1224, 9999)))
		self.server_address=server_address
		self.username=username
		self.chat_buffer=[]
		self.input_frozen=False
		self.chatwin = ui.IngameRenderedConsole(self.graphics)
		self.ping = -1
		self.recv_rate=-1
		self.player=-1
		self.entity_lock=util.ContextManagerLock()

		self.particle_manager=particles.ParticleManager(self.graphics)

	def post_chat_message(self, username, message):
		self.chat_buffer.append(message)
	
	def build_message(self):
		self.send_message_idx+=1
		msg=self.chat_buffer.pop() if self.chat_buffer else ""
		return control.controls_struct.pack(self.uid, self.send_message_idx, time.time(),
			pygame.key.get_pressed()[pygame.K_a], pygame.key.get_pressed()[pygame.K_d],
			pygame.key.get_pressed()[pygame.K_SPACE], pygame.mouse.get_pressed()[0], pygame.mouse.get_pressed()[1],
			pygame.mouse.get_pressed()[2],
			pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], self.username, str(msg))

	def handle_loop(self):
		clock=pygame.time.Clock()
		while True:
			try:
				clock.tick()
				self.recv_rate=clock.get_fps()
				idx=False
				while not idx:
					try:
						idx, self.player, ts, count, msg, usr=state_struct.unpack(self.sock.recvfrom(state_struct.size)[0])
					except socket.error:
						self.sock.recvfrom(model.entity_struct.size)
						print "(Unaligned in handle_loop, received buffer entity_struct)"
					except struct.error:
						break
				if idx:
					self.ping=time.time()-ts
					msg, usr = msg.replace('\0',''), usr.replace('\0','')
					if idx>self.recv_message_idx:
						self.recv_message_idx=idx
						if msg:
							self.display_message(msg, usr)
						i=0
						with self.entity_lock:
							for e in self.entities.values():
								if not e.static:
									e.kill=1
							while i!=count:
								chunk=self.sock.recvfrom(model.entity_struct_maxsize)[0]
								entitydata=model.entity_struct.unpack(chunk[:model.entity_struct.size])
								if entitydata[0] in self.entities:
									self.entities[entitydata[0]].kill=0
									self.entities[entitydata[0]].recv_data(chunk)
								else:
									try:
										self.entities[entitydata[0]]=model.construct_entity(self, entitydata[1], chunk)
									except: pass
								i+=1
					else:
						self.sock.recvfrom(model.entity_struct.size*count) #Invalid order, throw away
			except socket.error as e:
				print e

	def start_handle_loop(self):
		thread.start_new_thread(self.handle_loop, ())

	def send_loop(self):
		clock=pygame.time.Clock()
		while True:
			if not self.input_frozen: self.sock.sendto(self.build_message(), self.server_address)
			clock.tick(20)

	def start_send_loop(self):
		thread.start_new_thread(self.send_loop, ())

	def display_message(self, message, user):
		self.chatwin.post(user+": "+message, color=(0,255,0) if user=="SERVER" else (255,255,255))