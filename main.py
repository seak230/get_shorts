import os
import argparse
import sys
from src.subtitle_generator import transcribe_video, format_segments_for_shorts
from src.highlight_detector import find_best_highlights
from src.video_processor import render_shorts_highlight

def process_video_to_shorts(
    video_path: str,
    output_dir: str = "output_shorts",
    num_highlights: int = 3,
    target_duration: float = 30.0,
    crop_mode: str = "blur_background",
    whisper_model: str = "base",
    language: str = "ko",
    task: str = "transcribe"
):
    """
    동영상 경로를 받아 하이라이트를 추출하고 쇼츠 자막 동영상을 생성하는 메인 파이프라인.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"입력 동영상 파일이 존재하지 않습니다: {video_path}")

    os.makedirs(output_dir, exist_ok=True)
    print(f"🎬 동영상 처리 시작: {video_path} (언어 설정: {language})")

    # 1. Whisper 음성 인식 및 자막 데이터 추출
    whisper_result = transcribe_video(video_path, model_size=whisper_model, language=language, task=task)
    segments = whisper_result.get('segments', [])

    # 숏폼용 짧은 단위 자막 형성
    shorts_subtitles = format_segments_for_shorts(segments)

    # 2. 음성 에너지 및 대화 밀도 기반 하이라이트 구간 자동 탐색
    print(f"🔍 하이라이트 {num_highlights}개 추출 중 (목표 길이: {target_duration}초)...")
    highlights = find_best_highlights(
        video_path=video_path,
        whisper_segments=segments,
        num_highlights=num_highlights,
        target_duration=target_duration
    )

    if not highlights:
        print("⚠️ 하이라이트 구간을 찾을 수 없습니다.")
        return []

    generated_files = []
    base_name = os.path.splitext(os.path.basename(video_path))[0]

    # 3. 각 하이라이트별 9:16 자막 입힌 쇼츠 생성
    for idx, hl in enumerate(highlights, 1):
        output_filename = f"{base_name}_shorts_{idx}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        subtitle_style = {
            'font_size': 56,
            'text_color': '#FFFF00',  # 쇼츠 노란색 자막
            'stroke_color': '#000000', # 검은 테두리
            'bg_color': '#000000B3'   # 반투명 검은 배경
        }

        render_shorts_highlight(
            video_path=video_path,
            start_time=hl['start'],
            end_time=hl['end'],
            output_path=output_path,
            subtitles=shorts_subtitles,
            crop_mode=crop_mode,
            subtitle_style=subtitle_style
        )
        generated_files.append(output_path)

    print("\n🎉 모든 쇼츠 제작이 완료되었습니다!")
    for filepath in generated_files:
        print(f" - {filepath}")

    return generated_files

def main():
    parser = argparse.ArgumentParser(description="동영상 하이라이트 자동 추출 및 쇼츠(Shorts) 자막 동영상 제작기")
    parser.add_argument("--video", type=str, required=True, help="입력 동영상 파일 경로")
    parser.add_argument("--output_dir", type=str, default="output_shorts", help="결과물 저장 폴더 경로")
    parser.add_argument("--num_highlights", type=int, default=3, help="추출할 하이라이트 개수")
    parser.add_argument("--duration", type=float, default=30.0, help="하이라이트 목표 길이 (초)")
    parser.add_argument("--crop_mode", type=str, choices=["speaker_tracking", "smart_face", "blur_background", "fill_screen", "center_crop", "fit_black"], default="speaker_tracking", help="9:16 비율 화면 변환 방식 (speaker_tracking: 실시간 발언자 얼굴 동적 추적, smart_face: 얼굴인식 고정 꽉 채우기, blur_background: 블러배경)")



    parser.add_argument("--whisper_model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper 모델 크기")
    parser.add_argument("--language", type=str, default="ko", choices=["ko", "en", "auto"], help="자막 선택 언어 (ko: 한국어, en: 영어, auto: 자동감지)")
    parser.add_argument("--task", type=str, default="transcribe", choices=["transcribe", "translate"], help="자막 모드 (transcribe: 원본 자막, translate: 영어로 번역 자막)")

    args = parser.parse_args()

    process_video_to_shorts(
        video_path=args.video,
        output_dir=args.output_dir,
        num_highlights=args.num_highlights,
        target_duration=args.duration,
        crop_mode=args.crop_mode,
        whisper_model=args.whisper_model,
        language=args.language,
        task=args.task
    )


if __name__ == "__main__":
    main()
