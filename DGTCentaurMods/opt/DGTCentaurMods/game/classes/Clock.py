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

from DGTCentaurMods.game.classes import Log, CentaurScreen
from DGTCentaurMods.game.consts import fonts
from DGTCentaurMods.game.lib import common

import datetime

SCREEN = CentaurScreen.get()

_BASE_TIME = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

class _Clock():

    _duration = None

    _initial_time = None
    _paused_time = None
    _is_paused = False

    _wheader = "White player"
    _bheader = "Black player"

    def __init__(self, date):
        #self._duration = _BASE_TIME + datetime.timedelta(minutes=minutes)
        self._duration = date

    @staticmethod
    def zero():
        return _BASE_TIME

    def start(self):
        self._initial_time = datetime.datetime.now()

    def pause(self):
        try:
            if self._is_paused:
                return
            
            if self._initial_time is None:
                self.start()

            self._paused_time = datetime.datetime.now()
            self._is_paused = True

        except Exception as e:
            Log.Exception(_Clock.pause, e)

    def resume(self):
        try:
            if not self._is_paused:
                return

            if self._initial_time is None:
                self.start()

            self._initial_time = self._initial_time + (datetime.datetime.now() - self._paused_time)
            self._is_paused = False

        except Exception as e:
            Log.Exception(_Clock.resume, e)

    def set(self, time):
        try:
            self._duration = _BASE_TIME + (time -_BASE_TIME)
            self._initial_time = datetime.datetime.now()
            self._paused_time = datetime.datetime.now()
        except Exception as e:
            Log.Exception(_Clock.set, e)

    def get(self):
        try:
            if self._initial_time is None:
                self.start()

            if self._is_paused:
                result = self._paused_time - self._initial_time
            else:
                result = datetime.datetime.now() - self._initial_time

            result = self._duration - result
        
            return _BASE_TIME if result<_BASE_TIME else result

        except Exception as e:
            Log.Exception(_Clock.get, e)

class ClockPanel(common.Singleton):

    _wclock = None
    _bclock = None

    _clocks_enabled = False

    def __init__(self):
        pass

    def push(self, color):
        
        if self._wclock and self._bclock:
            if color:
                self._wclock.resume()
                self._bclock.pause()
            else:
                self._bclock.resume()
                self._wclock.pause()

    def initialize(self, wtime = None, btime = None):
        
        if wtime:
            # First call - clocks need to be initialized
            if self._wclock == None:
                self._wclock = _Clock(wtime)
                self._bclock = _Clock(wtime)

            self._wclock.set(wtime)

        if btime and self._bclock:
            self._bclock.set(btime)

    def enable(self, value):
        
        self._clocks_enabled = value

        if not value:
            self._wclock = None
            self._bclock = None

    def stop(self):
        
        if self._wclock and self._bclock:
            self._bclock.pause()
            self._wclock.pause()

    def set_clock_headers(self, wheader, bheader):
        self._wheader = wheader
        self._bheader = bheader

    def paint(self):

        if self._clocks_enabled:

            SCREEN.write_text(12.2, self._wheader, font=fonts.SMALL_FONT)
            SCREEN.write_text(9.5, self._bheader, font=fonts.SMALL_FONT)

            if self._wclock:
                SCREEN.write_text(13.2, self._wclock.get().strftime("%M:%S"), font=fonts.DIGITAL_FONT)
            else:
                SCREEN.write_text(13.2, _Clock.zero().strftime("%M:%S"), font=fonts.DIGITAL_FONT)

            if self._bclock:
                SCREEN.write_text(10.5, self._bclock.get().strftime("%M:%S"), font=fonts.DIGITAL_FONT)
            else:
                SCREEN.write_text(10.5, _Clock.zero().strftime("%M:%S"), font=fonts.DIGITAL_FONT)

def get():
    return ClockPanel()
