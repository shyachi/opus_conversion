# このプログラムは入力の音楽ファイルのディレクトリー構成を保ったまま
# opusファイルに変換するプログラムです
# 別途必要な実行ファイル
# opusenc.exe : opusファイルを作成するのに必要です
# ffmpeg.exe : 様々な音楽ファイルをwavに変換し、opusenc.exeに渡すために必要です

import os
import shutil

INPUT_DIR_PASS = "music_input"
OUTPUT_DIR_PASS = "music_output"

def copy_directory(src, dst):
    # この関数は、元のディレクトリー構造をコピー先に再帰的に作り出します
    # src:コピー元のディレクトリーのパス
    # dst:コピー先のディレクトリーのパス
    
    os.makedirs(dst, exist_ok=True)
    
    # 再帰的にディレクトリーをコピー
    # もしすでにディレクトリーが存在したら、そのまま上書き
    for root, dirs, files in os.walk(src):
        for dir in dirs:
            src_dir = os.path.join(root, dir)       # 入力のディレクトリー構造のパス
            dst_dir = src_dir.replace(src, dst)     # 出力のディレクトリー構造のパス
            os.makedirs(dst_dir, exist_ok=True)
            test_foo(dst_dir)
            
def test_foo(dst):
    # 将来的に、ここでファイル変換をします
    print(f"現在のディレクトリー構造:{dst}")
    
def main():
    copy_directory(INPUT_DIR_PASS, OUTPUT_DIR_PASS)
    
if __name__ == "__main__" :
    main()