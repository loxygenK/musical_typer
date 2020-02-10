import math

import pygame
import sys
from pygame.locals import *

import Romautil
import pygame_misc

import re

ONE_CHAR_POINT = 10
PERFECT_POINT = 100
CLEAR_POINT = 50
MISS_POINT = -30
COULDNT_TYPE_POINT = -2

pygame.mixer.pre_init(44100, 16, 2, 1024)
pygame.init()
pygame.mixer.init()

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
    next_current_minute = 0
    current_minute = 0
    current_seconds = 0.0

    song = ""
    phon = ""

    point = 0

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
                continue
            elif command == "end":
                is_in_song = False
                continue

        if not is_in_song:
            score.log_error(line, "Unknown text outside song section!")
            score.re_initialize_except_log()
            break

        if rect_blk_match is not None:
            command = rect_blk_match[1]
            if command == "break":
                score.score.append([60 * current_minute + current_seconds, "", ""])
                continue

        if line.startswith(">>"):
            score.score.append([60 * current_minute + current_seconds, line[2:], ""])
            continue

        # Minute
        if line.startswith("|"):
            line = line[1:]
            next_current_minute = int(line)
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
            current_minute = next_current_minute
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
                score.zone.append([60 * current_minute + current_seconds, zone_name, "start"])
                continue
            elif flag == "end":
                score.zone.append([60 * current_minute + current_seconds, zone_name, "end"])
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

    if "song_data" not in score.properties.keys():
        score.log_error("[Loading song failed]", "No song specified!")
    else:
        pygame.mixer.music.load(score.properties["song_data"])

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
    pygame.mixer.music.play(1)
    pygame.mixer.music.get_pos()

    lyrincs_index = -1
    zone_index = -1
    lyrincs_index = -1
    target_kana = ""
    target_roma = ""
    full = ""

    point = 0
    sent_miss = 0
    sent_count = 0
    completed = False

    latest_missrate = 0
    latest_missrate_col = (0, 0, 0)
    missrate_col = (255, 0, 0)

    next_income = score_data.score[0][0]

    current_zone = ""
    while mainloop_continues:

        pos = pygame.mixer.music.get_pos() / 1000

        # If new lyncs coming
        if score_data.score[lyrincs_index + 1][0] <= pos:

            point += COULDNT_TYPE_POINT * len(target_roma)

            lyrincs_index += 1
            print(str(lyrincs_index) + " (" + str(score_data.score[lyrincs_index]) + ")")

            next_income = score_data.score[lyrincs_index + 1][0]
            full = score_data.score[lyrincs_index][1]
            target_kana = score_data.score[lyrincs_index][2]
            target_roma = Romautil.hira2roma(target_kana)
            sent_count= 0
            sent_miss = 0
            completed = False
            latest_missrate = missrate
            latest_missrate_col = missrate_col
            missrate = 0
            missrate_col = (255, 0, 0)

        if score_data.zone[zone_index + 1][0] <= pos:
            zone_index += 1

            if score_data.zone[zone_index][2] == "start":
                current_zone = score_data.zone[zone_index][1]
            else:
                current_zone = ""

        sentence_continues = True

        screen.fill((0, 0, 0))


        w, h = pygame.display.get_surface().get_size()
        ratio = (next_income - pos) / (next_income - score_data.score[lyrincs_index][0])
        missrate = sent_count / ((sent_miss + sent_count) if sent_miss + sent_count > 0 else 1)

        pygame.draw.rect(screen, (128, 0, 0), (0, 0, math.floor(ratio * w), 120))

        pygame_misc.print_str(screen, 5, 0, nihongo_font, target_kana)
        pygame_misc.print_str(screen, 5, 55, full_font, full, (192, 192, 192))
        pygame_misc.print_str(screen, 5, 80, alphabet_font, target_roma)
        pygame_misc.print_str(screen, 5, 130, system_font, "Typed: {}".format(count))
        pygame_misc.print_str(screen, 5, 150, system_font, "Miss: {}".format(missed))
        pygame_misc.print_str(screen, 5, 170, system_font, "Sent: {}".format(sent_miss))
        pygame_misc.print_str(screen, 5, 190, full_font, "Score: {}".format(point))
        pygame_misc.print_str(screen, 5, 220, system_font, "Zone: {}".format(current_zone))
        pygame_misc.print_str(screen, 5, 350, system_font, str(pos))

        pygame.draw.rect(screen, missrate_col, (0, 85, math.floor(missrate * w), 2))
        pygame.draw.rect(screen, latest_missrate_col, (0, 12, math.floor(latest_missrate * w), 2))
        if completed:
            pygame_misc.print_str(screen, 5, 280, full_font, "WA" if sent_miss != 0 else "AC", (255, 255, 120))

        for event in pygame.event.get():
            if event.type == QUIT:
                mainloop_continues = False
                break
            if event.type == KEYDOWN:

                # Completed already, or no phonuciation provided
                if len(target_roma) == 0:
                    continue

                # filter event -- if alphabet, number, or "-" key pressed
                if Romautil.is_readable_key_pressed(event.key):
                    # if correct key was pushed
                    if target_roma[0] == chr(event.key):
                        target_roma = target_roma[1:]
                        target_kana = Romautil.get_not_halfway_hr(target_kana, target_roma)
                        count += 1
                        point += ONE_CHAR_POINT
                        sent_count += 1

                    else:
                        missed += 1
                        sent_miss += 1
                        point += MISS_POINT
                        missrate = sent_miss / ((sent_miss + sent_count) if sent_miss + sent_count > 0 else 1)
                        print(missrate)


                    # Completed!
                    if len(target_roma) == 0:
                        point += CLEAR_POINT
                        if sent_miss == 0:
                            point += PERFECT_POINT
                            missrate_col = (255, 255, 0)
                        else:
                            missrate_col = (0, 255, 0)
                        completed = True


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