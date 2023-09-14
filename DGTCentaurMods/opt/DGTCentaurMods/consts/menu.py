# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/Alistair-Crompton/DGTCentaurMods )
#
# DGTCentaur Mods is free software: you can redistribute
# it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# DGTCentaur Mods is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this file.  If not, see
#
# https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

from DGTCentaurMods.consts import consts
from DGTCentaurMods.lib import common

from DGTCentaurMods.consts.latest_tag import LASTEST_TAG

from pathlib import Path

import os, configparser, copy


class Tag():

  ITEMS : str = "items"
  ACTION : str =  "action"
  LABEL : str =  "label"
  SHORT_LABEL : str =  "short_label"
  VALUE : str =  "value"
  TYPE : str =  "type"
  ONLY_WEB : str =  "only_web"
  ONLY_BOARD : str =  "only_board"
  ID : str =  "id"
  DISABLED : str =  "disabled"
  FILE : str =  "file"

# Menu items
# Proto version, shared between web & ePaper
_MENU_ITEMS = [
    
    {
        Tag.ID:"homescreen",
        Tag.LABEL:"← Back to main menu", 
        Tag.ACTION: { "type": "socket_sys", Tag.VALUE: "homescreen"}
    },

    {   Tag.ID:"play",
        Tag.LABEL:"Play",
        Tag.ITEMS: [
            {Tag.LABEL: "Resume last game", Tag.SHORT_LABEL: "Resume",
            Tag.ACTION: { Tag.TYPE: "socket_execute", Tag.VALUE: "uci_resume.py"} },
            {Tag.LABEL: "Play 1 vs 1", 
            Tag.ACTION:{ Tag.TYPE: "socket_execute", Tag.VALUE: "1vs1_module.py"} },
            {Tag.LABEL: "Play Lichess", 
            Tag.ACTION:{ Tag.TYPE: "socket_execute", Tag.VALUE: "lichess_module.py"} },
        ] }, 
    
    { Tag.ID:"links", Tag.LABEL:"Links", Tag.ONLY_WEB:True, Tag.ITEMS: [
            {Tag.LABEL: "Open Lichess position analysis", 
            Tag.ACTION :{ Tag.TYPE: "js", Tag.VALUE: '() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")' }},
            {Tag.LABEL: "Open Lichess PGN import page", 
            Tag.ACTION:{ Tag.TYPE: "js", Tag.VALUE: '() => window.open("https://lichess.org/paste", "_blank")' }},
            {Tag.LABEL: "View current PGN", 
            Tag.ACTION:{ Tag.TYPE: "js", Tag.VALUE: '() => me.viewCurrentPGN()' }},
        ]}, 
    
    { Tag.ID:"settings", Tag.LABEL:"Settings", Tag.ONLY_WEB:True, Tag.ITEMS: [
        { Tag.LABEL:"🕸 Web settings", Tag.ONLY_WEB:True, Tag.ITEMS: [], Tag.TYPE: "subitem", Tag.ACTION:{Tag.TYPE: "js_variable", Tag.VALUE: "displaySettings"} },
        { Tag.LABEL:"🎵 Board sounds", Tag.ONLY_WEB:True, Tag.ACTION:{ Tag.TYPE: "socket_data", Tag.VALUE: "sounds_settings"}}, 
    ]},
    
    { Tag.ID:"previous", Tag.LABEL:"Previous games", Tag.ONLY_WEB:True, Tag.ACTION:{ Tag.TYPE: "socket_data", Tag.VALUE: "previous_games"} }, 
    
    {   Tag.ID:"system", 
        Tag.LABEL:"System", Tag.ITEMS: [

            { Tag.LABEL: "✏ Edit configuration file", Tag.ONLY_WEB:True, Tag.ITEMS: [], Tag.ACTION:{ Tag.TYPE: "socket_read", Tag.VALUE: { Tag.ID: "conf", Tag.FILE:"centaur" }}},
            { Tag.ID:"uci", Tag.LABEL:"✏ Edit engines UCI", Tag.TYPE: "subitem", Tag.ITEMS: [], Tag.ONLY_WEB:True },
            { Tag.ID:"famous", Tag.LABEL:"✏ Edit famous PGN", Tag.TYPE: "subitem", Tag.ITEMS: [{ Tag.LABEL: "➕ Create a new PGN", Tag.ACTION:{ Tag.TYPE: "socket_read", Tag.VALUE: { Tag.ID:"famous_pgn", Tag.FILE:"__new__" }}}], Tag.ONLY_WEB:True },

            { Tag.TYPE: "divider", Tag.ONLY_WEB:True },

            { Tag.LABEL: "📴 Power off board", Tag.SHORT_LABEL: "Power off",
              Tag.ACTION:{ Tag.TYPE: "socket_sys", "message": "A shutdown request has been sent to the board!", Tag.VALUE: "shutdown"}
            },
            { Tag.LABEL: "🌀 Reboot board", Tag.SHORT_LABEL: "Reboot",
              Tag.ACTION:{ Tag.TYPE: "socket_sys", "message": "A reboot request has been sent to the board!", Tag.VALUE: "reboot"}
            },
            { Tag.LABEL: "⚡ Restart CORE service", Tag.ONLY_WEB:True,
              Tag.ACTION:{ Tag.TYPE: "socket_sys", "message": "A restart request has been sent to the board!", Tag.VALUE: "restart_service"}
            },
            { Tag.LABEL: "⚡ Restart WEB service", Tag.ONLY_WEB:True,
              Tag.ACTION:{ Tag.TYPE: "socket_sys", "message": "A restart request has been sent to the board!", Tag.VALUE: "restart_web_service"}
            },
            { Tag.LABEL:"Wifi", Tag.ONLY_BOARD:True,
              Tag.ACTION:{ Tag.TYPE: "socket_execute", Tag.VALUE: "wifi_module"} },

            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },

            { Tag.LABEL:"Update", Tag.ONLY_BOARD:True,
              Tag.ACTION:{ Tag.TYPE: "script_execute", Tag.VALUE: "update"} },

            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
            
            { Tag.LABEL: f"tag:{consts.TAG_RELEASE}", Tag.ONLY_BOARD:True, Tag.DISABLED:True, "font":"SMALL_FONT" },
            { Tag.LABEL: f"last:{LASTEST_TAG}", Tag.ONLY_BOARD:True, Tag.DISABLED:True, "font":"SMALL_FONT" },

            { Tag.TYPE: "divider", Tag.ONLY_WEB:True },
            
            { Tag.LABEL: "📋 Last log events", Tag.ONLY_WEB:True,
              Tag.ACTION:{ Tag.TYPE: "socket_sys", "message": None, Tag.VALUE: "log_events"}
            },
        ] },

        # Current tag version label
        { Tag.LABEL: consts.EMPTY_LINE, Tag.ONLY_BOARD:True, Tag.DISABLED:True },
        { Tag.LABEL: f"tag:{consts.TAG_RELEASE}" if LASTEST_TAG == consts.TAG_RELEASE else "Update available!", Tag.ONLY_BOARD:True, Tag.DISABLED:True, "font":"SMALL_FONT" },
]

