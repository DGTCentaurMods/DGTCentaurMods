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

import time, threading, serial

from DGTCentaurMods.classes import Log
from DGTCentaurMods.classes.CentaurConfig import CentaurConfig
from DGTCentaurMods.lib import common
from DGTCentaurMods.consts import Enums, consts

def _rotate_field(index):
    R = (index // 8)
    C = (index % 8)
    new_index = (7 - R) * 8 + C
    return new_index

def _checksum(bytes_array):
    csum = 0
    for c in bytes(bytes_array):
        csum += c
    return csum % 128

class CentaurBoard(common.Singleton):

    _SERIAL = None
    _BAUD_RATE = 1000000
    _TIMEOUT = .2

    _initialized = False

    _IDLE_BOARD_RESPONSE = b''
    _IDLE_KEYS_RESPONSE = b''

    _key_callback = None
    _field_callback = None

    _events_worker = None

    _callbacks_queue = []

    _battery_level = 0

    _stand_by = False

    _disabled = False

    _timeout_disabled = False
    _events_enabled = True

    _power_connected = False

    _stand_by_thread = None

    _socket = None

    _last_battery_check = time.time()-18 # Little starting delay before first check

    def _initialize(self):

        if self._SERIAL == None:

            print("Opening board port...")
            self._SERIAL = serial.Serial("/dev/serial0", baudrate=self._BAUD_RATE, timeout=self._TIMEOUT)

            if self._SERIAL.isOpen():
                
                # If the port was already open, we close it then re-open it
                self._SERIAL.close()
                self._SERIAL.open()


            # But the address might not be correct
            # We send an initial 0x4d to ask the board to provide its address
            print('Detecting board address...')

            self.read_from_serial()

            print('Sending payload 1...')
            self.write_to_serial(b'\x4d')
            self.read_from_serial()

            print('Sending payload 2...')
            self.write_to_serial(b'\x4e')
            self.read_from_serial()

            print('Serial is open. Waiting for response...')

            response = b''

            self._address_1 = 0
            self._address_2 = 0

            timeout = time.time() + 10

            while len(response) < 4 and time.time() < timeout:

                self.write_to_serial(b'\x87\x00\x00\x07')
                response = self.read_from_serial()
                
                if len(response) > 4:

                    self._address_1 = response[3]
                    self._address_2 = response[4]

                    self._IDLE_KEYS_RESPONSE = self.build_packet(b'\xb1\x00\x06', b'')
                    self._IDLE_BOARD_RESPONSE = self.build_packet(b'\x85\x00\x06', b'')

                    print("Address:" + hex(self._address_1) + hex(self._address_2))
                    break

                time.sleep(1)
            
            if self._address_1 == 0 and self._address_2 == 0:
                Log.exception(CentaurBoard._initialize, "No response from serial!")
                Log.info("Board communication has been disabled...")
                self._disabled = True
                self._SERIAL.close()
                pass

        return self

    def initialize(self):

        if self._SERIAL == None:

            self._initialize()
            
            time.sleep(2)

            if not self.clear_serial():
                Log.exception(CentaurBoard.initialize, "Unable to clear the serial!")

            self._initialized = True

            self._events_worker = threading.Thread(target=self.events_board_thread)
            self._events_worker.daemon = True
            
            self._events_worker.start()

        return self

    def destroy(self):
        self.time_limit = 0
        self._events_worker.join()
        self._SERIAL = None

    def serial(self):
        return self._SERIAL

    def read_from_serial(self) -> bytes:

        bytes = b''

        if self._disabled:
            return bytes

        try:
            length = 1000 if not self._initialized  else self._SERIAL.in_waiting
            if length:
                bytes = self._SERIAL.read(length)
        except:
            Log.info("Serial returned no data (Board may be disconnected)...")

            pass

        return bytes

    def write_to_serial(self, bytes):
        try:
            if not self._disabled:
                self._SERIAL.write(bytearray(bytes))

        except:
            Log.info(f"Unable to write to serial '{bytes}'...")

    def build_packet(self, command, data, no_checksum = False) -> bytearray:

        result = bytearray(command 
                           + self._address_1.to_bytes(1,byteorder='big') 
                           + self._address_2.to_bytes(1,byteorder='big') 
                           + data)
        
        if not no_checksum:
            result.append(_checksum(result))

        return result
    
    def ask_serial(self, command, data) -> bytes:

        if self._disabled:
            return b''

        self.send_packet(command, data)
        time.sleep(.01)

        result = self.read_from_serial()
        time.sleep(.01)

        return result

    def send_packet(self, command, data):
        self.write_to_serial(self.build_packet(command, data))

    def leds_off(self):
        self.send_packet(b'\xb0\x00\x07', b'\x00')
    
    def clear_board_data(self):
        self.read_from_serial()
        self.send_packet(b'\x83', b'')
        self.read_from_serial()

    # TODO to be reviewed
    def clear_serial(self, timeout=30):

        if self._disabled:
            return True

        response_1 = b''
        response_2 = b''
        
        timeout = time.time() + timeout

        while True:
            print('Checking and clear the serial...')
            while time.time() < timeout:

                expected_1 = self.build_packet(b'\x85\x00\x06', b'')
                response_1 = self.ask_serial(b'\x83', b'')

                expected_2 = self.build_packet(b'\xb1\x00\x06', b'')
                response_2 = self.ask_serial(b'\x94', b'')

                # If board is idle, return True
                if expected_1 == response_1 and expected_2 == response_2:
                    print('Board is idle. Serial is clear.')
                    return True
                
                time.sleep(1)
            
            print('Unable to clear th serial...')
            return False

    def beep(self, sound) -> None:
        """Play sound only if enabled in config"""

        _SOUND_TO_CONF_MAPPING = {
            Enums.Sound.CORRECT_MOVE : consts.SOUND_CORRECT_MOVES,
            Enums.Sound.WRONG_MOVE : consts.SOUND_WRONG_MOVES,
            Enums.Sound.TAKEBACK_MOVE : consts.SOUND_TAKEBACK_MOVES,
            Enums.Sound.COMPUTER_MOVE : consts.SOUND_COMPUTER_MOVES,
            Enums.Sound.GAME_LOST : consts.SOUND_GAME_LOST,
            Enums.Sound.MUSIC : consts.SOUND_MUSIC,
            Enums.Sound.VICTORY : consts.SOUND_VICTORY,
        }

        if sound in _SOUND_TO_CONF_MAPPING:
            if not CentaurConfig.get_sound_settings(_SOUND_TO_CONF_MAPPING[sound]):
                return
    
        if sound == Enums.Sound.CORRECT_MOVE:
            self.send_packet(b'\xb1\x00\x0a', b'\x48\x05\x52\x05')

        if sound == Enums.Sound.TAKEBACK_MOVE:
            self.send_packet(b'\xb1\x00\x0a', b'\x52\x05\x48\x05')

        if sound == Enums.Sound.WRONG_MOVE:
            self.send_packet(b'\xb1\x00\x0a', b'\x30\x04\x29\x04')

        if sound == Enums.Sound.COMPUTER_MOVE:
            self.send_packet(b'\xb1\x00\x08', b'\x68\x05')
       
        if sound == Enums.Sound.MUSIC:
            self.send_packet(b'\xb1\x00\x10', b'\x40\x10\x44\x08\x45\x08\x47\x10\x45\x08')

        if sound == Enums.Sound.GAME_LOST:
            self.send_packet(b'\xb1\x00\x16', b'\x49\x04\x46\x10\x48\x04\x45\x10\x47\x04\x44\x10\x46\x04\x43\x10')

        if sound == Enums.Sound.VICTORY:
            self.send_packet(b'\xb1\x00\x1C', b'\x40\x04\x42\x04\x45\x10\x42\x04\x44\x04\x47\x10\x44\x04\x46\x04\x49\x10\x46\x04\x49\x10')

        if sound == Enums.Sound.POWER_OFF:
            self.send_packet(b'\xb1\x00\x0a', b'\x4c\x08\x48\x08')

    # TODO to be reviewed
    def led_array(self, inarray, speed = 3, intensity=5, no_field_rotation = False):
        
        # Lights all the leds in the given inarray with the given speed and intensity
        message = self.build_packet(b'\xb0\x00\x0c', b'\x05', no_checksum=True)
        
        message.append(speed)
        message.append(0)
        message.append(intensity)

        if no_field_rotation:
            for i in range(0, len(inarray)):
                message.append(inarray[i])
        else:
            for i in range(0, len(inarray)):
                message.append(_rotate_field(inarray[i]))

        message[2] = len(message) + 1

        message.append(_checksum(message))

        self.write_to_serial(message)

    # TODO to be reviewed
    def led_from_to(self, lfrom, lto, intensity=5):
        # Light up a from and to LED for move indication
        # Note the call to this function is 0 for a1 and runs to 63 for h8
        # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
        message = self.build_packet(b'\xb0\x00\x0c', b'\x05\x03\x00\x05\x3d\x31\x0d', no_checksum=True)

        # Recalculate lfrom to the different indexing system
        message[8] = intensity
        message[9] = _rotate_field(lfrom)
        # Same for lto
        message[10] = _rotate_field(lto)
        # Wipe checksum byte and append the new checksum.
        message.pop()
        message.append(_checksum(message))
        
        self.write_to_serial(message)

    # TODO to be reviewed
    def led(self, num, intensity=5):
        # Flashes a specific led
        # Note the call to this function is 0 for a1 and runs to 63 for h8
        # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
        try_index = 0

        while try_index < 5:
            try:
                message = self.build_packet(b'\xb0\x00\x0b', b'\x05\x0a\x01\x01\x3d\x5f', no_checksum=True)
                
                # Recalculate num to the different indexing system
                # Last bit is the checksum
                message[8] = intensity
                message[9] = _rotate_field(num)
                # Wipe checksum byte and append the new checksum.
                message.pop()
                message.append(_checksum(message))
                
                self.write_to_serial(message)
                
                break

            except:
                time.sleep(.1)
                try_index = try_index + 1

    def led_flash(self):
        self.send_packet(b'\xb0\x00\x0a', b'\x05\x0a\x00\x01')

    def sleep(self):
        self.send_packet(b'\xb2\x00\x07', b'\x0a')

    # TODO to be reviewed
    def get_board_state(self) -> bytearray:
        # Query the board and return a representation of it
        # Consider this function experimental
        # lowerlimit/upperlimit may need adjusting
        # Get the board data

        EMPTY_STATE : bytearray = [0] * 64

        if self._disabled:
            return consts.BOARD_START_STATE

        self.pause_events()

        try:
            response = []
            while (len(response) < 64):
                response = self.ask_serial(b'\xf0\x00\x07', b'\x7f')

            response = response = response[6:(64 * 2) + 6]
            
            result = EMPTY_STATE

            for x in range(0, 127, 2):
                tval = (response[x] * 256) + response[x+1]
                result[(int)(x/2)] = tval

            # Any square lower than 400 is empty
            # Any square higher than upper limit is also empty
            upperlimit = 32000
            lowerlimit = 300

            for x in range(0,64):
                result[x] = 0 if (result[x] < lowerlimit) or (result[x] > upperlimit) else 1
            
        except:
            result = EMPTY_STATE
            pass
        
        self.unpause_events()
        
        return result

    def print_board_state(self):

        state = self.get_board_state()

        for x in range(0,64,8):
            print("+---+---+---+---+---+---+---+---+")
            for y in range(0,8):
                print("| " + str(state[x+y]) + " ", end='')
            print("|\r")
        print("+---+---+---+---+---+---+---+---+")

    
    def subscribe_events(self, key_callback, field_callback, socket = None):

        # We backup the current callbacks
        # In order to restore them in the next unsubscribe_events call
        self._callbacks_queue.append({"field_callback":self._field_callback, "key_callback":self._key_callback})

        self._field_callback = field_callback
        self._key_callback = key_callback

        if socket:
            self._socket = socket

    def unsubscribe_events(self):

        # We cannot unsubscribe from the root callbacks!
        if len(self._callbacks_queue) > 1:
            callbacks = self._callbacks_queue.pop()

            # We restore the previous callbacks.
            self._field_callback = callbacks["field_callback"]
            self._key_callback = callbacks["key_callback"]

    def pause_events(self):
        self._events_enabled = False

    def unpause_events(self):
        self._events_enabled = True
        self.time_limit = time.time() + self._events_timeout

    def _read_fields(self, timeout):
        try:
            if not self._disabled and self._field_callback:

                response = self.ask_serial(b'\x83', b'')
                
                if not self._stand_by and response != self._IDLE_BOARD_RESPONSE:

                    if len(response) > 1 and response[0:2] == bytes(b'\x85\x00'):
                        
                        for x in range(2, len(response) -1):

                            b = response[x:x+1]
                            
                            if b == b'\x40' or b == b'\x41':
                                
                                self._field_callback(_rotate_field(response[x+1]), 
                                    { 64:Enums.PieceAction.LIFT, 65:Enums.PieceAction.PLACE }[response[x]])
                                
                                self.time_limit = time.time() + timeout
                                break
        
        except Exception as e:
            print(e)
            Log.exception(CentaurBoard._read_fields, e)
            pass

    def _read_keys(self, timeout):

        if self._disabled:
            return

        A1_HEX = "{:02x}".format(self._address_1)
        A2_HEX = "{:02x}".format(self._address_2)
        
        try:
            button = Enums.Btn.NONE
            
            response = self.ask_serial(b'\x94', b'')
        
            if not self._stand_by and response != self._IDLE_KEYS_RESPONSE:

                response_is = lambda header, data: response.hex()[:-2] == header+A1_HEX+A2_HEX+data

                if response_is("b10011", "00140a0501000000007d47"):
                    button = Enums.Btn.BACK

                if response_is("b10011", "00140a0510000000007d17"):
                    button = Enums.Btn.TICK

                if response_is("b10011", "00140a0508000000007d3c"):
                    button = Enums.Btn.UP

                if response_is("b10010", "00140a05020000000061"):
                    button = Enums.Btn.DOWN

                if response_is("b10010", "00140a0540000000006d"):
                    button = Enums.Btn.HELP

                if response_is("b10010", "00140a0504000000002a"):
                    button = Enums.Btn.PLAY

            # TODO standby mode to be reviewed
            """
            if (response.hex()[:-2] == "b10010" 
                + A1_HEX
                + A2_HEX 
                + "00140a0504000000002a"):

                breaktime = time.time() + 0.5

                while time.time() < breaktime:
                    
                    expected = bytearray(b'\xb1\x00\x06' 
                                            + self.address_1.to_bytes(1, byteorder='big') 
                                            + self.address_2.to_bytes(1, byteorder='big'))
                    expected.append(_checksum(expected))
                    
                    response = self.ask_serial(b'\x94', b'')
                    
                    if response.hex().startswith("b10011" 
                                                    + A1_HEX
                                                    + A2_HEX 
                                                    + "00140a0500040"):
                
                        if self._stand_by == False:

                            Log.info("Standby mode invoked...")

                            self.beep(Enums.Sound.POWER_OFF)
                            if self._socket:
                                self._socket.send_request({"standby":True})

                            self._stand_by = True

                            self.leds_off()

                            self._stand_by_thread = threading.Timer(600,self.shutdown)
                            self._stand_by_thread.start()
                            
                            self.time_limit = time.time() + 100000
                            break
                        else:

                            Log.info("Standby mode cancelled...")
                            self.clear_serial()
                            if self._socket:
                                self._socket.send_request({"standby":False})
                            
                            if self._stand_by_thread:
                                self._stand_by_thread.cancel()

                            self._stand_by = False
                            self.time_limit = time.time() + timeout
                            break

                else:
                    self.shutdown()

            """

            if button != Enums.Btn.NONE:
                self.time_limit = time.time() + timeout

                if self._key_callback:
                    self._key_callback(button)

        except Exception as e:
            print(e)
            Log.exception(CentaurBoard._read_keys, e)
            pass

    def push_button(self, button):
        if self._key_callback:
            self._key_callback(button)

    def shutdown(self):
        
        if self._socket:
            self.beep(Enums.Sound.POWER_OFF)
            self._socket.send_request({"sys":"shutdown"})

    # TODO to be reviewed
    def _read_battery(self, timeout):

        if self._disabled:
            return

        try:

            # Every 30 seconds check the battery details
            if time.time() - self._last_battery_check > 30:

                response = b''
                timeout = time.time() + 4

                while len(response) < 7 and time.time() < timeout:
                    
                    # Sending the board a packet starting with 152 gives battery info
                    try:
                        response = self.ask_serial(bytearray([152]), b'')
                    except:
                        pass

                if len(response) > 6 and response[0] == 181:

                    self._last_battery_check = time.time()
                    self._battery_level = response[5] & 31
                    vall = (response[5] >> 5) & 7
                    if vall == 1 or vall == 2:
                        self._power_connected = True
                    else:
                        self._power_connected = False

                    if self._socket:
                        self._socket.send_request({"battery":-1 if self._power_connected else self._battery_level})
        
        except Exception as e:
            print(e)
            Log.exception(CentaurBoard._read_battery, e)
        pass

    def events_board_thread(self, timeout = 60 * 15):

        self.time_limit = time.time() + timeout
        self._events_timeout = timeout

        while time.time() < self.time_limit:

            loopstart = time.time()

            if self._events_enabled:
                # Hold and restart timeout on charger attached
                if self._power_connected:
                    self.time_limit = time.time() + 100000
                    self._timeout_disabled = True

                else:
                
                    if self._timeout_disabled:
                        self.time_limit = time.time() + timeout
                        self._timeout_disabled = False

                if not self._stand_by:

                    # FIELDS HANDLING
                    self._read_fields(timeout)
            
                    # KEYS HANDLING
                    self._read_keys(timeout)
                
                # BATTERY HANDLING
                self._read_battery(timeout)

            else:
                self.time_limit = time.time() + 100000

            if time.time() - loopstart > 30:
                self.time_limit = time.time() + timeout

        else:

            if self._events_enabled and not self._disabled:
                self.shutdown()


def get():
    return CentaurBoard().initialize()

