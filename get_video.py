import os
import argparse
import yt_dlp
import imageio_ffmpeg

def download_youtube_video(
    url: str,
    output_dir: str = "input_videos",
    resolution: str = "1080p"
) -> str:
    """
    유튜브 URL을 전달받아 최고 화질/음질의 동영상(MP4)을 다운로드합니다.

    Args:
        url (str): 유튜브 동영상 URL
        output_dir (str): 저장할 폴더 경로
        resolution (str): 해상도 선호도 (예: 720p, 1080p, best)

    Returns:
        str: 다운로드된 동영상 파일의 절대 경로
    """
    os.makedirs(output_dir, exist_ok=True)
    print(f"📥 유튜브 동영상 다운로드 시도 중: {url}")

    # imageio_ffmpeg에 번들된 ffmpeg 실행 파일 경로 설정
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # yt-dlp 옵션 설정
    ydl_opts = {
        'ffmpeg_location': ffmpeg_exe,
        'format': f'bestvideo[ext=mp4][height<={resolution.replace("p","")}] + bestaudio[ext=m4a]/bestvideo[height<={resolution.replace("p","")}] + bestaudio/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
    except Exception as e:
        print(f"⚠️ 병합 인코딩 중 예외 발생: {e}. 단일 통합 포맷으로 재시도합니다.")
        # ffmpeg 병합 필요 없는 단일 MP4 포맷 폴백
        ydl_opts['format'] = 'best[ext=mp4]/best'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)

    base_path, _ = os.path.splitext(filename)
    mp4_filename = f"{base_path}.mp4"
    
    if os.path.exists(mp4_filename):
        final_path = os.path.abspath(mp4_filename)
    elif os.path.exists(filename):
        final_path = os.path.abspath(filename)
    else:
        raise FileNotFoundError("다운로드된 비디오 파일을 찾을 수 없습니다.")

    print(f"✅ 다운로드 완료: {final_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="유튜브 URL에서 동영상 파일 다운로드")
    parser.add_argument("--url", type=str, required=True, help="다운로드할 유튜브 동영상 URL")
    parser.add_argument("--output_dir", type=str, default="input_videos", help="동영상 저장 폴더 경로")
    parser.add_argument("--resolution", type=str, default="1080p", help="최대 해상도 (720p, 1080p 등)")
    parser.add_argument("--make_shorts", action="store_true", help="다운로드 완료 후 자동으로 하이라이트 쇼츠 제작 연동")
    parser.add_argument("--crop_mode", type=str, default="speaker_tracking", choices=["speaker_tracking", "smart_face", "blur_background", "fill_screen", "center_crop", "fit_black"], help="화면 변환 방식 (speaker_tracking: 동적 발언자 추적, smart_face: 대표얼굴 꽉 채우기, blur_background: 블러배경)")

    parser.add_argument("--language", type=str, default="auto", choices=["ko", "en", "auto"], help="자막 인식 언어 (ko: 한국어, en: 영어, auto: 자동감지)")
    parser.add_argument("--whisper_model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper 모델 크기")

    args = parser.parse_args()

    # 동영상 다운로드
    video_path = download_youtube_video(
        url=args.url,
        output_dir=args.output_dir,
        resolution=args.resolution
    )

    # 필요시 바로 쇼츠 제작 파이프라인과 연동
    if args.make_shorts:
        print(f"\n🚀 쇼츠 자동 제작 파이프라인으로 연동합니다 (언어: {args.language}, 레이아웃: {args.crop_mode})...")
        from main import process_video_to_shorts
        process_video_to_shorts(
            video_path=video_path,
            crop_mode=args.crop_mode,
            language=args.language,
            whisper_model=args.whisper_model
        )



if __name__ == "__main__":
    main()
