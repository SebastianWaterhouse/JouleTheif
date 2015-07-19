import lobby, loader

loader.assets.load_dir("assets_shared")

server=lobby.LobbyServer(loader.assets("baseserver"))
server.loop()