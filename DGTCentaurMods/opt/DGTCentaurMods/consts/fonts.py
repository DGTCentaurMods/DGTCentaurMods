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

from PIL import ImageFont
from DGTCentaurMods.consts import consts

MAIN_FONT = ImageFont.truetype(consts.FONT_FILE, 16)
SMALL_FONT = ImageFont.truetype(consts.FONT_FILE, 11)
MEDIUM_FONT = ImageFont.truetype(consts.FONT_FILE, 13)
DIGITAL_FONT = ImageFont.truetype(consts.DIGITAL_FONT_FILE, 30)
SMALL_DIGITAL_FONT = ImageFont.truetype(consts.DIGITAL_FONT_FILE, 20)
