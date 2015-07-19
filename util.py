import threading, pygame

class ContextManagerLock(object):
	def __init__(self):
		self._lock=threading.Lock()

	def __enter__(self):
		self._lock.acquire()

	def __exit__(self, t, v, tr):
		self._lock.release()

def must_be_alive(func):
	def _internal(client, message):
		if not client.dead:
			func(client, message)
		else:
			client.outgoing_chat_buffer.append(["[ERROR] You are dead", "SERVER"])
	return _internal

class SocketWrapper(object):
	def __init__(self, sock):
		self.sock=sock

	def _recv_to_nul(self):
		data=""
		while 1:
			r=self.sock.recv(1)
			if r:
				if r!="\0":
					data+=r
				else:
					break
		return data

	def recv(self):
		return eval(self._recv_to_nul())

	def send(self, data):
		self.sock.sendall(repr(data)+"\0")

class ScrollingWorldManager(object):
	def __init__(self, screen, offset_x=0, offset_y=0):
		self.screen=screen
		self.offset_x=offset_x
		self.offset_y=offset_y
		self.rect=pygame.Rect((0,0), screen.get_size())
	def get_t_coords(self, pos):
		return (pos[0]-self.offset_x, pos[1]-self.offset_y)
	def get_t_rect(self, rect):
		rect=rect.copy()
		rect.topleft=self.get_t_coords(rect)
		return rect
	def blit(self, image, coords):
		new_rect=pygame.Rect((coords[0]-self.offset_x, coords[1]-self.offset_y), image.get_size())
		# if new_rect.colliderect(pygame.Rect((0,0),self.screen.get_size())):
		self.screen.blit(image, (coords[0]-self.offset_x, coords[1]-self.offset_y))
	def set_offset(self, offset):
		self.offset_x=offset[0]
		self.offset_y=offset[1]
	def draw_line(self, color, start, end, thickness=1):
		pygame.draw.line(self.screen, color, (start[0]-self.offset_x, start[1]-self.offset_y),(end[0]-self.offset_x, end[1]-self.offset_y), thickness)
	def draw_rect(self, color, rect, width=0):
		pygame.draw.rect(self.screen, color, ((rect.x-self.offset_x, rect.y-self.offset_y),rect.size), width)
	def clamp(self, rect):
		rect2=rect.copy()
		rect2.x-=self.offset_x
		rect2.y-=self.offset_y
		rect2.clamp_ip(self.screen.get_rect())
		return rect2
	def blit_clamped(self, image, rect):
		rect2=self.clamp(rect)
		self.screen.blit(image, rect2)