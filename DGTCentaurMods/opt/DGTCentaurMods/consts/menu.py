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
from DGTCentaurMods.consts.latest_tag import LASTEST_TAG

import os

_ITEMS = "items"
_ACTION = "action"
_LABEL = "label"
_SHORT_LABEL = "short_label"
_VALUE = "value"
_TYPE = "type"
_ONLY_WEB = "only_web"
_ONLY_BOARD = "only_board"
_ID = "id"
_DISABLED = "disabled"

# Menu items
# Proto version, shared between web & ePaper
MENU_ITEMS = [

    {   _ID:"play", 
        _LABEL:"Play",
        _ITEMS: [
            {_LABEL: "Resume last game", _SHORT_LABEL: "Resume",
             _ACTION: { _TYPE: "socket_execute", _VALUE: "uci_resume.py"} },
            {_LABEL: "Play 1 vs 1", 
             _ACTION:{ _TYPE: "socket_execute", _VALUE: "1vs1_module.py"} },
            {_LABEL: "Play Lichess", 
             _ACTION:{ _TYPE: "socket_execute", _VALUE: "lichess_module.py"} },
        ] }, 
    
    { _LABEL:"Links", _ONLY_WEB:True, _ITEMS: [
            {_LABEL: "Open Lichess position analysis", 
             _ACTION :{ _TYPE: "js", _VALUE: '() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")' }},
            {_LABEL: "Open Lichess PGN import page", 
             _ACTION:{ _TYPE: "js", _VALUE: '() => window.open("https://lichess.org/paste", "_blank")' }},
            {_LABEL: "View current PGN", 
             _ACTION:{ _TYPE: "js", _VALUE: '() => me.viewCurrentPGN()' }},
        ]}, 
    
    { _LABEL:"Settings", _ONLY_WEB:True, _ITEMS: [
        { _LABEL:"🕸 Web settings", _ONLY_WEB:True, _ITEMS: [], _TYPE: "subitem", _ACTION:{_TYPE: "js_variable", _VALUE: "displaySettings"} },
        { _LABEL:"🎵 Board sounds", _ONLY_WEB:True, _ACTION:{ _TYPE: "socket_data", _VALUE: "sounds_settings"}}, 
    ]},
    
    { _LABEL:"Previous games", _ONLY_WEB:True, _ACTION:{ _TYPE: "socket_data", _VALUE: "previous_games"} }, 
    
    {   _ID:"system", 
        _LABEL:"System", _ITEMS: [

            { _LABEL: "✏ Edit configuration file", _ONLY_WEB:True, _ITEMS: [], _ACTION:{ _TYPE: "socket_read", _VALUE: "centaur.ini"}},
            { _ID:"uci", _LABEL:"✏ Edit engines UCI", _TYPE: "subitem", _ITEMS: [], _ONLY_WEB:True },
            { _ID:"famous", _LABEL:"✏ Edit famous PGN", _TYPE: "subitem", _ITEMS: [], _ONLY_WEB:True },

            { _TYPE: "divider", _ONLY_WEB:True },

            { _LABEL: "📴 Power off board", _SHORT_LABEL: "Power off",
              _ACTION:{ _TYPE: "socket_sys", "message": "A shutdown request has been sent to the board!", _VALUE: "shutdown"}
            },
            { _LABEL: "🌀 Reboot board", _SHORT_LABEL: "Reboot",
              _ACTION:{ _TYPE: "socket_sys", "message": "A reboot request has been sent to the board!", _VALUE: "reboot"}
            },
            { _LABEL: "⚡ Restart CORE service", _ONLY_WEB:True,
              _ACTION:{ _TYPE: "socket_sys", "message": "A restart request has been sent to the board!", _VALUE: "restart_service"}
            },
            { _LABEL: "⚡ Restart WEB service", _ONLY_WEB:True,
              _ACTION:{ _TYPE: "socket_sys", "message": "A restart request has been sent to the board!", _VALUE: "restart_web_service"}
            },
            { _LABEL:"Wifi", _ONLY_BOARD:True,
              _ACTION:{ _TYPE: "socket_execute", _VALUE: "wifi_module"} },

            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },

            { _LABEL:"Update", _ONLY_BOARD:True,
              _ACTION:{ _TYPE: "script_execute", _VALUE: "update"} },

            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
            
            { _LABEL: f"tag:{consts.TAG_RELEASE}", _ONLY_BOARD:True, _DISABLED:True, "font":"SMALL_FONT" },
            { _LABEL: f"last:{LASTEST_TAG}", _ONLY_BOARD:True, _DISABLED:True, "font":"SMALL_FONT" },

            { _TYPE: "divider", _ONLY_WEB:True },
            
            { _LABEL: "📋 Last log events", _ONLY_WEB:True,
              _ACTION:{ _TYPE: "socket_sys", "message": None, _VALUE: "log_events"}
            },
        ] },

        # Current tag version label
        { _LABEL: consts.EMPTY_LINE, _ONLY_BOARD:True, _DISABLED:True },
        { _LABEL: f"tag:{consts.TAG_RELEASE}" if LASTEST_TAG == consts.TAG_RELEASE else "Update available!", _ONLY_BOARD:True, _DISABLED:True, "font":"SMALL_FONT" },
]

if os.path.exists(f"{consts.HOME_DIRECTORY}/centaur/centaur"):
    MENU_ITEMS.insert(len(MENU_ITEMS)-2, { _LABEL:"Launch Centaur", _SHORT_LABEL:"Centaur", _ACTION:{ _TYPE: "socket_sys", _VALUE: "centaur"} })
