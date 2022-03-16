#!/usr/bin/python

import json

class MenuSystem:
    def __init__(self):
        #board.subscribeEvents(key_pressed)
        with open('menu/menu.json') as f:
            self.menu = json.load(f)
        self.level = []


    def get_items(self, level):
        self.items = []
        item_list = []
        for item in level['items']:
            k = level['items'][item]
            if isinstance(k, dict):
                self.items.append(k)
        for i in range(len(self.items)):
            title = self.items[i]['title']
            item_list.append(title)
            print(title)
        #epaper.drawMenu(item_list)


    def select(self, index):
        # If this is a submenu - get the items and display
        if self.items[index]['type'] == 'menu':
            self.get_items(self.items[index])
            self.level.append(index)
        # If other types - add here what to do


    def key_press(self, id):
        index = 0
        if id == board.BTNTICK:
            self.selected(index)
            event_key.set()
        if id == board.BTNUP:
            if id < index:
                index += 1
        if id == board.BTNDOWN:
            if id >= 0:
                index -= 1
        if id == board.BTNBACK:
            self.level.pop()
            if self.level[-1] == 0:
                self.main()
            else:
                self.select(self.level[-1])


    def main(self):
        # Show main menu
        self.get_items(self.menu['mainmenu'])
        self.level.append('0')
        #print(self.menu['mainmenu'])
