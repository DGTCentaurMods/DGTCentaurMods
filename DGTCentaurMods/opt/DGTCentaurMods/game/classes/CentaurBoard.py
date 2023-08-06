# DGT Centaur board control functions
#
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

import os, time, threading, serial

from DGTCentaurMods.game.classes import Log, CentaurScreen
from DGTCentaurMods.game.lib import common
from DGTCentaurMods.game.consts import Enums


SCREEN = CentaurScreen.get()

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

    _key_callback = None
    _field_callback = None

    _events_worker = None

    _callbacks_queue = []

    _battery_level = 0

    _stand_by = False

    _timeout_disabled = False
    _events_enabled = True

    _power_connected = False

    _last_battery_check = time.time()


    def initialize(self):

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

            self.read_serial()

            print('Sending payload 1...')
            self.write_serial(b'\x4d')
            self.read_serial()

            print('Sending payload 2...')
            self.write_serial(b'\x4e')
            self.read_serial()

            print('Serial is open. Waiting for response...')

            response = b''

            self.address_1 = 00
            self.address_2 = 00

            timeout = time.time() + 60

            while len(response) < 4 and time.time() < timeout:

                self.write_serial(b'\x87\x00\x00\x07')
                response = self.read_serial()
                
                if len(response) > 3:

                    self.address_1 = response[3]
                    self.address_2 = response[4]

                    print("Discovered new address:" + hex(self.address_1) + hex(self.address_2))
                    break
            else:

                raise Exception("No response from serial!")
            
            time.sleep(2)

            self.clear_serial()

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

    def read_serial(self, length = 10000) -> bytes:
        try:
            bytes = self._SERIAL.read(length)
        except:
            return b''
        
        #bytes = self._SERIAL.read(length)

        #if bytes != b'':
        #    print("<-"+"".join("\\x%02x" % i for i in bytes))
        
        return bytes

    def write_serial(self, bytes):
        self._SERIAL.write(bytearray(bytes))
        #print("->"+"".join("\\x%02x" % i for i in bytes))

    def build_packet(self, command, data) -> bytearray:

        result = bytearray(command 
                           + self.address_1.to_bytes(1,byteorder='big') 
                           + self.address_2.to_bytes(1,byteorder='big') 
                           + data)
        
        result.append(_checksum(result))

        return result
    
    def ask_serial(self, command, data) -> bytes:

        self.send_packet(command, data)
        return self.read_serial()

    def send_packet(self, command, data):
        self.write_serial(self.build_packet(command, data))

    def leds_off(self):
        self.send_packet(b'\xb0\x00\x07', b'\x00')
    
    def clear_board_data(self):
        self.read_serial()
        self.send_packet(b'\x83', b'')
        self.read_serial()

    def clear_serial(self):
        print('Checking and clear the serial line...')

        response_1 = b''
        response_2 = b''
        
        while True:

            expected_1 = self.build_packet(b'\x85\x00\x06', b'')
            response_1 = self.ask_serial(b'\x83', b'')


            expected_2 = self.build_packet(b'\xb1\x00\x06', b'')
            response_2 = self.ask_serial(b'\x94', b'')

            # If board is idle, return True
            if expected_1 == response_1 and expected_2 == response_2:
                print('Board is idle. Serial is clear.')
                return True
            else:
                print('Attempting to clear serial...')


    def beep(self, beeptype):
       
        if (beeptype == Enums.Sound.GENERAL):
            self.send_packet(b'\xb1\x00\x08',b'\x4c\x08')
        if (beeptype == Enums.Sound.FACTORY):
            self.send_packet(b'\xb1\x00\x08', b'\x4c\x40')
        if (beeptype == Enums.Sound.POWER_OFF):
            self.send_packet(b'\xb1\x00\x0a', b'\x4c\x08\x48\x08')
        if (beeptype == Enums.Sound.POWER_ON):
            self.send_packet(b'\xb1\x00\x0a', b'\x48\x08\x4c\x08')
        if (beeptype == Enums.Sound.WRONG):
            self.send_packet(b'\xb1\x00\x0a', b'\x4e\x0c\x48\x10')
        if (beeptype == Enums.Sound.WRONG_MOVE):
            self.send_packet(b'\xb1\x00\x08', b'\x48\x08')


    def led_array(self, inarray, speed = 3, intensity=5):
        
        # Lights all the leds in the given inarray with the given speed and intensity
        message = bytearray(b'\xb0\x00\x0c' + self.address_1.to_bytes(1, byteorder='big') + self.address_2.to_bytes(1, byteorder='big') + b'\x05')
        
        message.append(speed)
        message.append(0)
        message.append(intensity)

        for i in range(0, len(inarray)):
            message.append(_rotate_field(inarray[i]))

        message[2] = len(message) + 1

        message.append(_checksum(message))

        self.write_serial(message)


    def led_from_to(self, lfrom, lto, intensity=5):
        # Light up a from and to LED for move indication
        # Note the call to this function is 0 for a1 and runs to 63 for h8
        # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
        message = bytearray(b'\xb0\x00\x0c' 
                            + self.address_1.to_bytes(1, byteorder='big') 
                            + self.address_2.to_bytes(1, byteorder='big') 
                            + b'\x05\x03\x00\x05\x3d\x31\x0d')

        # Recalculate lfrom to the different indexing system
        message[8] = intensity
        message[9] = _rotate_field(lfrom)
        # Same for lto
        message[10] = _rotate_field(lto)
        # Wipe checksum byte and append the new checksum.
        message.pop()
        message.append(_checksum(message))
        
        self.write_serial(message)


    def led(self, num, intensity=5):
        # Flashes a specific led
        # Note the call to this function is 0 for a1 and runs to 63 for h8
        # but the electronics runs 0x00 from a8 right and down to 0x3F for h1
        try_index = 0

        while try_index < 5:
            try:
                message = bytearray(b'\xb0\x00\x0b' 
                                    + self.address_1.to_bytes(1, byteorder='big') 
                                    + self.address_2.to_bytes(1, byteorder='big') 
                                    + b'\x05\x0a\x01\x01\x3d\x5f')
                
                # Recalculate num to the different indexing system
                # Last bit is the checksum
                message[8] = intensity
                message[9] = _rotate_field(num)
                # Wipe checksum byte and append the new checksum.
                message.pop()
                message.append(_checksum(message))
                
                self.write_serial(message)
                
                break

            except:
                time.sleep(.1)
                try_index = try_index + 1

    def led_flash(self):
        self.send_packet(b'\xb0\x00\x0a', b'\x05\x0a\x00\x01')

    def sleep(self):
        self.send_packet(b'\xb2\x00\x07', b'\x0a')

    def get_board_state(self, field = None):
        # Query the board and return a representation of it
        # Consider this function experimental
        # lowerlimit/upperlimit may need adjusting
        # Get the board data

        self.pause_events()

        response = []
        while (len(response) < 64):

            response = self.ask_serial(b'\xf0\x00\x07', b'\x7f')

            if (len(response) < 64):
                time.sleep(0.5)

        response = response = response[6:(64 * 2) + 6]
        
        result = [None] * 64

        for x in range(0, 127, 2):
            tval = (response[x] * 256) + response[x+1]
            result[(int)(x/2)] = tval

        # Any square lower than 400 is empty
        # Any square higher than upper limit is also empty
        upperlimit = 32000
        lowerlimit = 300

        for x in range(0,64):
            if ((result[x] < lowerlimit) or (result[x] > upperlimit)):
                result[x] = 0
            else:
                result[x] = 1
        if field:
            return result[field]
        
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

    
    def subscribe_events(self, key_callback, field_callback):

        # We backup the current callbacks
        # In order to restore them in the next unsubscribe_events call
        self._callbacks_queue.append({"field_callback":self._field_callback, "key_callback":self._key_callback})

        self._field_callback = field_callback
        self._key_callback = key_callback

    def unsubscribe_events(self):

        callbacks = self._callbacks_queue.pop()

        # We restore the previous callbacks
        self._field_callback = callbacks["field_callback"]
        self._key_callback = callbacks["key_callback"]

    def pause_events(self):
        self._events_enabled = False

    def unpause_events(self):
        self._events_enabled = True
        self.time_limit = time.time() + self._events_timeout

    def shutdown(self):

        SCREEN.loading_screen("Bye!")

        self.beep(Enums.Sound.POWER_OFF)
        
        self.led_from_to(7,7)

        os.system("(sleep 1 && sudo poweroff)")

    def _read_fields(self, timeout):
        try:
            expected = bytearray(b'\x85\x00\x06'
                                    + self.address_1.to_bytes(1, byteorder='big') 
                                    + self.address_2.to_bytes(1, byteorder='big'))
            
            expected.append(_checksum(expected))
            
            response = bytearray(self.ask_serial(b'\x83', b''))
            
            if (response != expected):
                if (len(response) > 1 and response[0] == 133 and response[1] == 0):
                    for x in range(0, len(response) - 1):
                        
                        if (response[x] == 64):

                            # Calculate the square to 0(a1)-63(h8) so that
                            # all functions match

                            new_square = _rotate_field(response[x + 1])
                            
                            if self._field_callback:
                                self._field_callback(new_square + 1)
                            
                            self.time_limit = time.time() + timeout
                        
                        if (response[x] == 65):

                            # Calculate the square to 0(a1)-63(h8) so that
                            # all functions match

                            new_square = _rotate_field(response[x + 1])
                            
                            if self._field_callback:
                                self._field_callback((new_square + 1) * -1)
                            
                            self.time_limit = time.time() + timeout

        
        except Exception as e:
            print(e)
            Log.exception(CentaurBoard._read_fields, e)
            pass

    def _read_keys(self, timeout):

        A1_HEX = "{:02x}".format(self.address_1)
        A2_HEX = "{:02x}".format(self.address_2)
        
        try:
            button = Enums.Btn.NONE
            
            expected = bytearray(b'\xb1\x00\x06' 
                                    + self.address_1.to_bytes(1, byteorder='big') 
                                    + self.address_2.to_bytes(1, byteorder='big'))
        
            expected.append(_checksum(expected))
            
            response = bytearray(self.ask_serial(b'\x94', b''))
        
            if not self._stand_by:

                if (response.hex()[:-2] == "b10011" 
                    + A1_HEX
                    + A2_HEX 
                    + "00140a0501000000007d47"):

                    self.time_limit = time.time() + timeout
                    button = Enums.Btn.BACK

                if (response.hex()[:-2] == "b10011" 
                    + A1_HEX
                    + A2_HEX 
                    + "00140a0510000000007d17"):

                    self.time_limit = time.time() + timeout
                    button = Enums.Btn.TICK

                if (response.hex()[:-2] == "b10011" 
                    + A1_HEX
                    + A2_HEX 
                    + "00140a0508000000007d3c"):

                    self.time_limit = time.time() + timeout
                    button = Enums.Btn.UP

                if (response.hex()[:-2] == "b10010" 
                    + A1_HEX
                    + A2_HEX 
                    + "00140a05020000000061"):

                    self.time_limit = time.time() + timeout
                    button = Enums.Btn.DOWN

                if (response.hex()[:-2] == "b10010" 
                    + A1_HEX
                    + A2_HEX 
                    + "00140a0540000000006d"):

                    self.time_limit = time.time() + timeout
                    button = Enums.Btn.HELP
            
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
                    
                    response = bytearray(self.ask_serial(b'\x94', b''))
                    
                    if response.hex().startswith("b10011" 
                                                    + A1_HEX
                                                    + A2_HEX 
                                                    + "00140a0500040"):
                
                        if self._stand_by == False:

                            Log.info("Standby mode invoked...")

                            #epaper.standbyScreen(True)

                            self._stand_by = True

                            self._stand_by_thread = threading.Timer(600,self.shutdown)
                            self._stand_by_thread.start()
                            
                            self.time_limit = time.time() + 100000
                            break
                        else:

                            Log.info("Standby mode cancelled...")
                            self.clear_serial()
                            
                            #epaper.standbyScreen(False)

                            self._stand_by_thread.cancel()

                            self._stand_by = False
                            self.time_limit = time.time() + timeout
                            break

                else:
                    self.beep(Enums.Sound.POWER_OFF)
                    self.shutdown()

            if button != Enums.Btn.NONE:
                self.time_limit = time.time() + timeout
                
                if self._key_callback:
                    self._key_callback(button)

        except Exception as e:
            print(e)
            Log.exception(CentaurBoard._read_keys, e)
            pass

    def _read_battery(self, timeout):
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

                if len(response) < 7:
                    pass
                else:
                    if response[0] == 181:
                        self._last_battery_check = time.time()
                        self._battery_level = response[5] & 31
                        vall = (response[5] >> 5) & 7
                        if vall == 1 or vall == 2:
                            self._power_connected = True
                        else:
                            self._power_connected = False

                        # TODO: implement battery change event
                        SCREEN.set_battery_value(-1 if self._power_connected else self._battery_level)

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

                time.sleep(0.05)

            else:
                self.time_limit = time.time() + 100000

            if time.time() - loopstart > 30:
                self.time_limit = time.time() + timeout

            time.sleep(0.05)
        else:

            if self._events_enabled:
                self.shutdown()


def get():
    return CentaurBoard().initialize()

