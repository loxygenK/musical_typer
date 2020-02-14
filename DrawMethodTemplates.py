import pygame
from GameSystem import Screen

from ColorTheme import *

def slide_fadeout_text(current_frame, total_frame, ui: Screen, args):
    w, h = ui.screen_size

    color_r = args[1][0] + (BACKGROUND_COLOR[0] - args[1][0]) * (current_frame / total_frame)
    color_g = args[1][1] + (BACKGROUND_COLOR[1] - args[1][1]) * (current_frame / total_frame)
    color_b = args[1][2] + (BACKGROUND_COLOR[2] - args[1][2]) * (current_frame / total_frame)

    color_r = max(0, min(color_r, 255))
    color_g = max(0, min(color_g, 255))
    color_b = max(0, min(color_b, 255))

    color = (color_r, color_g, color_b)

    # I don't use ui.print_str, because I wanna know the size of font surface size.

    text = args[2].render(args[0], True, color)
    text_w, text_h = text.get_size()

    ui.print_str((w - text_w) / 2, (h - text_h) / 2 - args[3] * (current_frame / total_frame), args[2], args[0], color)

def blink_screen(current_frame, total_frame, ui: Screen, args):
    w, h = ui.screen_size

    color_r = args[0][0] + (BACKGROUND_COLOR[0] - args[0][0]) * (current_frame / total_frame)
    color_g = args[0][1] + (BACKGROUND_COLOR[1] - args[0][1]) * (current_frame / total_frame)
    color_b = args[0][2] + (BACKGROUND_COLOR[2] - args[0][2]) * (current_frame / total_frame)

    color_r = max(0, min(color_r, 255))
    color_g = max(0, min(color_g, 255))
    color_b = max(0, min(color_b, 255))

    color = (color_r, color_g, color_b)

    pygame.draw.rect(ui.screen, color, (0, 0, w, h))