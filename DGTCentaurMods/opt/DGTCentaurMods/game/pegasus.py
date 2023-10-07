# DGT Centaur Pegasus Emulation
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

import dbus
from DGTCentaurMods.thirdparty.advertisement import Advertisement
from DGTCentaurMods.thirdparty.service import Application, Service, Characteristic, Descriptor
from DGTCentaurMods.board import *
from DGTCentaurMods.display.ui_components import AssetManager
import time
import threading
import os
import pathlib
from DGTCentaurMods.board import *
from DGTCentaurMods.display import epaper
from PIL import Image, ImageDraw

kill = 0

epaper.initEpaper()

for x in range(0,10):
    board.sendPacket(b'\x83', b'')
    expect = board.buildPacket(b'\x85\x00\x06', b'')
    resp = board.ser.read(10000)
    resp = bytearray(resp)
    board.sendPacket(b'\x94', b'')
    expect = board.buildPacket(b'\xb1\x00\x06', b'')
    resp = board.ser.read(10000)
    resp = bytearray(resp)

statusbar = epaper.statusBar()
statusbar.start()

def displayLogo():
    filename = str(AssetManager.get_resource_path("logo_mods_screen.jpg"))
    lg = Image.open(filename)
    lg = lg.resize((48,112))
    return epaper.epaperbuffer.paste(lg,(0,20))

statusbar.print()
epaper.writeText(1,"           PEGASUS")
epaper.writeText(2,"              MODE")
epaper.writeText(10,"PCS-REVII-081500")
epaper.writeText(11,"Use back button")
epaper.writeText(12,"to exit mode")
epaper.writeText(13,"Await Connect")
displayLogo()

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000
DGT_MSG_BOARD_DUMP = 134
DGT_MSG_FIELD_UPDATE = 142
DGT_MSG_UNKNOWN_143 = 143
DGT_MSG_UNKNOWN_144 = 144
DGT_MSG_SERIALNR = 145
DGT_MSG_TRADEMARK = 146
DGT_MSG_VERSION = 147
DGT_MSG_HARDWARE_VERSION = 150
DGT_MSG_BATTERY_STATUS = 160
DGT_MSG_LONG_SERIALNR = 162
DGT_MSG_UNKNOWN_163 = 163
DGT_MSG_LOCK_STATE = 164
DGT_MSG_DEVKEY_STATE = 165

class UARTAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("PCS-REVII-081500")
        #self.add_local_name("DGT_PEGASUS_EMULATION")
        self.include_tx_power = True
        self.add_service_uuid("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")

class UARTService(Service):

    tx_obj = None

    UART_SVC_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"

    def __init__(self, index):
        Service.__init__(self, index, self.UART_SVC_UUID, True)
        self.add_characteristic(UARTTXCharacteristic(self))
        self.add_characteristic(UARTRXCharacteristic(self))

