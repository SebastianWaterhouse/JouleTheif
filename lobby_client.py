import lobby, pygame

pygame.init()
screen=pygame.display.set_mode((600,400))

client=lobby.LobbyClient(('localhost', 1442), screen, "Louis")

while True:
	screen.fill((0,0,0))
	client.render()
	pygame.display.flip()

	for e in pygame.event.get():
		if e.type==pygame.QUIT:
			pygame.quit()
