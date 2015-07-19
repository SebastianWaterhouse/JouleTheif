import pygame, random

# [color, x, y, sizex, sizey, xvel, yvel, ttl]

class ParticleManager(object):
	def __init__(self, screen):
		self.particles=[]
		self.clock=pygame.time.Clock()
		self.screen=screen

	def add_particles(self, p):
		self.particles.extend(p)

	def update(self):
		self.clock.tick()
		dt=1/self.clock.get_fps() if self.clock.get_fps()>10 else 0
		for particle in self.particles:
			self.screen.draw_rect(particle[0], pygame.Rect(*particle[1:5]))
			particle[7]-=dt
			particle[1]+=dt*particle[5]
			particle[2]+=dt*particle[6]
			if particle[7]<0:
				del self.particles[self.particles.index(particle)]

	def make_explosion(self, count, x, y):
		for _ in xrange(count):
			self.particles.append([(random.randint(200,255), random.randint(50,100), 0), x, y, random.randint(5,9), random.randint(5,9), random.uniform(-240,240), random.uniform(-240,240), random.uniform(0.5,1)])

	def make_blue_trail(self, count, x, y):
		for _ in xrange(count):
			w=random.randint(0,255)
			self.particles.append([(w, w, random.randint(200,255)),int(x+random.uniform(-10,10)),int(y+random.uniform(-10,10)),random.randint(3,6), random.randint(3,6), random.uniform(-5,5), random.uniform(-5,5), random.uniform(0.25,0.5)])

	def make_jet_trail(self, count, x, y):
		for _ in xrange(count):
			w=random.randint(0,255)
			self.particles.append([(random.randint(200,255), w, w),int(x+random.uniform(-10,10)),int(y+random.uniform(-10,10)),random.randint(3,6), random.randint(3,6), random.uniform(-5,5), random.uniform(-5,5), random.uniform(0.25,0.5)])