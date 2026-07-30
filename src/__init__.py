import os
import imageio_ffmpeg

# imageio-ffmpeg 실행 파일 디렉토리를 시스템 PATH에 추가하여 whisper, moviepy, subprocess 등에서 ffmpeg를 찾을 수 있도록 설정
try:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception as e:
    print(f"[경고] FFmpeg PATH 설정 중 예외: {e}")