if os.path.exists(f"{consts.HOME_DIRECTORY}/centaur/centaur"):
    _MENU_ITEMS.insert(len(_MENU_ITEMS)-2, { Tag.ID:"centaur", Tag.LABEL:"Launch Centaur", Tag.SHORT_LABEL:"Centaur", Tag.ACTION:{ Tag.TYPE: "socket_sys", Tag.VALUE: "centaur"} })


class _Menu(common.Singleton):

    def __call__(self, flag:str, ids:tuple) -> list :

        excluded_flag = Tag.ONLY_BOARD if flag == Tag.ONLY_WEB else Tag.ONLY_WEB

        result : list = []

        # Items to exclude
        for m in list(filter(lambda item:excluded_flag not in item or item[excluded_flag] == False, copy.deepcopy(_MENU_ITEMS))):
            
            if Tag.ID not in m or (len(ids) == 0 and m[Tag.ID] != "homescreen") or m[Tag.ID] in ids:

              if Tag.ITEMS in m:
                  menu_item = copy.deepcopy(m)
                  menu_item[Tag.ITEMS] = list(filter(lambda item:excluded_flag not in item or item[excluded_flag] == False, m[Tag.ITEMS]))
                  result.append(menu_item)
              else:
                  result.append(m)
        
        play_item = next(filter(lambda item:Tag.ID in item and item[Tag.ID] == "play", result), None)
        sys_item = next(filter(lambda item:Tag.ID in item and item[Tag.ID] == "system", result), None)

        ENGINE_PATH = consts.OPT_DIRECTORY+"/engines"
        PGNS_PATH = consts.OPT_DIRECTORY+"/famous_pgns"

        def get_sections(uci_file):
            parser = configparser.ConfigParser()
            parser.read(uci_file)

            return list(map(lambda section:section, parser.sections()))

        # We read the available engines + their options
        engines = list(map(lambda f:{Tag.ID:Path(f.name).stem, "options":get_sections(f.path)}, 
                           filter(lambda f: f.name.endswith(".uci"), os.scandir(ENGINE_PATH))))
        
        famous_pgns = list(map(lambda f:Path(f.name).stem, 
                           filter(lambda f: f.name.endswith(".pgn"), os.scandir(PGNS_PATH))))


        # Famous PGN menu item
        if play_item:
          play_item[Tag.ITEMS].append({ Tag.LABEL: "Play famous games", Tag.SHORT_LABEL: "Famous games", Tag.TYPE: "subitem", 
                                    Tag.ITEMS:list(map(lambda pgn: { Tag.LABEL: "⭐ "+common.capitalize_string(pgn), Tag.SHORT_LABEL:common.capitalize_string(pgn), Tag.ACTION: { Tag.TYPE: "socket_execute", Tag.VALUE: f'famous_module.py "{pgn}.pgn"' }},famous_pgns)) })

          # Engines menu items
          for engine in engines:

              engine_menu = { Tag.LABEL: "Play "+common.capitalize_string(engine[Tag.ID]), Tag.SHORT_LABEL: common.capitalize_string(engine[Tag.ID]), Tag.TYPE: "subitem", Tag.ITEMS:[] }

              play_item[Tag.ITEMS].append(engine_menu)
              
              for option in engine["options"]:
                      
                  engine_menu[Tag.ITEMS].append({
                          Tag.LABEL: "⭐ "+option.capitalize(), Tag.SHORT_LABEL:option.capitalize(),
                          Tag.ACTION: { Tag.TYPE: "socket_execute", "dialogbox": "color", Tag.VALUE: "uci_module.py {value} "+engine[Tag.ID]+' "'+option+'"' } })
                

        # Famous PGN editor menu items
        # UCI editor menu items
        # Only web
        if sys_item and excluded_flag == Tag.ONLY_BOARD:

            famous_item = next(filter(lambda item:Tag.ID in item and item[Tag.ID] == "famous", sys_item[Tag.ITEMS]), None)

            if famous_item:
                for pgn in famous_pgns:

                    editor_menu = { Tag.LABEL: 'Edit "'+common.capitalize_string(pgn)+'"', Tag.ONLY_WEB:True, Tag.ITEMS: [], Tag.ACTION:{ Tag.TYPE: "socket_read", Tag.VALUE: { Tag.ID: "famous_pgn", Tag.FILE:pgn }} }
                    famous_item[Tag.ITEMS].insert(len(famous_item[Tag.ITEMS])-1, editor_menu)

            uci_item = next(filter(lambda item:Tag.ID in item and item[Tag.ID] == "uci", sys_item[Tag.ITEMS]))
            
            for engine in engines:

                if os.path.exists(f"{consts.OPT_DIRECTORY}/engines/{engine['id']}.uci"):

                    editor_menu = { Tag.LABEL: "Edit UCI of "+common.capitalize_string(engine[Tag.ID]), Tag.ONLY_WEB:True, Tag.ITEMS: [], Tag.ACTION:{ Tag.TYPE: "socket_read", Tag.VALUE: { Tag.ID: "uci", Tag.FILE:engine[Tag.ID] }} }

                    uci_item[Tag.ITEMS].append(editor_menu)

        return result
    
def get(flag: str, ids: tuple = ()):
    return _Menu()(flag, ids)
