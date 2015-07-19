import pygame

class TextBox(object):
	def __init__(self, prompt=">> ", fontsize=14, size=50, bgcolor=(50,0,0), framecolor=(100,0,0), textcolor=(255,255,255), select=pygame.K_TAB):
		self.prompt=prompt
		self.bgcolor=bgcolor
		self.framecolor=framecolor
		self.textcolor=textcolor
		self.text=""
		self.buf=[]
		self.font=pygame.font.SysFont('monospace', fontsize)
		self.size=self.font.size("A"*size)
		self.select=select
		self.enabled=False

	def update(self, event):
		try:
			if event.type==pygame.KEYDOWN:
				if self.enabled:
					if event.unicode.upper() in "QWERTYUIOPLKJHGFDSAZXCVBNM[]{};':\",./<>?`1234567890-=~!@#$%^&*()_+\\| ":
						self.text+=event.unicode
					elif event.key==pygame.K_BACKSPACE:
						self.text=self.text[:-1]
					elif event.key==pygame.K_RETURN:
						self.buf.append(self.text)
						self.text=""
						self.enabled=False
					elif event.key==self.select:
						self.enabled=False
				elif event.key==self.select:
					self.enabled=True
		except AttributeError:
			pass

	def render(self, screen, pos):
		pygame.draw.rect(screen, self.framecolor, pygame.Rect(pos[0]-3, pos[1]-3, self.size[0]+6, self.size[1]+6))
		pygame.draw.rect(screen, self.bgcolor, pygame.Rect(pos[0], pos[1], self.size[0], self.size[1]))
		screen.blit(self.font.render((self.prompt if self.enabled else "")+self.text, True, self.textcolor), pos)

class IngameRenderedConsole:
	#Line tuple is (text, color, bgcolor, bold, italics, underline)
	def __init__(self, screen, lines=3, width=50):
		self.screen=screen
		self.lines=[]
		self.enabled=True
		self.debug=False
		self.maxlines=lines
		self.width=width
		self.font=pygame.font.SysFont('monospace', 14)

		#self.post("Console Started")

	def enable(self):
		self.enabled=True

	def disable(self):
		self.enabled=False

	def enable_debug(self):
		self.debug=True

	def disable_debug(self):
		self.debug=False

	def render_line(self, line, offset):
		self.font.set_bold(line[3])
		self.font.set_italic(line[4])
		self.font.set_underline(line[5])
		self.screen.blit(self.font.render(
				line[0], False, pygame.Color(*line[1]), pygame.Color(*line[2]) if line[2] else None
			)
		, offset)
		self.font.set_bold(False)
		self.font.set_italic(False)
		self.font.set_underline(False)

	def render(self, position):
		position=list(position)
		pygame.draw.rect(self.screen, (0,50,0), pygame.Rect(
			position,
			(self.font.size("A"*self.width)[0]+6,
			self.font.size("A")[1]*self.maxlines)
			)
		)
		# pygame.draw.rect(self.screen, (255,255,255), pygame.Rect(
		# 	position[0]-2,
		# 	position[1]-2,
		# 	self.font.size("A")[0]*self.width,
		# 	self.font.size("A")[1]*self.maxlines+4
		# 	),
		# 	3
		# )
		if self.enabled:
			for l in self.lines:
				self.render_line(l, position)
				position[1]+=self.font.size(l[0])[1]

	def post(self, text, color=(255,255,255,255), bg=(0,50,0), bold=False, italic=False, underline=False, debugmsg=False):
		if not debugmsg or self.debug:
			#debug("Message posted")
			self.lines.append((text, color, bg, bold, italic, underline))
			if len(self.lines)>self.maxlines:
				del self.lines[0]