import pygame

def print_str(window, x, y, font, text, color=(255, 255, 255)):
    """
    Print string to screen

    :param window: screen to print string
    :param x: location x
    :param y: locagion y
    :param font: font
    :param text: text to print
    :param color: text color, default is white
    :return:
    """
    rect = font.render(text, True, color)
    if len(color) == 4:
        alpha_info = pygame.Surface(rect.get_size(), pygame.SRCALPHA)
        alpha_info.fill((255, 255, 255, 255 - color[3]))
        surf = rect.copy()
        surf.blit(alpha_info, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        window.blit(surf, (x, y))
    else:
        window.blit(rect, (x, y))
