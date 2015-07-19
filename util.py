import threading

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