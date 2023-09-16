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

import os, sys, logging, logging.handlers

from logging.handlers import RotatingFileHandler

from DGTCentaurMods.consts import consts

__ID__ = consts.LOG_NAME

class _Log:

    __initialized = False
    __logger = None
    __last_info = None

    @staticmethod
    def _init():

        try:

            if not os.path.exists(os.path.dirname(consts.LOG_FILENAME)):
                os.makedirs(os.path.dirname(consts.LOG_FILENAME))

            _Log.__logger  = logging.getLogger(__ID__)

            _Log.__logger.setLevel(consts.LOG_LEVEL)

             # Add a rotating handler
            file_handler = RotatingFileHandler(consts.LOG_FILENAME, 'a+', maxBytes=1000000, backupCount=5)

            file_handler.setFormatter(
                logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
            ))

            _Log.__logger.addHandler(file_handler)
            _Log.__initialized = True

            print("Logging initialized.")

            _Log.__logger.info("Logging started.")


        except Exception as e:
            print(f'[Log._init] {e}')

    @staticmethod
    def _info(message):
        if _Log.__initialized == False:
            _Log._init()

        if message != _Log.__last_info:
            _Log.__logger.info(message)
            _Log.__last_info = message

    @staticmethod
    def _exception(source, message):
        if _Log.__initialized == False:
            _Log._init()

        _Log.__logger.exception(f"{source.__name__} -> {message}")

    @staticmethod
    def _debug(message):

        if _Log.__initialized == False:
            _Log._init()

        _Log.__logger.debug(message)

def last_exception() -> str:
    exception_type, exception_object, exception_traceback = sys.exc_info()

    log = f"Exception -> {exception_object}\nException type -> {exception_type}\n\n"

    while(exception_traceback):
        traceback = f"File name -> {exception_traceback.tb_frame}\n\nLine number -> {exception_traceback.tb_lineno}"
        exception_traceback = exception_traceback.tb_next

    return log + traceback

def info(message):
    _Log._info(message)

def exception(source, message):
    _Log._exception(source, message)

def debug(message):
    _Log._debug(message)