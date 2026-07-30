import os
import imageio_ffmpeg

# FFmpeg PATH 설정 (Whisper 및 MoviePy 공통 사용)
try:
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

HAS_WHISPER = False
try:
    import whisper
    HAS_WHISPER = True
except (ImportError, OSError) as e:
    print(f"[알림] PyTorch/Whisper 로딩 중 제한 감지 ({e}). 대체 음성 인식 엔진을 준비합니다.")
    HAS_WHISPER = False

import numpy as np
from PIL import Image, ImageDraw, ImageFont
try:
    from moviepy.editor import ImageClip, CompositeVideoClip
except ImportError:
    from moviepy import ImageClip, CompositeVideoClip



def get_default_font(font_size: int = 54):
    """윈도우 및 일반 환경에 적합한 한글/영문 폰트를 로드합니다."""
    font_paths = [
        "C:\\Windows\\Fonts\\malgunbd.ttf", # 맑은 고딕 볼드
        "C:\\Windows\\Fonts\\malgun.ttf",   # 맑은 고딕
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    return ImageFont.load_default()

def transcribe_video(video_path: str, model_size: str = "base", language: str = "ko", task: str = "transcribe") -> dict:
    """Whisper 또는 SpeechRecognition 엔진을 이용해 비디오의 음성을 텍스트 및 타임스탬프와 함께 인식합니다."""
    if HAS_WHISPER:
        print(f"[Whisper] 모델 '{model_size}' 로딩 및 음성 인식 중 (언어: {language}, 태스크: {task})...")
        try:
            model = whisper.load_model(model_size)
            result = model.transcribe(
                video_path,
                language=language if language != "auto" else None,
                task=task,
                verbose=False
            )
            return result
        except Exception as e:
            print(f"[알림] Whisper 음성 인식 런타임 오류 ({e}). 대체 백엔드로 전환합니다.")


    # SpeechRecognition / Google STT 대체 처리
    print("[SpeechRecognition] 온라인 음성 인식 엔진을 준비 중입니다...")
    try:
        import speech_recognition as sr
        try:
            import moviepy.editor as mp
        except ImportError:
            import moviepy as mp


        temp_wav = "temp_stt.wav"
        video = mp.VideoFileClip(video_path)
        if video.audio is None:
            return {"segments": []}
        video.audio.write_audiofile(temp_wav, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
        duration = video.duration
        video.close()

        r = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='ko-KR' if language == 'ko' else 'en-US')

        if os.path.exists(temp_wav):
            os.remove(temp_wav)

        return {
            "text": text,
            "segments": [{
                "start": 0.0,
                "end": duration,
                "text": text
            }]
        }
    except Exception as err:
        print(f"[알림] 대체 음성 인식 중 오류 발생: {err}")
        return {"segments": []}


def format_segments_for_shorts(segments: list, max_words_per_chunk: int = 4) -> list:
    """
    Whisper 세그먼트를 숏폼 형식에 맞게 짧은 단어 단위 타임스탬프로 분할합니다.
    """
    shorts_subtitles = []
    for seg in segments:
        text = seg['text'].strip()
        if not text:
            continue
            
        words = text.split()
        if not words:
            continue

        seg_start = seg['start']
        seg_end = seg['end']
        duration = max(0.1, seg_end - seg_start)

        # 단어 수에 맞춰 시간을 나눔
        chunk_size = max(1, max_words_per_chunk)
        num_chunks = (len(words) + chunk_size - 1) // chunk_size
        time_per_chunk = duration / num_chunks

        for i in range(num_chunks):
            chunk_words = words[i * chunk_size : (i + 1) * chunk_size]
            chunk_text = " ".join(chunk_words)
            c_start = seg_start + (i * time_per_chunk)
            c_end = seg_start + ((i + 1) * time_per_chunk)
            shorts_subtitles.append({
                'start': c_start,
                'end': c_end,
                'text': chunk_text
            })

    return shorts_subtitles

def create_subtitle_image(
    text: str,
    video_width: int,
    video_height: int,
    font_size: int = 54,
    text_color: str = "#FFFFFF",
    stroke_color: str = "#000000",
    stroke_width: int = 4,
    bg_color: str = "#000000AA"
) -> Image.Image:
    """
    PIL을 이용하여 쇼츠용 고화질 자막 이미지(RGBA)를 생성합니다.
    """
    img = Image.new("RGBA", (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_default_font(font_size)

    # 텍스트 바운딩 박스 계산
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 자막 위치 (하단 3/4 위치 또는 중앙 하단)
    x = (video_width - text_w) // 2
    y = int(video_height * 0.75) - (text_h // 2)

    # 배경 패딩 박스 (Pill 형태)
    padding_x = 24
    padding_y = 12
    bg_box = [
        x - padding_x,
        y - padding_y,
        x + text_w + padding_x,
        y + text_h + padding_y
    ]
    
    if bg_color:
        draw.rounded_rectangle(bg_box, radius=16, fill=bg_color)

    # 외곽선(Stroke) 그리기
    if stroke_width > 0:
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)

    # 본문 텍스트 그리기
    draw.text((x, y), text, font=font, fill=text_color)
    return img

def generate_subtitle_clips(
    subtitles: list,
    highlight_start: float,
    highlight_end: float,
    video_size: tuple[int, int],
    style_options: dict = None
) -> list:
    """
    특정 하이라이트 구간에 포함되는 자막 MoviePy ImageClip 리스트를 생성합니다.
    """
    if style_options is None:
        style_options = {}

    font_size = style_options.get('font_size', 54)
    text_color = style_options.get('text_color', '#FFFF00') # 쇼츠 시그니처 노란색
    stroke_color = style_options.get('stroke_color', '#000000')
    bg_color = style_options.get('bg_color', '#000000B3')

    w, h = video_size
    clips = []

    for sub in subtitles:
        # 하이라이트 구간과 자막 구간 겹침 여부 확인
        if sub['end'] <= highlight_start or sub['start'] >= highlight_end:
            continue

        # 상대적 시간 계산 (클립 내 시작/종료 시간)
        rel_start = max(0.0, sub['start'] - highlight_start)
        rel_end = min(highlight_end - highlight_start, sub['end'] - highlight_start)
        duration = rel_end - rel_start

        if duration <= 0.05:
            continue

        pil_img = create_subtitle_image(
            text=sub['text'],
            video_width=w,
            video_height=h,
            font_size=font_size,
            text_color=text_color,
            stroke_color=stroke_color,
            bg_color=bg_color
        )

        img_np = np.array(pil_img)
        clip = ImageClip(img_np)
        if hasattr(clip, "with_start"):
            clip = clip.with_start(rel_start).with_duration(duration)
        else:
            clip = clip.set_start(rel_start).set_duration(duration)
        clips.append(clip)


    return clips
