# Dynamic menu 
# Name: Engines
# Description: builds a menu out of installed engines in engines/

import pathlib, os
import configparser
import json

def build():
    #Menu header
    enginemenu = {}
    enginemenu['title'] = 'Engines'
    enginemenu['type'] = 'menu'
    enginemenu['items'] = ''

    #After color selection - run uci.py with arguments handled by MenuSystem
    #colormenu = { 'title': 'You play as', 'type': 'menu', 'items': { 'white': {'title': 'White', 'type': 'script', 'path': ''}, 'black': {'title': 'Black', 'type': 'script', 'path': ''}}}


    ### Insert Stockfish first




    # Pick up the engines from the engines folder and create the menu items
    enginepath = str(pathlib.Path(__file__).parent.resolve()) + "/../engines/"
    enginefiles = os.listdir(enginepath)
    enginefiles = list(filter(lambda x: os.path.isfile(enginepath + x), os.listdir(enginepath)))
    print('Engines found:', enginefiles)
    engines = {}
    for f in enginefiles:
        fn = str(f)
        if '.' not in fn:
            # If this file is not .uci then assume it is an engine
            engines[fn] = {'title': fn, 'type': 'menu', 'items': {}}
            # Get uci option for each engine
            ucifile = enginepath + fn + ".uci"
            if os.path.exists(ucifile):
                # Read the uci file and build a menu
                config = configparser.ConfigParser()
                config.read(ucifile)
                print(config.sections())
                for sect in config.sections():
                    engines[fn]['items'][sect] = { 'title': sect, 'type':
                    'menu', 'items': ()}
                    #Build last menu option with the right script command at the end
                    colormenu = {'white': {'title': 'Play as white', 'type': 'script',
                    'path': '/../game/uci.py white ' + '"' + fn + '"' + ' "' + sect
                    + '"'}, 'black': {'title': 'Play as black', 'type': 'script',
                    'path': 'game/uci.py black ' + '"' + fn + '"' + ' "' + sect
                    + '"'}}
                    engines[fn]['items'][sect]['items'] = colormenu
            else:
                engines[fn]['items']['color'] = colormenu

    enginemenu['items'] = engines

    print(json.dumps(
        enginemenu,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    ))
    return enginemenu
