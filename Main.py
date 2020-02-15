##############################
#                            #
#   loxygenK/musical_typer   #
#   メインプログラム         #
#   (c)2020 loxygenK         #
#      All right reversed.   #
#                            #
##############################

import sys

# Python管理ライブラリ
import math
import pygame
from pygame.locals import *

# Pygame初期化
pygame.mixer.pre_init(44100, 16, 2, 1024)
pygame.mixer.init()
pygame.init()

# 自作ライブラリ
import DrawMethodTemplates
from GameSystem import *
from ColorTheme import *

def main():

    # ----- [ ゲーム用の情報準備 ] -----

    # 譜面を読み込む
    score_data = Score()
    score_data.read_score("test_music_text.tsc")

    # ゲームに必要なインスタンスを生成
    game_info = GameInfo(score_data)
    keyboard_drawer = DrawingUtil.KeyboardDrawer()
    ui = Screen()

    # FPS管理用インスタンスを生成
    fps_clock = pygame.time.Clock()

    # ループ管理用変数
    game_finished_reason = ""
    mainloop_continues = True
    song_finished = False

    # フレームカウンター
    # 点滅処理などに使う
    frame_count = 0

    # スクリーンのサイズを取得
    w, h = ui.screen_size

    # ----- [ ゲーム準備 ] -----

    # 再生
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(1)

    game_info.pos = 0

    # メインループ
    # (何らかの理由で強制的にメインループを抜ける必要が出てきた or 曲が終わった)
    while mainloop_continues and pygame.mixer.music.get_pos() >= 0:

        # -----------------
        #    事前計算
        # -----------------


        # フレームカウンタを更新
        frame_count = (frame_count + 1) % 60
        # 曲上の現在位置を把握
        game_info.pos = pygame.mixer.music.get_pos() / 1000

        # 現在の歌詞・ゾーン・セクションを取得
        lyx_idx = game_info.update_current_lyrincs()
        zne_idx = game_info.update_current_zone()
        sct_idx = game_info.get_current_section()

        # ---------------------------
        #   イベント処理／ジャッジ
        # ---------------------------

        # イベント処理ループ
        for event in pygame.event.get():
            if event.type == QUIT:
                mainloop_continues = False
                break
            if event.type == KEYDOWN:

                # ESCキーの場合
                if event.key == K_ESCAPE:
                    mainloop_continues = False
                    break

                # 大前提として、無効なキーが押されていないか
                if Romautil.is_readable_key_pressed(event.key):

                    # これ以上打つキーがない(打ち終わったか、そもそも歌詞がない)
                    if game_info.completed:
                        SoundEffectConstants.unneccesary.play()
                        continue

                    # 正しいキーが押されたか
                    if game_info.is_expected_key(chr(event.key)):

                        # 成功処理をする
                        game_info.count_success()

                        # 成功エフェクト
                        ui.add_fg_effector(30, DrawMethodTemplates.slide_fadeout_text,
                                           ["Pass", more_blackish(GREEN_THIN_COLOR, 50), ui.alphabet_font, 10, -150, -383])

                        # AC／WAのエフェクト
                        if game_info.is_ac:
                            ui.add_fg_effector(120, DrawMethodTemplates.slide_fadeout_text,
                                               ["AC", GREEN_THICK_COLOR, ui.alphabet_font, 20, -170, -383])
                            ui.add_bg_effector(15, DrawMethodTemplates.blink_rect,
                                               [more_whiteish(GREEN_THIN_COLOR, 50), (0, 60, w, 130)])
                            SoundEffectConstants.ac.play()
                        elif game_info.is_wa:
                            ui.add_fg_effector(120, DrawMethodTemplates.slide_fadeout_text,
                                               ["WA", more_whiteish(BLUE_THICK_COLOR, 100), ui.alphabet_font, 20, -170, -383])
                            ui.add_bg_effector(15, DrawMethodTemplates.blink_rect,
                                               [more_whiteish(BLUE_THICK_COLOR, 100), (0, 60, w, 130)])
                            SoundEffectConstants.wa.play()
                        else:
                            # 成功音を流す
                            if game_info.score.zone[game_info.zone_index][1] == "tech-zone":
                                SoundEffectConstants.special_success.play()
                            else:
                                if game_info.get_key_per_second() > 4:
                                    SoundEffectConstants.fast.play()
                                else:
                                    SoundEffectConstants.success.play()
                    else:
                        # 失敗をカウントする
                        game_info.count_failure()

                        # 効果音を流す
                        SoundEffectConstants.failed.play()

                        # エフェクト
                        ui.add_bg_effector(15, DrawMethodTemplates.blink_screen, [(255, 200, 200)])
                        ui.add_fg_effector(30, DrawMethodTemplates.slide_fadeout_text,
                                           ["WA", more_whiteish(RED_COLOR, 50), ui.alphabet_font,
                                                       10, -150, -383])

        # ------------
        #     計算
        # ------------

        # ===== 歌詞情報が変化したときの処理 =====

        # 歌詞が変わった?
        if lyx_idx:

            # 最終的なタイプ情報を記録する
            game_info.record_sentence_score()

            # TLEした?
            if len(game_info.target_roma) > 0:
                ui.add_fg_effector(30, DrawMethodTemplates.slide_fadeout_text,
                                   ["TLE", more_blackish(RED_COLOR, 50), ui.alphabet_font, -10,
                                               -150, -383])
                ui.add_bg_effector(15, DrawMethodTemplates.blink_rect,
                                   [more_whiteish(RED_COLOR, 50), (0, 60, w, 130)])
                SoundEffectConstants.tle.play()
            else:
                # 歌詞が変わるまでの待機時間を考慮して、前回のキータイプ時間を早める
                game_info.override_key_prev_pos()

            # TLEによる減点を反映して歌詞をアップデートする
            game_info.update_current_lyrics()

            # 曲が終わった?
            if game_info.song_finished:
                # 歌詞情報を消去する
                game_info.update_current_lyrics("", "", False)
                ui.add_bg_effector(60, DrawMethodTemplates.slide_fadeout_text,
                                   ["Song Finished!", (255, 127, 0), ui.system_font, 25, 0, 0])


        # セクションが変わった?
        if sct_idx:

            # セクションを全完した?
            if game_info.section_miss == 0 and game_info.section_count != 0:
                # エフェクトとボーナスポイント
                ui.add_bg_effector(60, DrawMethodTemplates.slide_fadeout_text,
                                   ["Section AC!", (255, 127, 0), ui.system_font, 25, 0, 0])
                game_info.point += game_info.SECTION_PERFECT_POINT

            # セクションごとのタイプ情報を記録
            game_info.record_section_score()

            # セクションのデータを削除
            game_info.reset_section_score()


        # ===== ゲームオーバー処理 =====

        if game_info.point < -300:
            game_finished_reason = "gameover"
            break

        # ----------------
        #     画面描画
        # ----------------

        # [ 背面レイヤー ]

        # 画面を消去する
        ui.screen.fill(BACKGROUND_COLOR)

        # 曲のタイトルなどの情報
        DrawingUtil.write_limit(ui.screen, (w - 2, 0), w / 2, ui.alphabet_font, score_data.properties["title"])
        DrawingUtil.write_limit(ui.screen, (w - 5, 33), w / 2, ui.system_font,
                                score_data.properties["song_author"] + "／" + score_data.properties["singer"],
                                more_whiteish(TEXT_COLOR, 100))

        # 残り時間ゲージ
        pygame.draw.rect(ui.screen, more_blackish(BACKGROUND_COLOR, 25), (0, 60, w, 130))
        pygame.draw.rect(ui.screen, more_blackish(BACKGROUND_COLOR, 50), (0, 60, math.floor(game_info.get_time_remain_ratio() * w), 130))

        # レイヤーが変わるのでここで背景エフェクトを更新する
        ui.update_bg_effector()

        # ----- [ 前面レイヤー ] -----

        # 歌詞
        DrawingUtil.print_progress(ui.screen, (w / 2, 80), MARGIN + 5, ui.get_font_by_size(50),
                                   game_info.typed_kana, game_info.target_kana)
        DrawingUtil.print_progress(ui.screen, (w / 2, 130), MARGIN + 5, ui.full_font,
                                   game_info.typed_roma, game_info.target_roma)

        # 正確率ゲージ
        pygame.draw.rect(ui.screen, GREEN_THICK_COLOR if not game_info.is_ac else RED_COLOR, (0, 60, w * game_info.get_sentence_accuracy(), 3))
        DrawingUtil.write_limit(ui.screen, (w * game_info.get_rate(limit=True), 168), 0, ui.system_font,
                                game_info.rank_string[game_info.calcutate_rank()], more_whiteish(TEXT_COLOR, 100))

        # 達成率ゲージ
        if game_info.calcutate_rank() > 0:
            acheive_rate = game_info.rank_standard[game_info.calcutate_rank() - 1] / 100
            pygame.draw.rect(ui.screen, RED_COLOR, (0, 187, w * acheive_rate, 3))
        pygame.draw.rect(ui.screen, GREEN_THICK_COLOR if game_info.get_rate() < 0.8 else BLUE_THICK_COLOR, (0, 187, w * game_info.get_rate(), 3))

        # キーボード
        keyboard_drawer.draw(ui.screen, 193, ui.full_font, 40, 5, game_info.target_roma[:1], 2,
                             background_color=(192, 192, 192) if game_info.completed else None)

        # 点数表示
        if game_info.point < 0:
            if frame_count % 20 < 10:
                color = RED_COLOR
            else:
                color = BLUE_THICK_COLOR
            ui.print_str(5, 20, ui.alphabet_font, "{:08d}".format(game_info.point), color)
        else:
            ui.print_str(5, 20, ui.alphabet_font, "{:08d}".format(game_info.point), BLUE_THICK_COLOR)


        # --- リアルタイム情報 ---
        pygame.draw.line(ui.screen, more_whiteish(TEXT_COLOR, 100), (0, 375), (w, 375), 2)

        # タイピング速度
        ui.print_str(MARGIN, 382, ui.get_font_by_size(14), "タイピング速度", more_whiteish(TEXT_COLOR, 100))
        if game_info.get_key_per_second() > 4:
            color = more_blackish(RED_COLOR, 30 if frame_count % 10 < 5 else 0)
            pygame.draw.rect(ui.screen, color, (MARGIN, 400, w - MARGIN * 2, 20))
        else:
            pygame.draw.rect(ui.screen,               GREEN_THIN_COLOR     , (MARGIN, 400, w - MARGIN * 2, 20))
            pygame.draw.rect(ui.screen, more_blackish(GREEN_THIN_COLOR, 50), (MARGIN, 400, game_info.get_key_per_second() / 4 * (w - MARGIN * 2), 20))

        DrawingUtil.write_center_x(ui.screen, w / 2, 398, ui.system_font, "{:4.2f} Char/sec".format(game_info.get_key_per_second()), TEXT_COLOR)

        # 正確率の数値情報
        ui.print_str(MARGIN, 430, ui.get_font_by_size(14), "正確率の詳細", more_whiteish(TEXT_COLOR, 100))

        pygame.draw.rect(ui.screen, more_blackish(RED_COLOR, 50),
                         (MARGIN + 10, 510, game_info.get_sentence_accuracy() * 175, 3))
        ui.print_str(MARGIN + 10, 450, ui.system_font, "文単位", more_whiteish(TEXT_COLOR, 50))
        ui.print_str(MARGIN + 10, 460, ui.nihongo_font, "{:06.2f}%".format(game_info.get_sentence_accuracy() * 100),
                     tuple(x * game_info.get_sentence_accuracy() for x in RED_COLOR))

        pygame.draw.rect(ui.screen, more_blackish(TEXT_COLOR, 50),
                         (MARGIN + 200, 510, game_info.get_section_missrate() * 175, 3))
        ui.print_str(MARGIN + 200, 450, ui.system_font, "セクション単位", more_whiteish(TEXT_COLOR, 50))
        ui.print_str(MARGIN + 200, 460, ui.nihongo_font, "{:06.2f}%".format(game_info.get_section_missrate() * 100),
                     tuple(x * game_info.get_section_missrate() for x in RED_COLOR))

        pygame.draw.rect(ui.screen, more_blackish(TEXT_COLOR, 50),
                         (MARGIN + 400, 510, game_info.get_full_accuracy() * 175, 3))
        ui.print_str(MARGIN + 400, 450, ui.system_font, "全体", more_whiteish(TEXT_COLOR, 50))
        ui.print_str(MARGIN + 400, 460, ui.nihongo_font, "{:06.2f}%".format(game_info.get_full_accuracy() * 100),
                     tuple(x * game_info.get_full_accuracy() for x in RED_COLOR))

        # ランク
        ui.print_str(MARGIN, 520, ui.get_font_by_size(14), "達成率", more_whiteish(TEXT_COLOR, 100))
        ui.print_str(MARGIN + 10, 525, ui.get_font_by_size(48), "{:06.2f}%".format(game_info.get_rate() * 100), BLUE_THICK_COLOR)

        ui.print_str(MARGIN + 260, 520, ui.get_font_by_size(14), "次のランクまで", more_whiteish(TEXT_COLOR, 100))
        if game_info.calcutate_rank() > 0:
            acheive_rate = game_info.rank_standard[game_info.calcutate_rank() - 1] - game_info.get_rate() * 100
            ui.print_str(MARGIN + 270, 525, ui.get_font_by_size(48), "{:06.2f}% ".format(acheive_rate), BLUE_THICK_COLOR)
        else:
            ui.print_str(MARGIN + 270, 525, ui.get_font_by_size(48), "N/A", BLUE_THICK_COLOR)

        # レイヤーが変わるのでここで前面エフェクトを更新する
        ui.update_fg_effector()

        # FPSカウンタ
        ui.print_str(3, -3, ui.system_font, "{:5.2f} fps".format(fps_clock.get_fps()), TEXT_COLOR)

        # ループ終わり
        fps_clock.tick(60)
        pygame.display.update()

    # メインループ終了
    print("*****************")
    print("* LOOP FINISHED *")
    print("*****************")
    print(mainloop_continues)
    print(game_finished_reason)

    if game_finished_reason == "gameover":
        ui.add_bg_effector(300, DrawMethodTemplates.blink_screen, [(192, 0, 0)])
        ui.add_bg_effector(300, DrawMethodTemplates.slide_fadeout_text, ["Too many mistake!", (255, 127, 0), ui.nihongo_font, -25, 0, 0])
        SoundEffectConstants.gameover.play()
        for _ in range(300):
            pygame.mixer.music.fadeout(1000)
            ui.update_bg_effector()
            pygame.time.wait(1000 // 60)
            pygame.display.update()




if __name__ == '__main__':
    main()

    pygame.quit()
    sys.exit()