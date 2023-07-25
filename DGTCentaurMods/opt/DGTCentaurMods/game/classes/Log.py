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

import os, logging, logging.handlers

from logging.handlers import RotatingFileHandler

from DGTCentaurMods.game.consts import consts

__ID__ = consts.LOG_NAME

class _Log:

    __initialized = False
    __logger = None

    @staticmethod
    def _init():

        try:

            if not os.path.exists(os.path.dirname(consts.LOG_FILENAME)):
                os.makedirs(os.path.dirname(consts.LOG_FILENAME))

            handler = logging.handlers.WatchedFileHandler(consts.LOG_FILENAME)
            formatter = logging.Formatter('%(asctime)s %(name)s - %(levelname)s:%(message)s')
            handler.setFormatter(formatter)

             # Add a rotating handler
            rotating_handler = RotatingFileHandler(consts.LOG_FILENAME, 'a+', maxBytes=1000000, backupCount=5)
            
            _Log.__logger = logging.getLogger(__ID__)
            _Log.__logger.setLevel(consts.LOG_LEVEL)
            _Log.__logger.addHandler(handler)
            _Log.__logger.addHandler(rotating_handler)

            _Log.__initialized = True

            print("Logging initialized.")
            _Log._info("Logging started.")

        except Exception as e:
            print(f'[Log._init] {e}')

    @staticmethod
    def _info(message):
        if _Log.__initialized == False:
            _Log._init()

        _Log.__logger.info(message)

    @staticmethod
    def _exception(message):
        if _Log.__initialized == False:
            _Log._init()

        _Log.__logger.exception(message)

    @staticmethod
    def _debug(message):
        if _Log.__initialized == False:
            _Log._init()

        _Log.__logger.debug(message)


def info(message):
    _Log._info(message)

def exception(message):
    _Log._exception(message)

def debug(message):
    _Log._debug(message)