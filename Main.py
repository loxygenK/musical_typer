import math
import pygame
pygame.mixer.pre_init(44100, 16, 2, 1024)
pygame.mixer.init()
pygame.init()

import sys
from pygame.locals import *

import DrawMethodTemplates
import Romautil
import pygame_misc

import re



from GameSystem import *


class Score:
    LOG_ERROR = 1
    LOG_WARN = 2

    def __init__(self):
        self.properties = {}
        self.log = []
        self.score = []
        self.zone = []
        self.section = []

    def log_error(self, line, text, init=True):
        self.log.append([Score.LOG_ERROR, [line, text]])
        if init: self.re_initialize_except_log()

    def log_warn(self, line, text):
        self.log.append([Score.LOG_WARN, [line, text]])

    def re_initialize_except_log(self):
        self.properties = {}
        self.score = []
        self.zone = []
        self.section = []



def set_val_to_dictionary(dict, key, value):
    if key in dict.keys():
        dict[key] = value
    else:
        dict.setdefault(key, value)


def read_score(file_name):

    re_rect_blacket = re.compile(r"\[(.*)\]")

    # ファイルを読み込む
    lines = []
    with open(file_name, mode="r") as f:
        lines = f.readlines()

    # 読み込み用変数準備
    score = Score()

    current_minute = 0
    current_time = 0

    song = ""
    phon = ""

    is_in_song = False

    for line in lines:

        line = line.strip()

        # ----- 処理対象行かの確認

        # コメント
        if line.startswith("#"): continue

        # 空行
        if len(line) == 0: continue

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
                score.score.append([current_time, "end", ""])
                is_in_song = False
                continue

        if not is_in_song:
            score.log_error(line, "Unknown text outside song section!")
            score.re_initialize_except_log()
            break

        if rect_blk_match is not None:
            command = rect_blk_match[1]
            if command == "break":
                score.score.append([current_time, "", ""])
                continue

        if line.startswith(">>"):
            score.score.append([current_time, "", ""])
            continue

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
                score.score.append([current_time, song, phon])
                song = ""
                phon = ""

            current_time = 60 * current_minute + float(line)

            continue

        if line.startswith("@"):
            line = line[1:]
            score.section.append([current_time, line])

            continue


        if line.startswith("!"):
            line = line[1:]
            flag, zone_name = line.split()

            if flag == "start":
                score.zone.append([current_time, zone_name, "start"])
                continue
            elif flag == "end":
                score.zone.append([current_time, zone_name, "end"])
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

    score_data = read_score("test_music_text.tsc")

    pygame.mixer.music.play(1)

    next_income = score_data.score[0][0]

    progress = GameProgressInfo(score_data)
    judge_info = GameJudgementInfo()
    ui = Screen()

    game_finished_reason = ""

    ui.add_draw_method(60, DrawMethodTemplates.slide_fadeout_text, ["Song start!", (255, 127, 0), ui.system_font, 25])
    mainloop_continues = True
    while mainloop_continues:

        # -----------------------
        #     Pre-Calculation
        # -----------------------

        # get some values
        pos = pygame.mixer.music.get_pos() / 1000

        current_lyrincs, lyx_idx = progress.get_current_lyrincs(pos)
        current_zone,    zne_idx = progress.get_current_zone(pos)
        current_section, sct_idx = progress.get_current_section(pos)

        # ------------------------
        #     Events / Judging
        # ------------------------

        for event in pygame.event.get():
            if event.type == QUIT:
                mainloop_continues = False
                break
            if event.type == KEYDOWN:

                # Completed already, or no phonuciation provided
                if judge_info.completed:
                    SEControl.unneccesary.play()
                    continue

                # filter event -- if alphabet, number, or "-" key pressed
                if Romautil.is_readable_key_pressed(event.key):
                    # if correct key was pushed
                    if judge_info.is_expected_key(chr(event.key)):
                        judge_info.count_success()
                        # Add some special score
                        if current_zone == "tech-zone":
                            judge_info.point += judge_info.SPECIAL_POINT
                            SEControl.special_success.play()
                        else:
                            SEControl.success.play()
                    else:
                        SEControl.failed.play()
                        judge_info.count_failure()
                        # blink screen
                        ui.add_draw_method(15, DrawMethodTemplates.blink_screen, [(127, 0, 0)])


                if event.key == K_ESCAPE:
                    mainloop_continues = False
                    break

        # --------------------
        #     Calculation
        # --------------------

        # If lyrics changed, re-initialize some things, such as judge_info
        if lyx_idx:

            # Before it let's add score
            judge_info.point += GameJudgementInfo.COULDNT_TYPE_POINT * len(judge_info.target_roma)

            # And erase something
            judge_info.reset_sentence_score()
            judge_info.set_current_lyrinc(score_data.score[progress.lyrincs_index][1], score_data.score[progress.lyrincs_index][2])

        # If section changed, there's some special calculation...
        if sct_idx:

            # If player completed this section, let's cerebrate it and add score
            if judge_info.section_miss == 0 and judge_info.section_count != 0:
                ui.add_draw_method(60, DrawMethodTemplates.slide_fadeout_text, ["Section AC!a", (255, 127, 0), ui.system_font, 25])
                judge_info.point += judge_info.SECTION_PERFECT_POINT

            # And erase section result data
            judge_info.reset_section_score()

            # cool blink
            ui.add_draw_method(15, DrawMethodTemplates.blink_screen, [(0, 0, 64)])

        if zne_idx:
            ui.add_draw_method(15, DrawMethodTemplates.blink_screen, [(64, 64, 0)])

        if judge_info.point < -300:
            game_finished_reason = "gameover"
            break


        # ----------------
        #     Drawing
        # ----------------

        # reset screen
        ui.screen.fill((0, 0, 0))
        w, h = ui.screen_size

        # update drawing method
        ui.update_draw_method()

        # Sentence remain time guage
        pygame.draw.rect(ui.screen, (128, 0, 0), (0, 0, math.floor(progress.get_time_remain_ratio(pos) * w), 120))

        # Debug output
        ui.print_str(5, 0,   ui.nihongo_font,   judge_info.target_kana)
        ui.print_str(5, 55,  ui.full_font,      judge_info.full, (192, 192, 192))
        ui.print_str(5, 80,  ui.alphabet_font,  judge_info.target_roma)
        ui.print_str(5, 130, ui.system_font,    "Full:     {} / {} ({})".format(judge_info.count, judge_info.missed, judge_info.typed))
        ui.print_str(5, 150, ui.system_font,    "Sentence: {} / {} ({})".format(judge_info.sent_count, judge_info.sent_miss, judge_info.sent_typed))
        ui.print_str(5, 170, ui.system_font,    "Section : {} / {} ({})".format(judge_info.section_count, judge_info.section_miss, judge_info.section_typed))
        ui.print_str(5, 190, ui.full_font,      "Score: {}".format(judge_info.point))
        ui.print_str(5, 240, ui.system_font,    "Zone: {}".format(current_zone))
        ui.print_str(5, 260, ui.system_font,    "Section: {}".format(current_section))

        ui.print_str(5, 350, ui.system_font,    str(pos))

        # Missrate Info
        pygame.draw.rect(ui.screen, (255, 0, 0), (0, 85, math.floor(judge_info.get_sentence_missrate() * w), 2))

        # Does player completed?
        if judge_info.completed and judge_info.sent_count > 0:
            # Give information
            ui.print_str(5, 280, ui.full_font, "WA" if judge_info.sent_miss != 0 else "AC", (255, 255, 120))

        # 60fps
        pygame.time.wait(1000 // 60)
        pygame.display.update()

    if game_finished_reason == "gameover":
        ui.add_draw_method(300, DrawMethodTemplates.blink_screen, [(192, 0, 0)])
        ui.add_draw_method(300, DrawMethodTemplates.slide_fadeout_text, ["Too many mistake!", (255, 127, 0), ui.nihongo_font, -25])
        SEControl.gameover.play()
        for _ in range(300):
            pygame.mixer.music.fadeout(1000)
            ui.update_draw_method()
            pygame.time.wait(1000 // 60)
            pygame.display.update()



    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()