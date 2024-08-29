from core.application import Application
from core.plugins.plugin import Plugin
from core.types import ControllerModule
from plugins.liveapi.decorators.event import LiveEvent
from plugins.liveapi.engines.socketio import SocketIOEngine
from plugins.liveapi.error import ErrorHandler
from plugins.liveapi.handler import SIOHandler


class LiveAPIPlugin(Plugin):
    name: str = "live-api"
    description: str = "Plugin for Live API communication"

    def __init__(self, use_identity: bool, location: str = "/ws",
                 engine: str = "socketio", cors_allowed_origins: list[str] = ["*"],
                 main_controller: str = "main") -> None:
        self.use_identity = use_identity
        self.location = location
        self.engine = engine
        self.cors_allowed_origins = cors_allowed_origins
        self.main_controller = main_controller
    
    def install(self, application: Application, *args, **kwargs):
        self.logger.info("Running live-api plugin, mounting SocketIO into Ascender Framework's Core...")
        self._application = application
        self._application.app.add_event_handler("startup", self.on_server_start)

        self.initialize_engine()
        self.logger.info("[green]Successfully mounted Socket IO engine into Ascender Framework's core [/green]")

    def initialize_engine(self):
        engine = SocketIOEngine(self._application.app,
                                self.location, self.cors_allowed_origins)
        self._application.service_registry.add_singletone(SocketIOEngine, engine)
        self.logger.debug("Running SocketIO engine...")
        self.logger.info("Mounting SocketIO with `{location}` location".format(location=self.location))
        self._application.service_registry.add_singletone(ErrorHandler, ErrorHandler(self.logger))

        self.handler = SIOHandler(engine, logger=self.logger)
    
    def on_server_start(self):
        self.handler.run_listeners()

    def after_controller_load(self, name: str, instance: object, configuration: ControllerModule):
        methods = [func for func in dir(instance) if callable(getattr(instance, func)) and not func.startswith("__")]
        _has_listener = False

        for method in methods:
            func = getattr(instance, method)
            if getattr(func, "_listener_metadata", None):  # Check if it's an instance of the decorator class
                if not _has_listener:
                    _has_listener = True

                metadata = func._listener_metadata
                self.handler.add_listener(func, metadata["event_name"], metadata["dependencies"], metadata["namespace"])
        
        if _has_listener:
            self.logger.info(f"Controller [green]{name}[/green] has been successfully mounted to SocketIO")