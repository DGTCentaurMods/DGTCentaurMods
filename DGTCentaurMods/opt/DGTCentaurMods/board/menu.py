from DGTCentaurMods.board import board, centaur
from DGTCentaurMods.display import epaper

import os, sys
import pathlib
import json
import threading
import importlib

statusbar = epaper.statusBar()

class MenuSystem:
    def __init__(self):
        #self.statusbar = epaper.statusBar()
        self.key = threading.Event()
        self.screen = epaper.MenuDraw()
        board.subscribeEvents(self.key_press, self.field)
        with open(centaur.dgtcm_path() + '/menu/menu.json') as f:
            self.menu = json.load(f)
        self.history = []

    def get_items(self, level):
        self.items = []
        self.index = 0
        menu_title, self.item_list = level['title'],[]
        self.keys = []
        for item in level['items']:
            k = level['items'][item]
            self.keys.append(item)
            if isinstance(k, dict):
                self.items.append(k)
        for i in range(len(self.items)):
            title = self.items[i]['title']
            self.item_list.append(title)
        print('Total items:',len(self.item_list))
        self.screen.draw_page(menu_title,self.item_list)
        self.screen.highlight(0)


    def select(self, index):
        # If this is a submenu - get the items and display
        if self.items[self.index]['type'] == 'menu':
            self.history.append(self.items[index])
            self.get_items(self.items[index])
        elif self.items[self.index]['type'] == 'dynamic-menu':
            dynamic_menu = {}
            menu_file = importlib.import_module('menu.' + self.keys[self.index])
            self.get_items(menu_file.build())
        # If other types - add here what to do
        elif self.items[self.index]['type'] == 'script':
            statusbar.stop()
            board.pauseEvents()
            epaper.loadingScreen()
            print('Executing:',self.items[self.index]['path'])
            os.system(str(sys.executable) + " " + str(pathlib.Path(__file__).parent.resolve()) + self.items[self.index]['path']) 
            board.unPauseEvents()
            statusbar.start()
            self.mainmenu()
        elif self.items[self.index]['type'] == 'item-file':
            # Start an item file in menu/items called as the dict key
            print('Execute: menu/items/' + self.keys[index])
            exec(open('menu/items/' + self.keys[index]).read())
        elif self.items[self.index]['type'] == 'function':
            function = self.items[self.index]['func']
            print('Command: ' + function)
            exec(command)

    def key_press(self, id):
        if id == board.BTNTICK:
            if not self.welcome:
                self.select(self.index)
            else:
                self.key.set()
                self.welcome = False
                return
        if not self.welcome:
            if id == board.BTNUP:
                if self.index > 0:
                    self.index -= 1
                    print('UP:', self.index)
                    self.screen.highlight(self.index)
                elif self.index == 0:
                    self.index = len(self.items) - 1
                    print('UP:', self.index)
                    self.screen.highlight(self.index)
                return
            if id == board.BTNDOWN:
                if self.index < len(self.items) - 1:
                    self.index += 1
                    print('DOWN:',self.index)
                    self.screen.highlight(self.index)
                elif self.index == len(self.items) - 1:
                    self.index = 0
                    print('DOWN:',self.index)
                    self.screen.highlight(self.index)
                return
            if id == board.BTNBACK:
                if len(self.history)  == 1:
                    self.get_items(self.history[-1])
                else:
                    self.history.pop()
                    self.get_items(self.history[-1])


    def field(self, field):
        """ Placeholder so eventThread() won't break """
        pass


    def mainmenu(self):
        self.level = self.menu['mainmenu']
        self.get_items(self.level)
        

    def main(self):
        epaper.welcomeScreen()
        self.welcome = True
        self.key.wait()
        # Show main menu
        self.level = self.menu['mainmenu']
        self.get_items(self.level)
        self.history.append(self.menu['mainmenu'])

