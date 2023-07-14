# This file is part of the DGTCentaur Mods open source software
# ( https://github.com/EdNekebno/DGTCentaur )
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
# https://github.com/EdNekebno/DGTCentaur/blob/master/LICENSE.md
#
# This and any other notices must remain intact and unaltered in any
# distribution, modification, variant, or derivative of this software.

import logging
import logging.handlers
import os

from DGTCentaurMods.game.consts import consts


class _Log:

    __initialized = False

    @staticmethod
    def _init():

        try:

            if not os.path.exists(consts.LOG_DIR):
                os.makedirs(consts.LOG_DIR)

            handler = logging.handlers.WatchedFileHandler(consts.LOG_DIR+'/'+consts.LOG_NAME)
            formatter = logging.Formatter(logging.BASIC_FORMAT)
            handler.setFormatter(formatter)
            
            root = logging.getLogger()
            root.setLevel(consts.LOG_LEVEL)
            root.addHandler(handler)

            _Log.__initialized = True

            print("Logging initialized.")
            _Log._info("Logging started.")

            logging.getLogger('chess.engine').setLevel(logging.INFO)

        except Exception as e:
            print(f'[Log._init] {e}')

    @staticmethod
    def _info(message):
        if _Log.__initialized == False:
            _Log._init()

        logging.info(message)

    @staticmethod
    def _exception(message):
        if _Log.__initialized == False:
            _Log._init()

        logging.exception(message)

    @staticmethod
    def _debug(message):
        if _Log.__initialized == False:
            _Log._init()

        logging.debug(message)


def info(message):
    _Log._info(message)

def exception(message):
    _Log._exception(message)

def debug(message):
    _Log._debug(message)