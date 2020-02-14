import pygame
from GameSystem import Screen

from ColorTheme import *

def slide_fadeout_text(current_frame, total_frame, ui: Screen, args):
    w, h = ui.screen_size

    color = args[1] + (255 * (current_frame / total_frame),)

    # I don't use ui.print_str, because I wanna know the size of font surface size.

    text = args[2].render(args[0], True, color)
    text_w, text_h = text.get_size()

    ui.print_str((w - text_w) / 2 + args[4], (h - text_h) / 2 + args[5] - args[3] * (current_frame / total_frame), args[2], args[0], color)

def blink_screen(current_frame, total_frame, ui: Screen, args):
    w, h = ui.screen_size

    color = args[0] + (255 - 255 * (current_frame / total_frame),)

    alpha_info = pygame.Surface(ui.screen_size, pygame.SRCALPHA)
    alpha_info.fill((255, 255, 255, 255 - 255 * (current_frame / total_frame)), special_flags=pygame.BLEND_RGBA_MULT)
    filler = pygame.Surface(ui.screen_size)
    filler.fill(color)
    filler.set_alpha(255 - 255 * (current_frame / total_frame))
    filler.blit(alpha_info, (0, 0))
    ui.screen.blit(filler, (0, 0))


def blink_rect(current_frame, total_frame, ui: Screen, args):
    w, h = ui.screen_size

    color = args[0] + (255 - 255 * (current_frame / total_frame),)

    size = (args[1][2], args[1][3])

    alpha_info = pygame.Surface(size, pygame.SRCALPHA)
    alpha_info.fill((255, 255, 255, 255 - 255 * (current_frame / total_frame)), special_flags=pygame.BLEND_RGBA_MULT)
    filler = pygame.Surface(size)
    filler.fill(color)
    filler.set_alpha(255 - 255 * (current_frame / total_frame))
    filler.blit(alpha_info, (0, 0))
    ui.screen.blit(filler, (args[1][0], args[1][1]))

def print_text(current_frame, total_frame, ui: Screen, args):
    ui.print_str(args[0], args[1], args[2], args[3], args[4])


def faded_text(current_frame, total_frame, ui: Screen, args):
    ui.print_str(args[0], args[1], args[2], args[3], (*args[4], 255 * (current_frame / total_frame)))
