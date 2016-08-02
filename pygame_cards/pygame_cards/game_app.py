#!/usr/bin/env python
try:
    import sys
    import os
    import pygame
    import threading
    import json
    import abc

    import gui

    from pygame_cards import globals
except ImportError as err:
    print "Fail loading a module: %s", err
    sys.exit(2)


class RenderThread(threading.Thread):
    """ Represents thread for rendering of game objects """

    def __init__(self, app):
        """
        :param app: object of GameApp class which sprites will be rendered
        """
        threading.Thread.__init__(self)
        self.app = app

    def run(self):
        """ Starts endless loop and renders game objects in it """
        while not self.app.stopped:
            self.app.clock.tick(300)
            self.app.render()
            pygame.display.flip()


class GameApp:
    """ Interface game app class that concrete game classes should inherit """
    __metaclass__ = abc.ABCMeta

    class GuiInterface:
        """ Inner class with GUI interface functions """
        def __init__(self, gui_json, screen):
            self.gui_json = gui_json
            self.screen = screen
            self.gui_list = []

        def show_label(self, text):
            label = gui.Title(self.screen, self.gui_json['notification_label'], text)
            self.gui_list.append(label)

        def show_button(self, text, callback):
            self.gui_list.append(gui.Button(self.screen, self.gui_json['done_button'], callback, text))

        def hide_button(self):
            pass

        def render(self):
            for g in self.gui_list:
                if hasattr(g, 'expired') and g.expired:
                        print 'removing g from gui_list'
                        self.gui_list.remove(g)
                        continue
                g.render()

        def check_mouse(self, down):
            for g in self.gui_list:
                g.check_mouse(pygame.mouse.get_pos(), down)

    def __init__(self, json_name):
        """
        :param json_name: path to configuration json file
        """
        # Windows properties that will be set in load_settings_from_json()
        self.title = None
        self.background_color = None
        self.size = None

        globals.settings_json = self.load_json(json_name)
        if globals.settings_json is None:
            raise ValueError('settings json file is not loaded', 'GameApp.__init__')
        self.load_settings_from_json()
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill(self.background_color)
        self.clock = pygame.time.Clock()
        self.render_thread = RenderThread(self)
        self.stopped = False
        self.gui_interface = None
        self.game_controller = None

    def process_events(self):
        """ Processes mouse events and quit event """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stopped = True
                self.render_thread.join()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONUP:
                self.process_mouse_event(False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.process_mouse_event(True)

    @staticmethod
    def load_json(path):
        """ Loads json file and returns handle to it
        :param path: path to json file to load
        :return: handle to loaded json file
        """
        with open(path, 'r') as json_file:
            return json.load(json_file)

    def load_settings_from_json(self):
        """ Parses configuration json file and sets properties with values from the json.
            Following window properties are set by this method:
            - Title
            - Background properties
            - Window size
            Other custom game-specific settings should be set by derived classes in load_game_settings_from_json().
        """
        self.title = globals.settings_json["window"]["title"]
        self.background_color = globals.settings_json["window"]['background_color']
        self.size = globals.settings_json["window"]["size"]

        # Following method should be overloaded in derived classes
        self.load_game_settings_from_json()

    @abc.abstractmethod
    def load_game_settings_from_json(self):
        """ Loads custom game settings from settings.json.
            Should be overloaded in derived classes.
        """
        pass

    @abc.abstractmethod
    def process_mouse_event(self, down):
        """ Abstract method for processing mouse events, should be overloaded in derived classes
        :param down: boolean, True for mouse down event, False for mouse up event
        """
        pass

    @abc.abstractmethod
    def build_game_objects(self):
        """ Abstract method to build game object. Should be defined in derived classes. """
        pass

    def init_gui(self):
        """ Initializes GUI elements from "gui" structure from settings.json """
        self.gui_interface = GameApp.GuiInterface(globals.settings_json["gui"], self.screen)

    def init_game(self):
        """ Initializes game and gui objects """
        self.init_gui()
        self.build_game_objects()

    def render(self):
        """ Renders game objects and gui elements """
        pygame.draw.rect(self.screen, self.background_color, (0, 0, self.size[0], self.size[1]))
        if self.game_controller is not None:
            self.game_controller.render_objects(self.screen)
        if self.gui_interface is not None:
            self.gui_interface.render()

    def execute_game_logic(self):
        """ Executes game logic. Should be called recurrently from the game loop """
        if self.game_controller is not None:
            self.game_controller.execute_game()

    def start_render_thread(self):
        """ Starts game rendering thread (object of RenderThread class) """
        self.render_thread.start()

    def run_game_loop(self):
        """ Runs endless loop where game logic and events processing are executed. """
        while 1:
            self.clock.tick(60)
            self.process_events()
            self.execute_game_logic()
            #self.render()

    def execute(self):
        """ Initializes game, starts rendering thread and starts game endless loop """
        self.init_game()
        self.start_render_thread()
        self.run_game_loop()