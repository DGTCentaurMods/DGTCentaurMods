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

from DGTCentaurMods.game.classes import Log

import datetime

_BASE_TIME = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)

class Clock():

    _duration = None

    _initial_time = None
    _paused_time = None
    _is_paused = False

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
            Log.Exception(Clock.pause, e)

    def resume(self):
        try:
            if not self._is_paused:
                return

            if self._initial_time is None:
                self.start()

            self._initial_time = self._initial_time + (datetime.datetime.now() - self._paused_time)
            self._is_paused = False

        except Exception as e:
            Log.Exception(Clock.resume, e)

    def set(self, time):
        try:
            self._duration = _BASE_TIME + (time -_BASE_TIME)
            self._initial_time = datetime.datetime.now()
            self._paused_time = datetime.datetime.now()
        except Exception as e:
            Log.Exception(Clock.set, e)

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
            Log.Exception(Clock.get, e)