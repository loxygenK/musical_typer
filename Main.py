import time

import math
import pygame

import DrawingUtil

pygame.mixer.pre_init(44100, 16, 2, 1024)
pygame.mixer.init()
pygame.init()

import sys
from pygame.locals import *

import DrawMethodTemplates
import re
from GameSystem import *

from ColorTheme import *

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
    key_speeder = KeySpeedCalculator()
    keyboard_drawer = DrawingUtil.KeyboardDrawer()
    ui = Screen()

    fps_clock = pygame.time.Clock()

    game_finished_reason = ""

    ui.add_background_draw_method(60, DrawMethodTemplates.slide_fadeout_text, ["Song start!", (255, 127, 0), ui.system_font, 25, 0, 0])
    mainloop_continues = True
    song_finished = False

    pygame.mixer.music.set_volume(0.5)

    frame_count = 0
    while mainloop_continues and pygame.mixer.music.get_pos() > 0:

        # -----------------------
        #     Pre-Calculation
        # -----------------------

        frame_count = (frame_count + 1) % 60

        # get some values
        pos = pygame.mixer.music.get_pos() / 1000

        current_lyrincs, lyx_idx = progress.get_current_lyrincs(pos)
        current_zone,    zne_idx = progress.get_current_zone(pos)
        current_section, sct_idx = progress.get_current_section(pos)

        w, h = ui.screen_size

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
                        key_speeder.ticked(pos)
                        judge_info.count_success()
                        # Add some special score
                        ui.add_foreground_draw_method(30, DrawMethodTemplates.slide_fadeout_text,
                                                      ["Pass", more_blackish(GREEN_THIN_COLOR, 50), ui.alphabet_font, 10, -150, -383])
                        if current_zone == "tech-zone":
                            judge_info.point += judge_info.SPECIAL_POINT
                            SEControl.special_success.play()
                        else:
                            SEControl.success.play()

                        # Did player finished the sentence by this type?
                        if judge_info.completed and judge_info.sent_typed > 0:
                            if judge_info.sent_miss == 0:
                                ui.add_foreground_draw_method(120, DrawMethodTemplates.slide_fadeout_text,
                                                              ["AC", GREEN_THICK_COLOR, ui.alphabet_font, 20, -170, -383])
                                ui.add_background_draw_method(15, DrawMethodTemplates.blink_rect,
                                                              [more_whiteish(GREEN_THIN_COLOR, 50), (0, 60, w, 130)])
                            else:
                                ui.add_foreground_draw_method(120, DrawMethodTemplates.slide_fadeout_text,
                                                              ["WA", more_whiteish(BLUE_THICK_COLOR, 100), ui.alphabet_font, 20, -170, -383])
                                ui.add_background_draw_method(15, DrawMethodTemplates.blink_rect,
                                                              [more_whiteish(BLUE_THICK_COLOR, 100), (0, 60, w, 130)])
                    else:
                        SEControl.failed.play()
                        judge_info.count_failure()
                        # blink screen
                        ui.add_background_draw_method(15, DrawMethodTemplates.blink_screen, [(255, 200, 200)])
                        ui.add_foreground_draw_method(30, DrawMethodTemplates.slide_fadeout_text,
                                                      ["WA", more_whiteish(RED_COLOR, 50), ui.alphabet_font,
                                                       10, -150, -383])

                if event.key == K_ESCAPE:
                    mainloop_continues = False
                    break

        # --------------------
        #     Calculation
        # --------------------

        # ===== Segment Change =====

        # If lyrics changed, re-initialize some things, such as judge_info
        if lyx_idx or (current_lyrincs is None and not song_finished):

            # Before it let's add score
            judge_info.point += GameJudgementInfo.COULDNT_TYPE_POINT * len(judge_info.target_roma)

            # Then record
            judge_info.record_sentence_score()

            # Did player TLE?
            if len(judge_info.target_roma) > 0:
                ui.add_foreground_draw_method(30, DrawMethodTemplates.slide_fadeout_text,
                                              ["TLE", more_blackish(RED_COLOR, 50), ui.alphabet_font, -10,
                                               -150, -383])
                ui.add_background_draw_method(15, DrawMethodTemplates.blink_rect,
                                              [more_whiteish(RED_COLOR, 50), (0, 60, w, 130)])

            # And erase something
            judge_info.reset_sentence_score()
            judge_info.set_current_lyrinc(score_data.score[progress.lyrincs_index][1], score_data.score[progress.lyrincs_index][2])

            # Reset the time standard
            key_speeder.set_prev_pos(pos)

            # did song finish?
            if current_lyrincs is None and not song_finished:
                judge_info.set_current_lyrinc("", "")
                song_finished = True
                ui.add_background_draw_method(60, DrawMethodTemplates.slide_fadeout_text, ["Song Finished!", (255, 127, 0), ui.system_font, 25, 0, 0])


        # If section changed, there's some special calculation...
        if sct_idx:

            # If player completed this section, let's cerebrate it and add score
            if judge_info.section_miss == 0 and judge_info.section_count != 0:
                ui.add_background_draw_method(60, DrawMethodTemplates.slide_fadeout_text, ["Section AC!", (255, 127, 0), ui.system_font, 25, 0, 0])
                judge_info.point += judge_info.SECTION_PERFECT_POINT

            # Then record
            judge_info.record_section_score()

            # And erase section result data
            judge_info.reset_section_score()

        if zne_idx:
            ui.add_background_draw_method(15, DrawMethodTemplates.blink_screen, [(64, 64, 0)])

        if judge_info.point < -300:
            game_finished_reason = "gameover"
            break

        is_ac = judge_info.completed and judge_info.sent_count > 0 and judge_info.sent_miss == 0

        # ----------------
        #     Drawing
        # ----------------

        # [ Background ]

        # reset screen
        ui.screen.fill(BACKGROUND_COLOR)

        # update drawing method

        # Song information
        DrawingUtil.write_limit(ui.screen, (w - 2, 0), w / 2, ui.alphabet_font, score_data.properties["title"])
        DrawingUtil.write_limit(ui.screen, (w - 5, 33), w / 2, ui.system_font,
                                score_data.properties["song_author"] + "／" + score_data.properties["singer"],
                                more_whiteish(TEXT_COLOR, 100))

        # Time remaining gauge background
        pygame.draw.rect(ui.screen, more_blackish(BACKGROUND_COLOR, 25), (0, 60, w, 130))
        pygame.draw.rect(ui.screen, more_blackish(BACKGROUND_COLOR, 50), (0, 60, math.floor(progress.get_time_remain_ratio(pos) * w), 130))

        ui.update_background_draw_method()

        # [ Foreground ]

        # Lyrics
        DrawingUtil.print_progress(ui.screen, (w / 2, 80), MARGIN + 5, ui.get_font_by_size(50),
                                   judge_info.typed_kana, judge_info.target_kana)
        DrawingUtil.print_progress(ui.screen, (w / 2, 130), MARGIN + 5, ui.full_font,
                                   judge_info.typed_roma, judge_info.target_roma)

        # mistake rate gauge
        pygame.draw.rect(ui.screen, GREEN_THICK_COLOR if not is_ac else RED_COLOR, (0, 60, w * judge_info.get_sentence_missrate(), 3))
        pygame.draw.rect(ui.screen, GREEN_THICK_COLOR, (0, 187, w * judge_info.get_full_missrate(), 3))

        # keyboard
        keyboard_drawer.draw(ui.screen, 193, ui.full_font, 40, 5, judge_info.target_roma[:1], 2,
                             background_color=(192, 192, 192) if judge_info.completed else None)

        # Score
        if judge_info.point < 0:
            if frame_count % 20 < 10:
                ui.print_str(5, 20, ui.alphabet_font, "{:08d}".format(judge_info.point), RED_COLOR)
            else:
                ui.print_str(5, 20, ui.alphabet_font, "{:08d}".format(judge_info.point), BLUE_THICK_COLOR)
        else:
            ui.print_str(5, 20, ui.alphabet_font, "{:08d}".format(judge_info.point), BLUE_THICK_COLOR)

        ui.update_foreground_draw_method()

        ui.print_str(3, -3, ui.system_font, "{:5.2f} fps".format(fps_clock.get_fps()), TEXT_COLOR)

        fps_clock.tick(60)
        pygame.display.update()

    if game_finished_reason == "gameover":
        ui.add_background_draw_method(300, DrawMethodTemplates.blink_screen, [(192, 0, 0)])
        ui.add_background_draw_method(300, DrawMethodTemplates.slide_fadeout_text, ["Too many mistake!", (255, 127, 0), ui.nihongo_font, -25, 0, 0])
        SEControl.gameover.play()
        for _ in range(300):
            pygame.mixer.music.fadeout(1000)
            ui.update_background_draw_method()
            pygame.time.wait(1000 // 60)
            pygame.display.update()



    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()