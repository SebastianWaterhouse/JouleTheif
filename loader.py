import os, pygame, json

class GameDatabase(object):
	def __init__(self):
		self.assets={}

	def load_image(self, name, tags, fqfn):
		i=pygame.image.load(fqfn)
		if "alpha" in tags:
			i=i.convert_alpha()
		elif "ccwhite" in tags:
			i.set_colorkey((255,255,255))
		self.assets[name]=i

	def load_text(self, name, tags, fqfn):
		with open(fqfn, 'r') as fd:
			self.assets[name]=fd.read()

	def load_json(self, name, tags, fqfn):
		with open(fqfn, 'r') as fd:
			self.assets[name]=json.load(fd)

	def load_dir(self, dirn):
		for fn in os.listdir(dirn):
			segs=fn.split(".")
			name=segs[0]
			tags=segs[1:]
			fqfn=dirn+"/"+fn
			if tags[-1] in ["jpg", "jpeg", "png"]:
				self.load_image(name, tags, fqfn)
			elif tags[-1] in ["txt"]:
				self.load_text(name, tags, fqfn)
			elif tags[-1] in ["json", "pfab", "ent", "cfg"]:
				self.load_json(name, tags, fqfn)

	def get_asset(self, name):
		return self.assets[name]

	def __call__(self, *a):
		return self.get_asset(*a)

assets=GameDatabase()