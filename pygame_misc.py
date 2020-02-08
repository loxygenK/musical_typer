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
    window.blit(rect, (x, y))