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
        self.level = []

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
            #print(title)
        self.screen.draw_page(menu_title,item_list)
        self.screen.highlight(0,0)


    def select(self, index):
        # If this is a submenu - get the items and display
        if self.items[self.index]['type'] == 'menu':
            self.get_items(self.items[index])
            self.level.append(self.index)
        # If other types - add here what to do


    def key_press(self, id):
        if id == board.BTNTICK:
            self.select(self.index)
        if id == board.BTNUP:
            print('UP:', self.index)
            if self.index >= 0:
                self.index -= 1
                self.screen.highlight(self.index, self.index+1)
        if id == board.BTNDOWN:
            print('DOWN:',self.index)
            if self.index <= len(self.items):
                self.index += 1
                self.screen.highlight(self.index, self.index-1)
        if id == board.BTNBACK:
            if self.level[-1] == 0:
                self.select(self.level[-1])
            else:
                self.level.pop()
                self.select(self.level[-1])


    def main(self):
        epaper.initEpaper()
        # Show main menu
        self.get_items(self.menu['mainmenu'])
        self.level.append('0')
        #print(self.menu['mainmenu'])
