import socket, util, thread, pygame

class LobbyServer(object):
	def __init__(self, config):
		self.connections=[]
		self.chat_buffer=[]
		self.msg_buffer=[]
		self.run=True
		self.address=config['address']
		thread.start_new_thread(self._start_server, ())
		self.config=config
		self.adminpassword=config["adminpassword"]
		self.password=config["password"]
		del self.config["adminpassword"]
		del self.config["password"]
		self.clock=pygame.time.Clock()
		self.users_cache=[]

	def _start_server(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serversock.bind((self.address, self.config["lobby_port"]))
		serversock.listen(5)
		while self.run:
			clientsock, addr = serversock.accept()
			clientsock=util.SocketWrapper(clientsock)
			self.connections.append(clientsock)
			thread.start_new_thread(self.recv_message, (clientsock,))

	def recv_message(self, sock):
		while True:
			self.msg_buffer.append((sock, sock.recv()))

	def send(self, msg):
		[sock.send(msg) for sock in self.connections]

	def loop(self):
		while True:
			self.clock.tick(1)
			self.config["timer"]-=1

			self.config["chat_username"], self.config["chat_message"] = self.chat_buffer.pop() if self.chat_buffer else ["",""]
			self.send(self.config)

			for client, message in self.msg_buffer:
				if message["chatmessage"]:
					self.chat_buffer.append((message["username"], message["chatmessage"]))

				if message["password"]!=self.password:
					client.send({"state":True})

				if message["adminpassword"]==self.adminpassword:
					self.config.update(message["config_update"])

				if message["username"] not in self.users_cache:
					self.chat_buffer.append(("SERVER", message["username"]+" has connected!"))

class LobbyClient(object):
	def __init__(self, addr, screen, username):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect(addr)
		self.sock=util.SocketWrapper(self.sock)
		self.screen=screen
		thread.start_new_thread(self.recv_loop, ())
		self.message={}
		self.config={}
		self.chat_buffer=[]
		self.font=pygame.font.SysFont('monospace', 14)
		self.offset=self.font.size("|")[1]

	def recv_loop(self):
		while True:
			self.config = self.sock.recv()

	def render(self):
		if len(self.config.keys())>0:
			self.screen.blit(self.font.render("Title    : "+self.config["title"], 1, (255,255,255)), (0,0))
			self.screen.blit(self.font.render("MOTD     : "+self.config["motd"], 1, (255,255,255)), (0,self.offset))
			self.screen.blit(self.font.render("GameMode : "+self.config["server_config"]["gamemode"], 1, (255,255,255)), (0,self.offset*2))
			self.screen.blit(self.font.render("Map      : "+self.config["server_config"]["map"], 1, (255,255,255)), (0,self.offset*3))
			self.screen.blit(self.font.render("Timer    : "+str(self.config["timer"]), 1, (255,0,0)), (0,self.offset*5))