#!/usr/bin/python

# Use this tool to poll the board to find out serial respons.
# When polling the board we use two different packets. Depending on the event,
# the response will come after one of the packets.

import serial
import time

ser = serial.Serial("/dev/ttyS0", baudrate=1000000, timeout=0.2)

addr1 = 0x06
addr2 = 0x50

def checksum(barr):
    csum = 0
    for c in bytes(barr):
        csum += c
    barr_csum = (csum % 128)
    return barr_csum

def buildPacket(command, data):
    # pass command and data as bytes
    tosend = bytearray(command + addr1.to_bytes(1,byteorder='big') + addr2.to_bytes(1,byteorder='big') + data)
    tosend.append(checksum(tosend))
    return tosend

def sendPacket(command, data):
    # pass command and data as bytes
    tosend = buildPacket(command, data)
    ser.write(tosend)

def main():
    # Get the board addresses
    ser.read(1000)
    print("attempt address discovery")
    tosend = bytearray(b'\x4d')
    ser.write(tosend)
    ser.read(1000)
    tosend = bytearray(b'\x4e')
    ser.write(tosend)
    ser.read(1000)
    resp = ""
    while len(resp) < 4:
        tosend = bytearray(b'\x87\x00\x00\x07')
        ser.write(tosend)
        resp = ser.read(1000)
        if len(resp) > 3:
            addr1 = resp[3]
            addr2 = resp[4]
            print("Discovered new address")
            print(addr1)
            print(addr2)
            print(hex(addr1))
            print(hex(addr2))
            sendPacket(b'\xf4\x00\x07', b'\x7f')
            resp = ser.read(1000)
            sendPacket(b'\xf0\x00\x07', b'\x7f')
            ser.read(10000)
            resp = "         "

    while True:
        packet = buildPacket(b'\x83', b'')
        expect = bytearray(b'\x85\x00\x06' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big'))
        sendPacket(b'\x83', b'')
        print('TX 1: ' + packet.hex())
        try:
            resp = ser.read(1000)
        except:
            resp = ser.read(1000)
        if resp.hex()[:-2]  != expect.hex():
            print('RX 1: ' + resp.hex() + '\n')
        time.sleep(1)

        packet = buildPacket(b'\x94', b'')
        expect = expect = bytearray(b'\xb1\x00\x06' + addr1.to_bytes(1, byteorder='big') + addr2.to_bytes(1, byteorder='big'))
        sendPacket(b'\x94', b'')
        print('TX 2: ' + packet.hex())
        try:
            resp = ser.read(1000)
        except:
            resp = ser.read(1000)
        if resp.hex()[:-2] != expect.hex():
            print('RX 2: ' + resp.hex() + '\n')
        time.sleep(1)
        print('')

    #Close serial on Interrupt
    ser.clone()

if __name__ == '__main__':
    main()
