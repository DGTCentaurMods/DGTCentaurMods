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
from DGTCentaurMods.game.consts import consts, fonts
from DGTCentaurMods.game.lib import common

from PIL import Image, ImageDraw

import threading, pathlib, time

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 296

ROW_HEIGHT = 20

B_W_MODE = '1'

MAIN_FONT = fonts.FONT_Typewriter
SMALL_FONT = fonts.FONT_Typewriter_small

MAIN_SCREEN_IMAGE = Image.open(consts.OPT_DIRECTORY + "/resources/logo_mods_screen.jpg"),(0,0)
CHESS_SHEET_IMAGE = Image.open(consts.OPT_DIRECTORY + "/resources/chesssprites.bmp")

class CentaurScreen(common.Singleton):

    _buffer = None
    _buffer_copy = None
    _thread_worker = None
    _api = None

    _thread_is_alive = True

    _last_bytes_buffer = bytearray(b'')

    _screen_reversed = False
    _screen_enabled = True

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

            self.loading_screen("Welcome!")

            self.screen_thread_worker = threading.Thread(target=self.screen_thread, args=())
            self.screen_thread_worker.daemon = True
            self.screen_thread_worker.start()

            print("Centaur screen initialized.")

        return self
    
    def set_battery_value(self, value):
        self._battery_value = value

    def screen_thread(self):

        self._api.display(self._api.getbuffer(self._buffer))

        time.sleep(3)
        
        while self._thread_is_alive:
            buffer_copy = self._buffer.copy()

            if self._screen_enabled:

                clock = time.strftime("%H:%M")
                self.write_text(0, clock, centered=False)

                bi = "batteryc"

                if self._battery_value >= 0:
                    bi = "battery1"

                if self._battery_value >= 6:
                    bi = "battery2"
                
                if self._battery_value >= 12:
                    bi = "battery3"

                if self._battery_value >= 18:
                    bi = "battery4"

                if self._battery_value == 20:
                    bi = "batterycf"

                img = Image.open(consts.OPT_DIRECTORY + f"/resources/{bi}.bmp")
                buffer_copy.paste(img,(98, 2)) 


                buffer_bytes = buffer_copy.tobytes()

                # Change detected?
                if self._last_bytes_buffer != buffer_bytes:

                    if self._screen_reversed == False:
                        buffer_copy = buffer_copy.transpose(Image.FLIP_TOP_BOTTOM)
                        buffer_copy = buffer_copy.transpose(Image.FLIP_LEFT_RIGHT)
                    
                    self._api.DisplayPartial(self._api.getbuffer(buffer_copy))
                
                    self._last_bytes_buffer = buffer_bytes

            time.sleep(.25)

    def pause(self):
        self._screen_enabled = False

    def unpause(self):
        self._screen_enabled = True

    def stop(self):

        image = Image.new(B_W_MODE, (SCREEN_WIDTH, SCREEN_HEIGHT), 255)

        image.paste(MAIN_SCREEN_IMAGE,(0,0))

        self._buffer = image.copy()

        time.sleep(3)
        self._thread_is_alive = False

        self.screen_thread.join()

        time.sleep(2)
        self._api.sleep()

    def kill(self):
        self._thread_is_alive = False

    def save_screen(self):
        
        self._buffer_copy = self._buffer.copy()

    def restore_screen(self):

        self._buffer = self._buffer_copy.copy()

    def loading_screen(self, text=None):

        logo = Image.open(consts.OPT_DIRECTORY + "/resources/logo_mods_screen.jpg")
        self._buffer.paste(logo,(0,ROW_HEIGHT))
        if text:
            self.write_text(10,text)

    def write_text(self, row, text, font=MAIN_FONT, centered=True, bordered=False):

        buffer_copy = self._buffer.copy()
        image = Image.new(B_W_MODE, (SCREEN_WIDTH, ROW_HEIGHT), 255)
        
        draw = ImageDraw.Draw(image)

        _, _, text_width, text_height = draw.textbbox(xy=(0, 0), text=text, font=font)

        if bordered:
            draw.rounded_rectangle([(0,0),(SCREEN_WIDTH -1,text_height+2)],radius=8,fill="white",outline='black', width=1)

        offset_x = int((SCREEN_WIDTH-text_width)/2 if centered else 0)
        draw.text((offset_x, 0), text=text, font=font, fill=0)

        buffer_copy.paste(image, box=(0, int(row * ROW_HEIGHT)))
        
        self._buffer = buffer_copy.copy()

    def draw_rectangle(self, x1, y1, x2, y2, fill=None, outline=None, width=1):

        draw = ImageDraw.Draw(self._buffer)
        draw.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline, width=width)

    def clear_area(self, x1 = 0, y1 = 0, x2 = SCREEN_WIDTH, y2 = SCREEN_HEIGHT):

        self.draw_rectangle(x1,y1,x2,y2,255,255)

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

    def draw_promotion_window(self):

        #TODO Promotion screen to be reviewed

        try:
            row = 5
            image = Image.new('1', (SCREEN_WIDTH, ROW_HEIGHT), 255)

            draw = ImageDraw.Draw(image)
            draw.text((0, 0), "    Q    R    N   B", font=MAIN_FONT, fill=0)
            draw.polygon([(2, 18), (18, 18), (10, 3)], fill=0)
            draw.polygon([(35, 3), (51, 3), (43, 18)], fill=0)
            o = 66
            draw.line((0+o,16,16+o,16), fill=0, width=5)
            draw.line((14+o,16,14+o,5), fill=0, width=5)
            draw.line((16+o,6,4+o,6), fill=0, width=5)
            draw.polygon([(8+o, 2), (8+o, 10), (0+o, 6)], fill=0)
            o = 97
            draw.line((6+o,16,16+o,4), fill=0, width=5)
            draw.line((2+o,10, 8+o,16), fill=0, width=5)

            self._buffer.paste(image, (0, (row * ROW_HEIGHT)))

            self.write_text(2,"Choose")
            self.write_text(3,"your")
            self.write_text(4,"promotion!")

        except Exception as e:
            Log.exception(CentaurScreen.draw_promotion_window, e)

    def draw_board(self, pieces, startrow=2):

        try:
            for square in range(0,64):
                
                index = (square - 63) * -1

                row = int(((startrow * ROW_HEIGHT) + 8) + (16 * (index // 8)))
                col = int((square % 8) * 16)

                r = square // 8
                c = square % 8

                offset_y = 0

                if ((r // 2 == r / 2 and c // 2 == c / 2) or
                    (r // 2 != r / 2 and c // 2 != c / 2)):

                    offset_y = offset_y + 16

                offset_x = {" ":0,"P":16,"R":32,"N":48,"B":64,"Q":80,"K":96,"p":112,"r":128,"n":144,"b":160,"q":176,"k":192} [pieces[square]]
                
                piece_image = CHESS_SHEET_IMAGE.crop((offset_x, offset_y, offset_x+16, offset_y+16))

                self._buffer.paste(piece_image,(col,row))
                
        except Exception as e:
            Log.exception(CentaurScreen.draw_board, e)

    def draw_evaluation_bar(self, row=8.5, value=0, text=None, disabled=False, font=SMALL_FONT):

        if disabled:
            text = "evaluation disabled"

        if text:
            self.write_text(row, text, font=font, centered=True, bordered=True)
            return
        
        draw = ImageDraw.Draw(self._buffer)

        MAX_VALUE = 800
        HEIGHT = 14
        PADDING = 6
        BAR_WIDTH = SCREEN_WIDTH - (PADDING*2)

        value = MAX_VALUE if disabled or text != None else value

        value = +MAX_VALUE if value>+MAX_VALUE else value
        value = -MAX_VALUE if value<-MAX_VALUE else value

        offset = (-(value/MAX_VALUE) * BAR_WIDTH *.5) + (BAR_WIDTH *.5)

        y = row * ROW_HEIGHT

        draw.rounded_rectangle([(0,y),(127,y+HEIGHT)],radius=8, fill="white",outline='black', width=1)
        draw.rectangle([(PADDING,y+(PADDING *.5)),(127-PADDING,y+HEIGHT-(PADDING *.5))],fill="white",outline='black', width=1)
        draw.rectangle([(PADDING,y+(PADDING *.5)),(PADDING+offset,y+HEIGHT-(PADDING *.5))],fill="black",outline='black', width=1)


def get():
    return CentaurScreen().initialize()