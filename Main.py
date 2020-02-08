import pygame
import sys
from pygame.locals import *

import Romautil
import pygame_misc

pygame.init()


def main():

    screen = pygame.display.set_mode((600, 480))
    pygame.display.set_caption("Musical Typer")

    nihongo_font = pygame.font.Font("mplus-1m-medium.ttf", 64)
    alphabet_font = pygame.font.Font("mplus-1m-medium.ttf", 32)
    system_font = pygame.font.Font("mplus-1m-medium.ttf", 16)

    # TODO: Read from file
    target_kana = u"たいへんつかれた"
    target_roma = Romautil.hira2roma(target_kana)

    count = 0
    missed = 0

    mainloop_continues = True
    while mainloop_continues:

        screen.fill((0, 0, 0))

        pygame_misc.print_str(screen, 5, 0, nihongo_font, target_kana)
        pygame_misc.print_str(screen, 5, 65, alphabet_font, target_roma)
        pygame_misc.print_str(screen, 5, 100, system_font, "Typed: {}".format(count))
        pygame_misc.print_str(screen, 5, 120, system_font, "Miss: {}".format(missed))

        for event in pygame.event.get():
            if event.type == QUIT:
                mainloop_continues = False
                break
            if event.type == KEYDOWN:

                # filter event -- if alphabet, number, or "-" key pressed
                if Romautil.is_readable_key_pressed(event.key):

                    # if correct key was pushed
                    if target_roma[0] == chr(event.key):
                        target_roma = target_roma[1:]
                        target_kana = Romautil.get_not_halfway_hr(target_kana, target_roma)
                        count += 1
                    else:
                        missed += 1

                if event.key == K_ESCAPE:
                    mainloop_continues = False
                    break

        # 60fps
        pygame.time.wait(1000 // 60)
        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()