class UARTRXCharacteristic(Characteristic):
    UARTRX_CHARACTERISTIC_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

    def __init__(self, service):

        Characteristic.__init__(
                self, self.UARTRX_CHARACTERISTIC_UUID,
                ["write"], service)

    def sendMessage(self, msgtype, data):
        # Send a message of the given type
        tosend = bytearray()
        # First the message type, then the length
        tosend.append(msgtype)
        lo = (len(data)+3) & 127
        hi = ((len(data)+3) >> 7) & 127
        tosend.append(hi)
        tosend.append(lo)
        for x in range(0, len(data)):
            tosend.append(data[x])
        UARTService.tx_obj.updateValue(tosend)

    def WriteValue(self, value, options):
        # When the remote device writes data, it comes here
        print("Received")
        print(value)
        bytes = bytearray()
        for i in range(0,len(value)):
            bytes.append(value[i])
        print(len(bytes))
        print(bytes)
        processed = 0
        if len(bytes) == 1 and bytes[0] == ord('B'):
            bs = board.getBoardState()
            self.sendMessage(DGT_MSG_BOARD_DUMP, bs)
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('D'):
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('E'):
            self.sendMessage(DGT_MSG_SERIALNR, [ord('A'),ord('B'),ord('C'),ord('D'),ord('E')])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('F'):
            self.sendMessage(DGT_MSG_UNKNOWN_144, [0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('G'):
            # Return a DGT_MSG_TRADEMARK but it must contain
            # Digital Game Technology\r\nCopyright (c)
            tm = b'Digital Game Technology\r\nCopyright (c) 2021 DGT\r\nsoftware version: 1.00, build: 210722\r\nhardware version: 1.00, serial no: PXXXXXXXXX'
            self.sendMessage(DGT_MSG_TRADEMARK, tm)
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('H'):
            self.sendMessage(DGT_MSG_HARDWARE_VERSION,[1,0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('I'):
            self.sendMessage(DGT_MSG_UNKNOWN_143, [])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('L'):
            self.sendMessage(DGT_MSG_BATTERY_STATUS, [0x58,0,0,0,0,0,0,0,2])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('M'):
            self.sendMessage(DGT_MSG_VERSION, [1,0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('U'):
            self.sendMessage(DGT_MSG_LONG_SERIALNR, [ord('A'),ord('B'),ord('C'),ord('D'),ord('E'),ord('F'),ord('G'),ord('H'),ord('I'),ord('J')])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('V'):
            self.sendMessage(DGT_MSG_UNKNOWN_163, [0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('Y'):
            self.sendMessage(DGT_MSG_LOCK_STATE, [0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('Z'):
            self.sendMessage(DGT_MSG_DEVKEY_STATE, [0])
            processed = 1
        if len(bytes) == 1 and bytes[0] == ord('@'):
            # This looks like some sort of reset, but it is used mid game after a piece has been moved sometimes.
            # Maybe it does something with LEDs as it was followed by a switching off leds
            # Let's report the battery status here - 0x58 (or presumably higher as there is rounding) = 100%
            # As I can't read centaur battery percentage here - fake it
            self.sendMessage(DGT_MSG_BATTERY_STATUS, [0x58,0,0,0,0,0,0,0,2])
            processed=1
        if bytes[0] == 99:
            # This registers the board with a developer key. No clue what this actually does
            msg = b'\x01' # Guessing, this isn't checked
            self.sendMessage(DGT_MSG_DEVKEY_STATE, msg)
            processed=1
        if len(bytes) == 4:
            if bytes[0] == 96 and bytes[1] == 2 and bytes[2] == 0 and bytes[3] == 0:
                # ledsOff
                print("leds off")
                board.ledsOff()
                # Let's report the battery status here - 0x58 (or presumably higher as there is rounding) = 100%
                # As I can't read centaur battery percentage here - fake it
                self.sendMessage(DGT_MSG_BATTERY_STATUS, [0x58,0,0,0,0,0,0,0,2])
                processed=1
        if processed == 0 and bytes[0] == 96:
            # LEDS stuff
            # 96, [Packet data length - 2], 5(light leds), LedSpeed, 0 or 1 is 0 except in moveLed or checkLed, Intensity, ...field ids, 0
            print("Received LED command")
            if bytes[2] == 5:
                ledspeed = bytes[3]
                intensity = bytes[5]
                data = bytearray()
                data.append(5)
                data.append(ledspeed)
                data.append(0)
                data.append(intensity)
                print(data.hex())
                for x in range(6,len(bytes)-1):
                    # This is looping through the leds to light
                    data.append(bytes[x])
                head = bytearray()
                head.append(176)
                head.append(0)
                head.append(len(data)+6)
                print(head.hex())
                print(data.hex())
                board.ledsOff()
                board.sendPacket(head,data)
                if bytes[4] == 1:
                    time.sleep(0.5)
                    board.ledsOff()
                # Let's report the battery status here - 0x58 (or presumably higher as there is rounding) = 100%
                # As I can't read centaur battery percentage here - fake it
                #msg = b'\x58'
                #self.sendMessage(DGT_MSG_BATTERY_STATUS, msg)
                processed=1
        if processed==0:
            print("Un-coded command")
            UARTService.tx_obj.updateValue(bytes)


class UARTTXCharacteristic(Characteristic):
    UARTTX_CHARACTERISTIC_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    def __init__(self, service):

        Characteristic.__init__(
                self, self.UARTTX_CHARACTERISTIC_UUID,
                ["read", "notify"], service)
        self.notifying = False
        print("setting timeout")
        self.add_timeout(300, self.checkBoard)

    def checkBoard(self):
        if self.notifying == True:
            board.sendPacket(b'\x83', b'')
            expect = board.buildPacket(b'\x85\x00\x06', b'')
            resp = board.ser.read(10000)
            resp = bytearray(resp)
            if (bytearray(resp) != expect):
                if (resp[0] == 133 and resp[1] == 0):
                    for x in range(0, len(resp) - 1):
                        if (resp[x] == 64):
                            fieldHex = resp[x + 1]
                            msg = bytearray()
                            msg.append(fieldHex)
                            msg.append(0)
                            self.sendMessage(DGT_MSG_FIELD_UPDATE, msg)
                            #msg = b'\x58'
                            #self.sendMessage(DGT_MSG_BATTERY_STATUS, msg)
                        if (resp[x] == 65):
                            fieldHex = resp[x + 1]
                            msg = bytearray()
                            msg.append(fieldHex)
                            msg.append(1)
                            self.sendMessage(DGT_MSG_FIELD_UPDATE, msg)
                            #msg = b'\x58'
                            #self.sendMessage(DGT_MSG_BATTERY_STATUS, msg)
            board.sendPacket(b'\x94', b'')
            expect = board.buildPacket(b'\xb1\x00\x06', b'')
            resp = board.ser.read(10000)
            resp = bytearray(resp)
            if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
                print("Back button pressed")
                # os.system('sudo service bluetooth restart')
                app.quit()
        else:
            board.sendPacket(b'\x83', b'')
            expect = board.buildPacket(b'\x85\x00\x06', b'')
            resp = board.ser.read(10000)
            board.sendPacket(b'\x94', b'')
            expect = board.buildPacket(b'\xb1\x00\x06', b'')
            resp = board.ser.read(10000)
            resp = bytearray(resp)
            if (resp.hex()[:-2] == "b10011" + "{:02x}".format(board.addr1) + "{:02x}".format(board.addr2) + "00140a0501000000007d47"):
                print("Back button pressed")
                # os.system('sudo service bluetooth restart')
                app.quit()
        return True

    def sendMessage(self, msgtype, data):
        # Send a message of the given type
        tosend = bytearray()
        # First the message type, then the length
        tosend.append(msgtype)
        lo = (len(data)+3) & 127
        hi = ((len(data)+3) >> 7) & 127
        tosend.append(hi)
        tosend.append(lo)
        for x in range(0, len(data)):
            tosend.append(data[x])
        UARTService.tx_obj.updateValue(tosend)

    def StartNotify(self):
        print("started notifying")
        epaper.writeText(13, "              ")
        epaper.writeText(13, "Connected")
        board.clearSerial()
        board.clearBoardData()
        board.beep(board.SOUND_GENERAL)
        UARTService.tx_obj = self
        self.notifying = True
        board.ledsOff()
        # Let's report the battery status here - 0x58 (or presumably higher as there is rounding) = 100%
        # As I can't read centaur battery percentage here - fake it
        #msg = b'\x58'
        #self.sendMessage(DGT_MSG_BATTERY_STATUS, msg)
        return self.notifying

    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
        return self.notifying

    def updateValue(self,value):
        if not self.notifying:
            return
        send = dbus.Array(signature=dbus.Signature('y'))
        for i in range(0,len(value)):
            send.append(dbus.Byte(value[i]))
        self.PropertiesChanged( GATT_CHRC_IFACE, { 'Value': send }, [])

    def ReadValue(self, options):
        value = 1
        return value

app = Application()
app.add_service(UARTService(0))
app.register()

adv = UARTAdvertisement(0)
adv.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
