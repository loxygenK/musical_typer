import pygame
from PIL import Image, ImageDraw
from math import tan, radians
from ColorTheme import *

import time


class KeyboardDrawer:
    # Drawing keyboard
    keyboard = ["1234567890-\\^", "qwertyuiop@[", "asdfghjkl;:]", "zxcvbnm,./\\"]
    highlight_text = "fj"

    def __init__(self):
        pass

    def draw(self, screen, start_y, font, key_size, key_margin, highlight = "", width = 1, background_color = None):
        w, h = pygame.display.get_surface().get_size()
        size = key_size + key_margin
        for i in range(4):
            key = self.keyboard[i]
            start = (w - size * len(key)) / 2
            for j in range(len(key)):
                is_highlight_needed = (highlight != "" and highlight.lower() == key[j].lower())
                if is_highlight_needed:
                    pygame.draw.rect(screen, GREEN_THICK_COLOR,
                                 (start + size * j, start_y + size * i, key_size, key_size), 0)
                elif background_color is not None:
                    pygame.draw.rect(screen, background_color,
                                 (start + size * j, start_y + size * i, key_size, key_size), 0)

                pygame.draw.rect(screen, TEXT_COLOR,
                                 (start + size * j, start_y + size * i, key_size, key_size), width)

                color = TEXT_COLOR
                if is_highlight_needed:
                    color = invert_color(TEXT_COLOR)
                elif key[j] in self.highlight_text:
                    color = BLUE_THICK_COLOR

                chr = font.render(key[j].upper(), True, color)
                screen.blit(chr, (start + size * j + key_size // 2 - chr.get_width() // 2, start_y + size * i + key_size // 2 - chr.get_height() // 2))

@DeprecationWarning
def arc(surface, color, pos, radius, start_angle, stop_angle, width = 1):

    lu = (pos[0] - radius, int(pos[1] + tan(radians(135)) * radius))
    rd = (pos[0] + radius, int(pos[1] - tan(radians(-45)) * radius))

    rect = (*lu, *rd)



    # 0.9ms
    im = Image.new("RGBA", (rd[0] - lu[0] + 1, rd[1] - lu[1]))
    draw = ImageDraw.Draw(im, "RGBA")

    draw.arc((0, 0, rd[0] - lu[0], rd[1] - lu[1]), start_angle, stop_angle, fill=color, width=5)
    byte = im.tobytes("raw")
    start = time.time()
    pyg_im = pygame.image.fromstring(byte, im.size, "RGBA")
    print(time.time() - start)


    surface.blit(pyg_im, lu)


def write_limit(screen, pos, left_limit, font, str, color=TEXT_COLOR):
    """
    左方向に描画制限を設けて、右揃えで文字列を描画する。

    :param screen: 描画対象スクリーン
    :param font: フォント
    :param str: 描画する文字
    :param left_limit: 左方向の制限X
    :param right: 描画基準X
    :param y: 描画基準Y
    :return: なし
    """
    rect_typed = font.render(str, True, color)

    if rect_typed.get_width() > (pos[0] - left_limit):
        screen.blit(rect_typed, (left_limit, pos[1]),
                       (rect_typed.get_width() - (pos[0] - left_limit), 0, rect_typed.get_width(), rect_typed.get_height()))
    else:
        screen.blit(rect_typed, (pos[0] - rect_typed.get_width(), pos[1]))

def print_progress(screen, pos, left_limit, font, typed, remain, past_color=None, remain_color=None):
    """
    タイピングの途中経過を描画する。

    :param screen: 描画対象スクリーン
    :param font: フォント
    :param typed: タイプした文字
    :param remain: 残っている文字
    :param left_limit: 左方向の制限X
    :param right: 描画基準X
    :param y: 描画基準Y
    :return:
    """

    if past_color is None:
        past_color = more_whiteish(TEXT_COLOR, 100)
    if remain_color is None:
        remain_color = TEXT_COLOR

    write_limit(screen, pos, left_limit, font, typed, past_color)
    rect_nottyped = font.render(remain, True, remain_color)
    screen.blit(rect_nottyped, pos, (0, 0, (pos[0] - left_limit), rect_nottyped.get_height()))


def write_center_x(window, x, y, font, text, color=(255, 255, 255)):

    rect = font.render(text, True, color)
    window.blit(rect, (x - rect.get_width() / 2, y))
