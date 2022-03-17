#!/usr/bin/python

from DGTCentaurMods.board import board
from DGTCentaurMods.display import epaper
import json

class MenuSystem:
    def __init__(self):
        self.screen = epaper.MenuDraw()
        board.subscribeEvents(self.key_press)
        with open('menu/menu.json') as f:
            self.menu = json.load(f)
        self.history = []

    def get_items(self, level):
        self.items = []
        self.index = 0
        menu_title, item_list = level['title'],[]
        for item in level['items']:
            k = level['items'][item]
            if isinstance(k, dict):
                self.items.append(k)
        for i in range(len(self.items)):
            title = self.items[i]['title']
            item_list.append(title)
            #print(i,title)
        print('Total items:',len(item_list))
        self.screen.draw_page(menu_title,item_list)
        self.screen.highlight(0)


    def select(self, index):
        # If this is a submenu - get the items and display
        if self.items[self.index]['type'] == 'menu':
            self.history.append(self.items[index])
            self.get_items(self.items[index])
        # If other types - add here what to do


    def key_press(self, id):
        if id == board.BTNTICK:
            self.select(self.index)
        if id == board.BTNUP:
            if self.index > 0:
                self.index -= 1
                self.screen.highlight(self.index)
                print('UP:', self.index)
        if id == board.BTNDOWN:
            if self.index < len(self.items) - 1:
                self.index += 1
                self.screen.highlight(self.index)
                print('DOWN:',self.index)
        if id == board.BTNBACK:
            if len(self.history)  == 1:
                self.get_items(self.history[-1])
            else:
                self.history.pop()
                self.get_items(self.history[-1])


    def main(self):
        epaper.initEpaper()
        # Show main menu
        self.get_items(self.menu['mainmenu'])
        self.history.append(self.menu['mainmenu'])
