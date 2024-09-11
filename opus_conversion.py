# このプログラムは入力の音楽ファイルのディレクトリー構成を保ったまま
# opusファイルに変換するプログラムです
# 別途必要な実行ファイル
# opusenc.exe : opusファイルを作成するのに必要です
# ffmpeg.exe : 様々な音楽ファイルをwavに変換し、opusenc.exeに渡すために必要です

import os
import subprocess
import ffmpeg

# タグとカバーアート用のライブラリ群（工事中）
# from io import BytesIO
# from PIL import Image
# from mutagen.easyid3 import EasyID3
# from mutagen.mp3 import MP3
# from mutagen.flac import FLAC


TARGET_FILE_TYPE = [".flac","mp3"]
OPUS_EXT = ".opus"
WAV_EXT = ".wav"

# 入力するディレクトリーのパスと、その上のディレクトリーの名前を取得
input_dir_pass = "music_input"
input_dir_root_pass = os.path.abspath(os.path.dirname(input_dir_pass))
# 出力するディレクトリーのパスと、その上のディレクトリーの名前を取得
output_dir_pass = "music_output"
output_dir_root_pass = os.path.abspath(os.path.dirname(output_dir_pass))

# ファイルパスのリスト
# (input_file_pass, output_file_pass, wav_file_pass)のタプルを入れる
file_pass_list = []

bitrate = "96k"


def copy_directory(src, dst):
    # この関数は、元のディレクトリー構造をコピー先に作り出します
    # src:コピー元のディレクトリーのパス
    # dst:コピー先のディレクトリーのパス
    
    os.makedirs(dst, exist_ok=True)
    
    # ディレクトリー構造をコピー
    # もしすでにディレクトリーが存在したら、そのまま上書き
    for root, dirs, files in os.walk(src):
        for dir in dirs:
            src_dir = os.path.join(root, dir)       # 入力のディレクトリー構造のパス
            dst_dir = src_dir.replace(src, dst)     # 出力のディレクトリー構造のパス
            os.makedirs(dst_dir, exist_ok=True)
            
        # ファイルが見つかった階層で、ターゲットファイルがあるかどうかチェック
        if len(files) > 0:
            target_file_check(src_dir, dst_dir)
            
def target_file_check(src_dir, dst_dir):    
    # src_dirに存在する音楽ファイルのチェック
    for root, dirs, files in os.walk(src_dir):
        for input_file in files:
            filename, ext = os.path.splitext(input_file)
            if ext in TARGET_FILE_TYPE:
                # もしターゲットの拡張子と一致したら
                # 入力パスと出力パスのリストに追加
                output_file = filename + str(OPUS_EXT)
                wav_file = filename + str(WAV_EXT)
                
                abs_input_pass = os.path.join(input_dir_root_pass, os.path.join(src_dir, input_file))
                abs_output_pass = os.path.join(output_dir_root_pass, os.path.join(dst_dir, output_file))
                abs_wav_pass = os.path.join(output_dir_root_pass, os.path.join(dst_dir, wav_file))
                
                file_pass_list.append((abs_input_pass, abs_output_pass, abs_wav_pass))

def file_pass_check():
    # 入力のターゲットのファイルパス一覧
    for list in file_pass_list:
        print(f"input file pass:{list[0]}")
        print(f"output file pass:{list[1]}")
        print(f"wav file pass:{list[2]}")
    
def convert_opus():
    # 一度すべてWAVファイルに変換する
    for file_pass in file_pass_list:
        input_file = file_pass[0]
        output_file = file_pass[1]
        wav_file = file_pass[2]
        
        # ファイルの種類別にタグとカバーアートを取得
        # タグ情報は埋め込みが難しいので工事中　2024/09/11
        
        # filename, ext = os.path.splitext(input_file)
        # if ext == ".flac":
        #     tags = FLAC(input_file)
        #     apic = tags.pictures
        #     for picture in apic:
        #         try:
        #             cover_img = Image.open(BytesIO(picture.data))
        #         except IOError:
        #             print("Error opening image")
        # elif ext == ".mp3":
        #     tags = MP3(input_file)
        #     apic = tags.pictures
        #     for picture in apic:
        #         try:
        #             cover_img = Image.open(BytesIO(picture.data))
        #         except IOError:
        #             print("Error opening image")
        
        stream = ffmpeg.input(input_file)
        stream = ffmpeg.output(stream, wav_file)
        ffmpeg.run(stream, quiet=True)          # コンソール表示をOFFのまま変換を実行
        
        subpro_opus(wav_file,output_file, bitrate)
        
        # 生成した中間ファイルのWAVファイルを削除
        if os.path.exists(wav_file):
            os.remove(wav_file)
        
        
def subpro_opus(input_wav, output_opus, bitrate="96k"):
    """
    Wave, AIFF, FLAC, Ogg/FLAC, or raw PCM ファイルを opus ファイルに変換する関数

    Args:
        input_wav (str): 入力 wav ファイルのパス
        output_opus (str): 出力 opus ファイルのパス
        bitrate (str, optional): ビットレート. Defaults to "96k".
    """

    # opusenc コマンドの作成
    command = ["opusenc", input_wav, output_opus, "--bitrate", bitrate]

    # コマンドの実行
    try:
        subprocess.run(command, check=True)
        print(f"変換が完了しました: {input_wav} -> {output_opus}")
    except subprocess.CalledProcessError as e:
        print(f"エラーが発生しました: {e}")

def main():
    copy_directory(input_dir_pass, output_dir_pass)
    # file_pass_check()
    convert_opus()
    
    
if __name__ == "__main__" :
    main()