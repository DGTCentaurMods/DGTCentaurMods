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

from DGTCentaurMods.display import epd2in9d

from DGTCentaurMods.game.classes import Log

from DGTCentaurMods.game.classes.Clock import Clock

from DGTCentaurMods.game.consts import consts, fonts
from DGTCentaurMods.game.lib import common

from PIL import Image, ImageDraw

import threading, time

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 296

HEADER_HEIGHT = 20

B_W_MODE = '1'

MAIN_SCREEN_IMAGE = Image.open(consts.OPT_DIRECTORY + "/resources/logo_mods_screen.jpg"),(0,0)
CHESS_SHEET_IMAGE = Image.open(consts.OPT_DIRECTORY + "/resources/chesssprites.bmp")

class CentaurScreen(common.Singleton):

    _buffer = None
    _buffer_copy = None
    _thread_worker = None
    _api = None

    _wclock = None
    _bclock = None

    _thread_is_alive = True

    _last_buffer_bytes = bytearray(b'')

    _screen_reversed = False
    _screen_enabled = True

    _clocks_enabled = False

    _battery_value = -1 # -1 means "charging"

    def initialize(self):

        if self._api == None:

            print("Centaur screen initializing...")

            self._api = epd2in9d.EPD()

            self._buffer = Image.new(B_W_MODE, (SCREEN_WIDTH, SCREEN_HEIGHT), 255)

            self._api.init()
            time.sleep(1)
            self._api.Clear(0xff)
            time.sleep(2)

            self.home_screen("Welcome!")

            self.screen_thread_worker = threading.Thread(target=self._screen_thread, args=())
            self.screen_thread_worker.daemon = True
            self.screen_thread_worker.start()

            print("Centaur screen initialized.")

        return self
    
    def set_reversed(self, value):
        self._screen_reversed = value
    
    def set_battery_value(self, value):
        self._battery_value = value

    def push_clock(self, color):
        
        if self._wclock and self._bclock:
            if color:
                self._wclock.resume()
                self._bclock.pause()
            else:
                self._bclock.resume()
                self._wclock.pause()

    def intialize_clocks(self, wtime = None, btime = None):
        
        if wtime:
            # First call - clocks need to be initialized
            if self._wclock == None:
                self._wclock = Clock(wtime)
                self._bclock = Clock(wtime)

            self._wclock.set(wtime)

        if btime and self._bclock:
            self._bclock.set(btime)

    def enable_clocks(self, value):
        
        self._clocks_enabled = value

        if not value:
            self._wclock = None
            self._bclock = None

    def stop_clocks(self):
        
        if self._wclock and self._bclock:
            self._bclock.pause()
            self._wclock.pause()

    def _screen_thread(self):

        self._api.display(self._api.getbuffer(self._buffer))

        time.sleep(3)
        
        while self._thread_is_alive:
            buffer_copy = self._buffer.copy()

            if self._screen_enabled:

                # Header time
                clock = time.strftime("%H:%M")
                self.write_text(0, clock, centered=False)

                # Player clocks
                if self._clocks_enabled:
                    if self._wclock:
                        self.write_text(13, self._wclock.get().strftime("%M:%S"), font=fonts.DIGITAL_FONT)
                    else:
                        self.write_text(13, Clock.zero().strftime("%M:%S"), font=fonts.DIGITAL_FONT)

                    if self._bclock:
                        self.write_text(10, self._bclock.get().strftime("%M:%S"), font=fonts.DIGITAL_FONT)
                    else:
                        self.write_text(10, Clock.zero().strftime("%M:%S"), font=fonts.DIGITAL_FONT)

                # Connected battery
                bi = "batteryc"

                if self._battery_value >= 0:
                    bi = "battery" + str(int(self._battery_value / 5))

                img = Image.open(consts.OPT_DIRECTORY + f"/resources/{bi}.bmp")
                buffer_copy.paste(img,(98, 2)) 

                buffer_bytes = buffer_copy.tobytes()

                # Change detected?
                if self._last_buffer_bytes != buffer_bytes:

                    if self._screen_reversed == False:
                        buffer_copy = buffer_copy.transpose(Image.FLIP_TOP_BOTTOM)
                        buffer_copy = buffer_copy.transpose(Image.FLIP_LEFT_RIGHT)
                    
                    self._api.DisplayPartial(self._api.getbuffer(buffer_copy))
                
                    self._last_buffer_bytes = buffer_bytes

            time.sleep(.25)

    def pause(self):
        self._screen_enabled = False
        #self._api.sleep()

    def unpause(self):
        self._screen_enabled = True
        #self._api.TurnOnDisplay()

    def save_screen(self):
        
        self._buffer_copy = self._buffer.copy()

    def restore_screen(self):

        self._buffer = self._buffer_copy.copy()

    def home_screen(self, text=None):

        logo = Image.open(consts.OPT_DIRECTORY + "/resources/logo_mods_screen.jpg")
        self._buffer.paste(logo,(0,HEADER_HEIGHT))
        if text:
            self.write_text(10,text)

    def system_message(self, message):
        self.write_text(1, message)

    def write_text(self, row, text, font=fonts.MAIN_FONT, centered=True, bordered=False, radius=8, option=None):

        if option != None or bordered:
            font=fonts.SMALL_FONT

        i = Image.new(B_W_MODE, (0, 0), 255)
        canvas = ImageDraw.Draw(i)
        _, _, text_width, text_height = canvas.textbbox(xy=(0, 0), text=text, font=font)

        del canvas
        del i

        buffer_copy = self._buffer.copy()
        i = Image.new(B_W_MODE, (SCREEN_WIDTH, text_height+4), 255)
        
        canvas = ImageDraw.Draw(i)

        # Too large text?
        if text_width>SCREEN_WIDTH and font!=fonts.SMALL_FONT:
            font=fonts.SMALL_FONT
            _, _, text_width, text_height = canvas.textbbox(xy=(0, 0), text=text, font=font)

        if bordered:
            canvas.rounded_rectangle([(0,0),(SCREEN_WIDTH -1,text_height)],radius=radius,fill="white",outline='black', width=1)

        offset_x = int((SCREEN_WIDTH-text_width)/2 if centered or bordered else 0) if option == None else 15

        canvas.text((offset_x, 0), text=text, font=font, fill=0)

        if option != None:
            canvas.ellipse((0, 1, 10, 11), fill = 'white', outline ='black', width=1)
            if option:
                canvas.ellipse((2, 3, 8, 9), fill = 'black', outline ='black', width=1)

        buffer_copy.paste(i, box=(0, int(row * HEADER_HEIGHT)))
        
        self._buffer = buffer_copy.copy()

    def draw_rectangle(self, x1, y1, x2, y2, fill=None, outline=None, width=1):

        canvas = ImageDraw.Draw(self._buffer)
        canvas.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline, width=width)

    def clear_area(self, x1 = 0, y1 = 0, x2 = SCREEN_WIDTH, y2 = SCREEN_HEIGHT):

        self.draw_rectangle(x1,y1,x2,y2,255,255)
        time.sleep(.2)

    def draw_fen(self, fen, startrow=2):

        try:
            fen = fen.replace("/", "")

            for index in range(1,9):
                fen = fen.replace(str(index), " "*index)

            reversed = ""
            for a in range(8,0,-1):
                for b in range(0,8):
                    reversed = reversed + fen[((a-1)*8)+b]

            self.draw_board(reversed, startrow)

        except Exception as e:
            Log.debug(f"fen:{fen}")
            Log.exception(CentaurScreen.draw_fen, e)
            pass

    def draw_back_button(self, canvas, x):
        canvas.line(
            (x,16,x+16,16), fill=0, width=5)
        canvas.line(
            (x+14,16,x+14,5), fill=0, width=5)
        canvas.line(
            (x+16,6,x+4,6), fill=0, width=5)
        canvas.polygon(
            [(x+8, 2), (x+8, 10), (x, 6)], fill=0)

    def draw_tick_button(self, canvas, x):
        canvas.line(
            (x+6,16,x+16,4), fill=0, width=5)
        canvas.line(
            (x+2,10, x+8,16), fill=0, width=5)

    def draw_resignation_window(self):

        try:

            self.draw_rectangle(0,HEADER_HEIGHT*2,SCREEN_WIDTH-1,8.2*HEADER_HEIGHT, fill=255)

            self.write_text(1,' '*20)
            self.write_text(2,"Do you really")
            self.write_text(3,"want to")
            self.write_text(4,"resign?")
            self.write_text(5,' '*20)
            self.write_text(6,"NO    YES")

            image = Image.new(B_W_MODE, (SCREEN_WIDTH, HEADER_HEIGHT), 255)

            canvas = ImageDraw.Draw(image)

            self.draw_back_button(canvas, 28)
            self.draw_tick_button(canvas, 82)

            self._buffer.paste(image, (0, (7 * HEADER_HEIGHT)))

            self.draw_rectangle(0,HEADER_HEIGHT*2,SCREEN_WIDTH-1,8.2*HEADER_HEIGHT)

        except Exception as e:
            Log.exception(CentaurScreen.draw_resignation_window, e)

    def draw_promotion_window(self):

        #TODO Promotion screen to be reviewed

        try:
            row = 5
            image = Image.new(B_W_MODE, (SCREEN_WIDTH, HEADER_HEIGHT), 255)

            canvas = ImageDraw.Draw(image)
            canvas.text((0, 0), "    Q    R    N   B", font=fonts.MAIN_FONT, fill=0)
            canvas.polygon([(2, 18), (18, 18), (10, 3)], fill=0)
            canvas.polygon([(35, 3), (51, 3), (43, 18)], fill=0)
            o = 66
            canvas.line((0+o,16,16+o,16), fill=0, width=5)
            canvas.line((14+o,16,14+o,5), fill=0, width=5)
            canvas.line((16+o,6,4+o,6), fill=0, width=5)
            canvas.polygon([(8+o, 2), (8+o, 10), (0+o, 6)], fill=0)
            o = 97
            canvas.line((6+o,16,16+o,4), fill=0, width=5)
            canvas.line((2+o,10, 8+o,16), fill=0, width=5)

            self._buffer.paste(image, (0, (row * HEADER_HEIGHT)))

            self.write_text(2,"Choose")
            self.write_text(3,"your")
            self.write_text(4,"promotion!")

        except Exception as e:
            Log.exception(CentaurScreen.draw_promotion_window, e)

    def draw_board(self, pieces, start_row=2, is_keyboard=False):

        try:

            for square in range(0,64):
                
                index = (square - 63) * -1

                row = int(((start_row * HEADER_HEIGHT) + 8) + (16 * (index // 8)))
                col = int((square % 8) * 16)

                r = square // 8
                c = square % 8

                offset_y = 0

                if ((r // 2 == r / 2 and c // 2 == c / 2) or
                    (r // 2 != r / 2 and c // 2 != c / 2)):

                    offset_y = offset_y + 16

                offset_x = 0 if is_keyboard else {" ":0,"P":16,"R":32,"N":48,"B":64,"Q":80,"K":96,"p":112,"r":128,"n":144,"b":160,"q":176,"k":192} [pieces[square]]

                piece_image = CHESS_SHEET_IMAGE.crop((offset_x, offset_y, offset_x+16, offset_y+16))

                if is_keyboard and index<len(pieces):
                    ImageDraw.Draw(piece_image).text((4, 0), pieces[index], font=fonts.SMALL_FONT, fill=0)

                self._buffer.paste(piece_image,(col,row))
                
        except Exception as e:
            Log.exception(CentaurScreen.draw_board, e)

    def draw_evaluation_bar(self, row=8.5, value=0, text=None, disabled=False, font=fonts.SMALL_FONT):

        if disabled:
            text = "evaluation disabled"

        if text:
            self.write_text(row, text, font=font, bordered=True)
            return
        
        canvas = ImageDraw.Draw(self._buffer)

        MAX_VALUE = 800
        HEIGHT = 14
        PADDING = 6
        BAR_WIDTH = SCREEN_WIDTH - (PADDING*2)

        value = MAX_VALUE if disabled or text != None else value

        value = +MAX_VALUE if value>+MAX_VALUE else value
        value = -MAX_VALUE if value<-MAX_VALUE else value

        offset = (-(value/MAX_VALUE) * BAR_WIDTH *.5) + (BAR_WIDTH *.5)

        y = row * HEADER_HEIGHT

        canvas.rounded_rectangle([(0,y),(127,y+HEIGHT)],radius=8, fill="white",outline='black', width=1)
        canvas.rectangle([(PADDING,y+(PADDING *.5)),(127-PADDING,y+HEIGHT-(PADDING *.5))],fill="white",outline='black', width=1)
        canvas.rectangle([(PADDING,y+(PADDING *.5)),(PADDING+offset,y+HEIGHT-(PADDING *.5))],fill="black",outline='black', width=1)


def get():
    return CentaurScreen().initialize()