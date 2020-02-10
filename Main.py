import pygame
import sys
from pygame.locals import *

import Romautil
import pygame_misc

import re

pygame.init()

class Score:
    LOG_ERROR = 1
    LOG_WARN = 2

    def __init__(self):
        self.properties = {}
        self.log = []
        self.score = []
        self.zone = []
        self.section = {}

    def log_error(self, line, text, init=True):
        self.log.append([Score.LOG_ERROR, [line, text]])
        if init: self.re_initialize_except_log()

    def log_warn(self, line, text):
        self.log.append([Score.LOG_WARN, [line, text]])

    def re_initialize_except_log(self):
        self.properties = {}
        self.score = []
        self.zone = []
        self.section = {}



def set_val_to_dictionary(dict, key, value):
    if key in dict.keys():
        dict[key] = value
    else:
        dict.setdefault(key, value)


def read_score(file_name):

    lines = []
    with open(file_name, mode="r") as f:
        lines = f.readlines()

    score = Score()

    re_rect_blacket = re.compile(r"\[(.*)\]")

    score_data = []
    zone_data = {}
    current_minute = 0
    current_seconds = 0.0

    song = ""
    phon = ""

    is_in_song = False
    for line in lines:
        line = line.strip()

        # Comment
        if line.startswith("#"): continue

        # Blank line
        if len(line) == 0: continue

        # Song property
        if line.startswith(":") and not is_in_song:
            line = line[1:]
            key, value = line.split()
            set_val_to_dictionary(score.properties, key, value)
            continue

        rect_blk_match = re_rect_blacket.match(line)

        if rect_blk_match is not None:
            command = rect_blk_match[1]
            if command == "start":
                is_in_song = True
            elif command == "end":
                is_in_song = False
            continue

        if not is_in_song:
            score.log_error(line, "Unknown text outside song section!")
            score.re_initialize_except_log()
            break

        # Minute
        if line.startswith("|"):
            line = line[1:]
            current_minute = int(line)
            continue

        # Seconds
        # At seconds setting line, song and phon data will be saved instantly
        if line.startswith("*"):
            line = line[1:]

            if len(song) != 0:
                if len(phon) == 0:
                    score.log_error(line, "No pronunciation data!")
                    break
                score.score.append([60 * current_minute + current_seconds, song, phon])
                song = ""
                phon = ""
            current_seconds = float(line)
            continue

        if line.startswith("@"):
            line = line[1:]
            if line in score.section:
                score.log_error(line, "Duplicated Section Name!")
                break
            else:
                set_val_to_dictionary(score.section, line, 60 * current_minute + current_seconds)

            continue


        if line.startswith("!"):
            line = line[1:]
            flag, zone_name = line.split()

            if flag == "start":
                if zone_name in zone_data.keys():
                    score.log_error(line, "Nest of the same name zone!")
                    break
                else:
                    set_val_to_dictionary(zone_data, zone_name, 60 * current_minute + current_seconds)
                    continue
            elif flag == "end":
                if zone_name not in zone_data.keys():
                    score.log_error(line, "Suddenly unknown zone appeared!")
                    break
                else:
                    score.zone.append([zone_data[zone_name], 60 * current_minute + current_seconds, zone_name])
                    del zone_data[zone_name]
                    continue


        # Phonenics
        if line.startswith(":"):
            line = line[1:]
            if len(phon) != 0:
                score.log_warn(line, "Pronunciation string overwrited: {} into {}.".format(song, line))
            phon = line
            continue

        if len(song) != 0:
            score.log_warn(line, "Song string overwrited: {} into {}.".format(song, line))
        song = line

    return score





def main():

    screen = pygame.display.set_mode((600, 480))
    pygame.display.set_caption("Musical Typer")

    nihongo_font = pygame.font.Font("mplus-1m-medium.ttf", 48)
    alphabet_font = pygame.font.Font("mplus-1m-medium.ttf", 32)
    full_font = pygame.font.Font("mplus-1m-medium.ttf", 24)
    system_font = pygame.font.Font("mplus-1m-medium.ttf", 16)

    score_data = read_score("test_music_text.tsc")

    count = 0
    missed = 0

    mainloop_continues = True
    for score in score_data.score:

        full = score[1]
        target_kana = score[2]
        target_roma = Romautil.hira2roma(target_kana)

        sentence_continues = True

        while mainloop_continues and sentence_continues:

            screen.fill((0, 0, 0))

            pygame_misc.print_str(screen, 5, 0, nihongo_font, target_kana)
            pygame_misc.print_str(screen, 5, 55, full_font, full, (192, 192, 192))
            pygame_misc.print_str(screen, 5, 80, alphabet_font, target_roma)
            pygame_misc.print_str(screen, 5, 130, system_font, "Typed: {}".format(count))
            pygame_misc.print_str(screen, 5, 150, system_font, "Miss: {}".format(missed))

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

                        # Completed!
                        if len(target_roma) == 0:
                            sentence_continues = False
                            break

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