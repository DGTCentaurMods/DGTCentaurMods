# DGT Centaur BLE Control
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
import time
import threading
import random

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class UARTAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("PCS-REVII-081500")
        self.include_tx_power = True
        self.add_service_uuid("5f040001-5866-11ec-bf63-0242ac130002")

class UARTService(Service):

    tx_obj = None

    UART_SVC_UUID = "5f040001-5866-11ec-bf63-0242ac130002"

    def __init__(self, index):
        Service.__init__(self, index, self.UART_SVC_UUID, True)
        self.add_characteristic(UARTTXCharacteristic(self))
        self.add_characteristic(UARTRXCharacteristic(self))

class UARTRXCharacteristic(Characteristic):
    UARTRX_CHARACTERISTIC_UUID = "5f040002-5866-11ec-bf63-0242ac130002"

    def __init__(self, service):

        Characteristic.__init__(
                self, self.UARTRX_CHARACTERISTIC_UUID,
                ["write"], service)

    def sendMessage(self, data):
        # Send a message
        tosend = bytearray()
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

class UARTTXCharacteristic(Characteristic):
    UARTTX_CHARACTERISTIC_UUID = "5f040003-5866-11ec-bf63-0242ac130002"

    def __init__(self, service):

        Characteristic.__init__(
                self, self.UARTTX_CHARACTERISTIC_UUID,
                ["read", "notify"], service)
        self.notifying = False

    def checkSend(self):
        if self.notifying == True:
            msg = bytearray()
            msg.append(random.randrange(65,90))
            print("----")
            print(msg)
            self.sendMessage(msg)
        return self.notifying

    def sendMessage(self, data):
        # Send a message
        print(data)
        tosend = bytearray()
        for x in range(0, len(data)):
            tosend.append(data[x])
        UARTService.tx_obj.updateValue(tosend)

    def StartNotify(self):
        print("started notifying")
        UARTService.tx_obj = self
        self.notifying = True
        self.add_timeout(200, self.checkSend)
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
        print("read value")
        value = bytearray()
        value.append(1)
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
