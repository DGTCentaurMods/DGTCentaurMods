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

import time, threading, serial

from DGTCentaurMods.board import centaur
from DGTCentaurMods.game.classes import Log
from DGTCentaurMods.game.lib import common

SOUND_GENERAL = 1
SOUND_FACTORY = 2
SOUND_POWER_OFF = 3
SOUND_POWER_ON = 4
SOUND_WRONG = 5
SOUND_WRONG_MOVE = 6

BTNBACK = 1
BTNTICK = 2
BTNUP = 3
BTNDOWN = 4
BTNHELP = 5
BTNPLAY = 6
BTNLONGPLAY = 7

def _rotate_field(index):
    R = (index // 8)
    C = (index % 8)
    new_index = (7 - R) * 8 + C
    return new_index

def _rotate_field_hex(field_hex):
    R = field_hex // 8
    C = field_hex % 8
    field = (7 - R) * 8 + C
    return field

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

    def read_serial(self, length = 10000):
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

    def build_packet(self, command, data):

        result = bytearray(command 
                           + self.address_1.to_bytes(1,byteorder='big') 
                           + self.address_2.to_bytes(1,byteorder='big') 
                           + data)
        
        result.append(_checksum(result))

        return result

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
            self.send_packet(b'\x83', b'')
            expected_1 = self.build_packet(b'\x85\x00\x06', b'')
            
            response_1 = self.read_serial()

            self.send_packet(b'\x94', b'')
            expected_2 = self.build_packet(b'\xb1\x00\x06', b'')
            
            response_2 = self.read_serial()

            # If board is idle, return True
            if expected_1 == response_1 and expected_2 == response_2:
                print('Board is idle. Serial is clear.')
                return True
            else:
                print('Attempting to clear serial...')


    def beep(self, beeptype):

        if centaur.get_sound() == "off":
            return
       
        if (beeptype == SOUND_GENERAL):
            self.send_packet(b'\xb1\x00\x08',b'\x4c\x08')
        if (beeptype == SOUND_FACTORY):
            self.send_packet(b'\xb1\x00\x08', b'\x4c\x40')
        if (beeptype == SOUND_POWER_OFF):
            self.send_packet(b'\xb1\x00\x0a', b'\x4c\x08\x48\x08')
        if (beeptype == SOUND_POWER_ON):
            self.send_packet(b'\xb1\x00\x0a', b'\x48\x08\x4c\x08')
        if (beeptype == SOUND_WRONG):
            self.send_packet(b'\xb1\x00\x0a', b'\x4e\x0c\x48\x10')
        if (beeptype == SOUND_WRONG_MOVE):
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
            self.send_packet(b'\xf0\x00\x07', b'\x7f')
            response = self.read_serial()
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
        self._events_running = False

    def unpause_events(self):
        self._events_running = True

    def events_board_thread(self, timeout = 60 * 15):

        self._stand_by = False
        self._hold_timeout = False
        self._events_paused = False

        self._events_running = True

        chargerconnected = 1
        batterylastchecked = time.time()

        self.time_limit = time.time() + timeout

        while time.time() < self.time_limit:

            loopstart = time.time()
            if self._events_running:
                # Hold and restart timeout on charger attached
                if chargerconnected == 1:
                    self.time_limit = time.time() + 100000
                    self._hold_timeout = True
                if chargerconnected == 0 and self._hold_timeout:
                    self.time_limit = time.time() + timeout
                    self._hold_timeout = False

                # Reset timeout on unPauseEvents
                if self._events_paused:
                    self.time_limit = time.time() + timeout
                    self._events_paused = False

                button_pressed = 0

                if not self._stand_by:
                    # Hold fields activity on standby
                    try:

                        self.send_packet(b'\x83', b'')
                        
                        expected = bytearray(b'\x85\x00\x06'
                                             + self.address_1.to_bytes(1, byteorder='big') 
                                             + self.address_2.to_bytes(1, byteorder='big'))
                        
                        expected.append(_checksum(expected))
                        
                        response = bytearray(self.read_serial())
                        
                        if (bytearray(response) != expected):
                            if (len(response) > 1 and response[0] == 133 and response[1] == 0):
                                for x in range(0, len(response) - 1):
                                    
                                    if (response[x] == 64):
                                        # Calculate the square to 0(a1)-63(h8) so that
                                        # all functions match
                                        field_hex = response[x + 1]
                                        new_square = _rotate_field_hex(field_hex)
                                        
                                        if self._field_callback:
                                            self._field_callback(new_square + 1)
                                        
                                        self.time_limit = time.time() + timeout
                                    
                                    if (response[x] == 65):
                                        # Calculate the square to 0(a1)-63(h8) so that
                                        # all functions match
                                        field_hex = response[x + 1]
                                        new_square = _rotate_field_hex(field_hex)
                                        
                                        if self._field_callback:
                                            self._field_callback((new_square + 1) * -1)
                                        
                                        self.time_limit = time.time() + timeout

                    
                    except Exception as e:
                        print(e)
                        Log.exception(CentaurBoard.events_board_thread, e)
                        pass
            
                try:
                    self.send_packet(b'\x94', b'')
                    
                    expected = bytearray(b'\xb1\x00\x06' 
                                         + self.address_1.to_bytes(1, byteorder='big') 
                                         + self.address_2.to_bytes(1, byteorder='big'))
                
                    expected.append(_checksum(expected))
                    
                    response = bytearray(self.read_serial())
                
                    if not self._stand_by:

                        #Disable these buttons on standby
                        if (response.hex()[:-2] == "b10011" 
                            + "{:02x}".format(self.address_1) 
                            + "{:02x}".format(self.address_2) 
                            + "00140a0501000000007d47"):

                            self.time_limit = time.time() + timeout
                            button_pressed = BTNBACK

                        if (response.hex()[:-2] == "b10011" 
                            + "{:02x}".format(self.address_1) 
                            + "{:02x}".format(self.address_2) 
                            + "00140a0510000000007d17"):

                            self.time_limit = time.time() + timeout
                            button_pressed = BTNTICK

                        if (response.hex()[:-2] == "b10011" 
                            + "{:02x}".format(self.address_1) 
                            + "{:02x}".format(self.address_2) 
                            + "00140a0508000000007d3c"):

                            self.time_limit = time.time() + timeout
                            button_pressed = BTNUP

                        if (response.hex()[:-2] == "b10010" 
                            + "{:02x}".format(self.address_1) 
                            + "{:02x}".format(self.address_2) 
                            + "00140a05020000000061"):

                            self.time_limit = time.time() + timeout
                            button_pressed = BTNDOWN

                        if (response.hex()[:-2] == "b10010" 
                            + "{:02x}".format(self.address_1) 
                            + "{:02x}".format(self.address_2) 
                            + "00140a0540000000006d"):

                            self.time_limit = time.time() + timeout
                            button_pressed = BTNHELP
                    
                    if (response.hex()[:-2] == "b10010" 
                        + "{:02x}".format(self.address_1) 
                        + "{:02x}".format(self.address_2) 
                        + "00140a0504000000002a"):

                        breaktime = time.time() + 0.5

                        while time.time() < breaktime:
                            self.send_packet(b'\x94', b'')
                            
                            expected = bytearray(b'\xb1\x00\x06' 
                                                 + self.address_1.to_bytes(1, byteorder='big') 
                                                 + self.address_2.to_bytes(1, byteorder='big'))
                            expected.append(_checksum(expected))
                            
                            response = self.read_serial()
                            response = bytearray(response)
                            
                            if response.hex().startswith("b10011" 
                                                         + "{:02x}".format(self.address_1) 
                                                         + "{:02x}".format(self.address_2) 
                                                         + "00140a0500040"):
                        
                                print('Play btn pressed. Stanby is:',self._stand_by)
                                if self._stand_by == False:
                                    print('Calling standbyScreen()')
                                    #epaper.standbyScreen(True)
                                    self._stand_by = True
                                    print('Starting shutdown countdown')
                                    #sd = threading.Timer(600,shutdown)
                                    #sd.start()
                                    self.time_limit = time.time() + 100000
                                    break
                                else:
                                    self.clear_serial()
                                    #epaper.standbyScreen(False)
                                    print('Cancel shutdown')
                                    #sd.cancel()
                                    self._stand_by = False
                                    self.time_limit = time.time() + timeout
                                    break
                                break
                        else:
                            self.beep(SOUND_POWER_OFF)
                            #shutdown()
                except Exception as e:
                    print(e)
                    Log.exception(CentaurBoard.events_board_thread, e)
                pass

                try:
                    # Sending 152 to the controller provides us with battery information
                    # Do this every 30 seconds and fill in the globals
                    if time.time() - batterylastchecked > 15:
                        # Every 5 seconds check the battery details
                        response = ""
                        timeout = time.time() + 4
                        while len(response) < 7 and time.time() < timeout:
                            # Sending the board a packet starting with 152 gives battery info
                            self.send_packet(bytearray([152]), b'')
                            try:
                                response = self.read_serial()
                            except:
                                pass
                        if len(response) < 7:
                            pass
                        else:        
                            if response[0] == 181:                            
                                batterylastchecked = time.time()
                                batterylevel = response[5] & 31
                                vall = (response[5] >> 5) & 7                            
                                if vall == 1 or vall == 2:
                                    chargerconnected = 1
                                else:
                                    chargerconnected = 0
                except Exception as e:
                    print(e)
                    Log.exception(CentaurBoard.events_board_thread, e)
                pass
                time.sleep(0.05)
                if button_pressed != 0:
                    self.time_limit = time.time() + timeout
                   
                    if self._key_callback:
                        self._key_callback(button_pressed)
            else:
                # If pauseEvents() hold timeout in the thread
                self.time_limit = time.time() + 100000
                self._events_paused = True

            if time.time() - loopstart > 30:
                self.time_limit = time.time() + timeout
            time.sleep(0.05)
        else:

            if self._events_running:

                print('Timeout. Shutting down...')
                #shutdown()




def get():
    return CentaurBoard().initialize()

"""
FOOBAR.clear_serial()
FOOBAR.clear_board_data()

FOOBAR.print_board_state()

FOOBAR.led(32)
FOOBAR.led_flash()
FOOBAR.led(33)
FOOBAR.led_flash()
FOOBAR.led_from_to(2,41)
FOOBAR.led_array([1,2,3,4,5,22,23,24])

FOOBAR.leds_off()

ser = FOOBAR.serial()
"""


def shutdown():
    """
    update = centaur.UpdateSystem()
    beep(SOUND_POWER_OFF)
    package = '/tmp/dgtcentaurmods_armhf.deb'
    if os.path.exists(package):
        ledArray([0,1,2,3,4,5,6,7],6)
        epaper.clearScreen()
        update.updateInstall()
        return
    print('Normal shutdown')
    epaper.clearScreen()
    time.sleep(1)
    ledFromTo(7,7)
    epaper.writeText(3, "     Shutting")
    epaper.writeText(4, "       down")
    time.sleep(3)
    epaper.stopEpaper()
    os.system("sudo poweroff")
    """





#
# Board response - functions related to get something from the board
#

"""
def waitMove():
    # Wait for a player to lift a piece and set it down somewhere different
    lifted = -1
    placed = -1
    moves = []
    while placed == -1:
        ser.read(100000)
        sendPacket(b'\x83', b'')
        expect = buildPacket(b'\x85\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
        if (bytearray(resp) != expect):
            if (resp[0] == 133 and resp[1] == 0):
                for x in range(0, len(resp) - 1):
                    if (resp[x] == 64):
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        newsquare = _rotate_field_hex(fieldHex)
                        lifted = newsquare
                        print(lifted)
                        moves.append((newsquare+1) * -1)
                    if (resp[x] == 65):
                        # Calculate the square to 0(a1)-63(h8) so that
                        # all functions match
                        fieldHex = resp[x + 1]
                        newsquare = _rotate_field_hex(fieldHex)
                        placed = newsquare
                        moves.append(newsquare + 1)
                        print(placed)
        sendPacket(b'\x94', b'')
        expect = buildPacket(b'\xb1\x00\x06', b'')
        resp = ser.read(10000)
        resp = bytearray(resp)
    print(moves)
    return moves

def poll():
    # We need to continue poll the board to get data from it
    # Perhaps there's a packet length in here somewhere but
    # I haven't noticed it yet, therefore we need to process
    # the data as it comes
    ser.read(100000)
    sendPacket(b'\x83', b'')
    expect = buildPacket(b'\x85\x00\x06', b'')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (bytearray(resp) != expect):
        if (resp[0] == 133 and resp[1] == 0):
            for x in range(0, len(resp) - 1):
                if (resp[x] == 64):
                    print("PIECE LIFTED")
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = _rotate_field_hex(fieldHex)
                    print(newsquare)
                if (resp[x] == 65):
                    print("PIECE PLACED")
                    # Calculate the square to 0(a1)-63(h8) so that
                    # all functions match
                    fieldHex = resp[x + 1]
                    newsquare = _rotate_field_hex(fieldHex)
                    print(newsquare)
    sendPacket(b'\x94', b'')
    expect = buildPacket(b'\xb1\x00\x06', b'')
    resp = ser.read(10000)
    resp = bytearray(resp)
    if (resp != expect):
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a0501000000007d47"):
            print("BACK BUTTON")
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a0510000000007d17"):
            print("TICK BUTTON")
        if (resp.hex()[:-2] == "b10011" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a0508000000007d3c"):
            print("UP BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a05020000000061"):
            print("DOWN BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a0540000000006d"):
            print("HELP BUTTON")
        if (resp.hex()[:-2] == "b10010" + "{:02x}".format(address_1) + "{:02x}".format(address_2) + "00140a0504000000002a"):
            print("PLAY BUTTON")



def getChargingState():
    # Returns if the board is plugged into the charger or not
    # 0 = not plugged in, 1 = plugged in, -1 = error in checking
    resp = ""
    timeout = time.time() + 5
    while len(resp) < 7 and time.time() < timeout:
        # Sending the board a packet starting with 152 gives battery info
        sendPacket(bytearray([152]), b'')
        try:
            resp = ser.read(1000)
        except:
            pass
        if len(resp) < 7:
            pass
        else:  
            if resp[0] == 181:
                print("connected state")
                print(resp.hex())                
                vall = (resp[5] >> 5) & 7
                print(vall)
                if vall == 1:
                    return 1
                else:
                    return 0
    return - 1

def getBatteryLevel():
    # Returns a number 0 - 20 representing battery level of the board
    # 20 is fully charged. The board dies somewhere around a low of 1
    resp = ""
    timeout = time.time() + 5
    while len(resp) < 7 and time.time() < timeout:
        # Sending the board a packet starting with 152 gives battery info
        sendPacket(bytearray([152]), b'')
        try:
            resp = ser.read(1000)
        except:
            pass
    if len(resp) < 7:
        return -1
    else:        
        if resp[0] == 181:
            print(resp.hex())
            vall = resp[5] & 31
            return vall
        else:
            # fix for when battery returns as None on first attempt
            return getBatteryLevel()

#
# Miscellaneous functions - do they belong in this file?
#

def checkInternetSocket(host="8.8.8.8", port=53, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False






# This section is the start of a new way of working with the board functions where those functions are
# the board returning some kind of data
import threading
eventsthreadpointer = None
eventsrunning = 1

def temp():
    '''
    Get CPU temperature
    '''
    temp = os.popen("vcgencmd measure_temp | cut -d'=' -f2").read().strip()
    return temp

"""






    





