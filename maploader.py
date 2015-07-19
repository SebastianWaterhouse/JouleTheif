import pytmx, pygame, model, loader
import pytmx.util_pygame

def load_entity(obj, game, layer):
	e=model.Entity.from_json(game, None, loader.assets(obj.proto))
	e.x=obj.x
	e.y=obj.y
	e.width=obj.width
	e.height=obj.height
	return e

def load_map(tmx_data, game, render_map, load_entities):
	if render_map:
		surf=pygame.Surface((tmx_data.width * tmx_data.tilewidth, tmx_data.height * tmx_data.tileheight))

		if tmx_data.background_color:
			surf.fill(pygame.Color(tmx_data.background_color))

	for layer in tmx_data.visible_layers:
		if isinstance(layer, pytmx.TiledTileLayer) and render_map:
			for x, y, image in layer.tiles():
				surf.blit(image, (x * tmx_data.tilewidth, y * tmx_data.tileheight))
		elif isinstance(layer, pytmx.TiledObjectGroup) and load_entities:
			if layer.name!="collision":
				for obj in layer:
					e=load_entity(obj, game, layer)
					game.entities[e.eid]=e
			else:
				for obj in layer:
					e=model.Entity(game)
					e.x=obj.x
					e.y=obj.y
					e.width=obj.width
					e.height=obj.height
					e.static=True
					game.entities[e.eid]=e

	if render_map: game.map_surf=surf

def load_map_fn(fn, game, render_map=0, load_entities=0):
	if render_map:
		md=pytmx.util_pygame.load_pygame(fn)
	else:
		md=pytmx.TiledMap(fn)
	load_map(md, game, render_map, load_entities)