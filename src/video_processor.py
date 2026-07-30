import os
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageFilter

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
except ImportError:
    from moviepy import VideoFileClip, CompositeVideoClip, ImageClip

# FFmpeg PATH 설정
try:
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

# MoviePy v1 / v2 호환용 헬퍼 함수들
def safe_subclip(clip, start, end):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)

def safe_resize(clip, size_or_factor):
    if hasattr(clip, "resized"):
        return clip.resized(size_or_factor)
    return clip.resize(size_or_factor)

def safe_crop(clip, **kwargs):
    if hasattr(clip, "cropped"):
        return clip.cropped(**kwargs)
    return clip.crop(**kwargs)

def safe_position(clip, pos):
    if hasattr(clip, "with_position"):
        return clip.with_position(pos)
    return clip.set_position(pos)

def safe_duration(clip, dur):
    if hasattr(clip, "with_duration"):
        return clip.with_duration(dur)
    return clip.set_duration(dur)

def make_blurred_frame(get_frame, t, target_size=(1080, 1920)):
    """현재 프레임을 가져와 블러 처리된 9:16 배경 프레임을 생성합니다."""
    frame = get_frame(t)
    pil_img = Image.fromarray(frame)
    
    target_w, target_h = target_size
    img_w, img_h = pil_img.size

    scale = max(target_w / img_w, target_h / img_h)
    new_w, new_h = int(img_w * scale), int(img_h * scale)
    
    resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    cropped = resized.crop((left, top, left + target_w, top + target_h))
    
    blurred = cropped.filter(ImageFilter.GaussianBlur(radius=25))
    darkened = Image.eval(blurred, lambda p: int(p * 0.5))
    return np.array(darkened)

def detect_face_center_x(clip, num_samples: int = 12) -> float:
    """
    OpenCV 다중 캐스케이드(Frontal + Profile) 모델을 이용해
    동영상 속 인물의 대표 얼굴 X 중심 좌표를 추적합니다.
    """
    orig_w, _ = clip.size
    default_x = orig_w / 2.0

    try:
        import cv2
        cascades = [
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'),
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        ]
    except Exception as e:
        print(f"[경고] OpenCV 감지기 로딩 실패: {e}")
        return default_x

    duration = clip.duration
    sample_times = np.linspace(0.1, max(0.1, duration - 0.1), num=num_samples)
    detected_x_centers = []

    for t in sample_times:
        try:
            frame = clip.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            frame_faces = []
            for cascade in cascades:
                if cascade is None or cascade.empty():
                    continue
                faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                if len(faces) > 0:
                    frame_faces.extend(faces)

            if len(frame_faces) > 0:
                largest_face = max(frame_faces, key=lambda rect: rect[2] * rect[3])
                fx, fy, fw, fh = largest_face
                face_center_x = fx + (fw / 2.0)
                detected_x_centers.append(face_center_x)
        except Exception:
            continue

    if detected_x_centers:
        median_x = float(np.median(detected_x_centers))
        print(f"👤 스마트 얼굴 추적 성공: 대표 X 중심 = {median_x:.1f}px (전체 {orig_w}px 중)")
        return median_x

    print(f"⚠️ 얼굴 감지 실패: 기본 중앙값({default_x:.1f}px) 사용")
    return default_x

def get_dynamic_speaker_trajectory(clip, sample_interval: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """
    영상 재생 시간에 따른 실시간 발언자 얼굴 X 좌표 트래킹 궤적(Trajectory)을 산출합니다.
    노이즈 제거를 위한 이동 평균 스무딩(Smoothing)을 적용합니다.
    """
    orig_w, _ = clip.size
    default_x = orig_w / 2.0

    try:
        import cv2
        cascades = [
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'),
            cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        ]
    except Exception:
        return np.array([0.0, clip.duration]), np.array([default_x, default_x])

    duration = clip.duration
    sample_times = np.arange(0.0, duration, sample_interval)
    if len(sample_times) == 0:
        sample_times = np.array([0.0])

    raw_x_centers = []
    last_x = default_x

    for t in sample_times:
        try:
            frame = clip.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            frame_faces = []
            for cascade in cascades:
                if cascade is None or cascade.empty():
                    continue
                faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                if len(faces) > 0:
                    frame_faces.extend(faces)

            if len(frame_faces) > 0:
                largest_face = max(frame_faces, key=lambda rect: rect[2] * rect[3])
                fx, fy, fw, fh = largest_face
                current_x = fx + (fw / 2.0)
                last_x = current_x
                raw_x_centers.append(current_x)
            else:
                raw_x_centers.append(last_x)
        except Exception:
            raw_x_centers.append(last_x)

    raw_x_centers = np.array(raw_x_centers, dtype=np.float64)
    
    # 3프레임 이동 평균 스무딩 (자연스러운 카메라 이동/스위칭)
    window_len = 3
    if len(raw_x_centers) >= window_len:
        smoothed_x = np.convolve(raw_x_centers, np.ones(window_len)/window_len, mode='same')
    else:
        smoothed_x = raw_x_centers

    print(f"🎥 동적 발언자 트래킹 궤적 추출 완료 ({len(sample_times)}개 타임스탬프 분석)")
    return sample_times, smoothed_x

def make_dynamic_speaker_frame(get_frame, t, sample_times, smoothed_x, target_size=(1080, 1920), orig_size=(1920, 1080)):
    """현재 시간에 맞춰 발언자 얼굴 중심 위치로 프레임을 동적으로 전환/크롭합니다."""
    frame = get_frame(t)
    pil_img = Image.fromarray(frame)

    target_w, target_h = target_size
    orig_w, orig_h = orig_size

    scale = max(target_w / orig_w, target_h / orig_h)
    new_w, new_h = int(orig_w * scale), int(orig_h * scale)
    resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)

    # t 시점의 X 좌표 보간
    current_x_orig = np.interp(t, sample_times, smoothed_x)
    scaled_x = current_x_orig * scale

    half_w = target_w / 2.0
    clamped_x = max(half_w, min(new_w - half_w, scaled_x))

    left = int(clamped_x - half_w)
    top = (new_h - target_h) // 2
    
    cropped = resized.crop((left, top, left + target_w, top + target_h))
    return np.array(cropped)

def format_video_to_shorts(
    clip: VideoFileClip,
    target_size: tuple[int, int] = (1080, 1920),
    crop_mode: str = "speaker_tracking"
) -> CompositeVideoClip:
    """
    일반 16:9 등의 동영상을 9:16 수직 쇼츠 포맷으로 전환합니다.
    """
    target_w, target_h = target_size
    orig_w, orig_h = clip.size

    if crop_mode in ["speaker_tracking", "smart_speaker", "dynamic_speaker"]:
        # 실시간 발언자 얼굴 동적 추적 스위칭 (Dynamic Speaker Tracking)
        sample_times, smoothed_x = get_dynamic_speaker_trajectory(clip, sample_interval=0.4)
        
        if hasattr(clip, "transform"):
            dynamic_clip = clip.transform(
                lambda gf, t: make_dynamic_speaker_frame(gf, t, sample_times, smoothed_x, target_size, (orig_w, orig_h))
            )
        else:
            dynamic_clip = clip.fl(
                lambda gf, t: make_dynamic_speaker_frame(gf, t, sample_times, smoothed_x, target_size, (orig_w, orig_h))
            )
        return dynamic_clip

    elif crop_mode in ["smart_face", "face_crop"]:
        # 대표 얼굴 중심 고정 크롭
        scale = max(target_w / orig_w, target_h / orig_h)
        scaled_clip = safe_resize(clip, scale)
        
        face_x_orig = detect_face_center_x(clip)
        scaled_face_x = face_x_orig * scale
        
        half_crop_w = target_w / 2.0
        clamped_x = max(half_crop_w, min(scaled_clip.w - half_crop_w, scaled_face_x))

        final_clip = safe_crop(
            scaled_clip,
            x_center=clamped_x,
            y_center=scaled_clip.h / 2,
            width=target_w,
            height=target_h
        )
        return final_clip

    elif crop_mode in ["center_crop", "fill_screen", "full_screen"]:
        scale = max(target_w / orig_w, target_h / orig_h)
        scaled_clip = safe_resize(clip, scale)
        final_clip = safe_crop(
            scaled_clip,
            x_center=scaled_clip.w / 2,
            y_center=scaled_clip.h / 2,
            width=target_w,
            height=target_h
        )
        return final_clip

    elif crop_mode == "blur_background":
        if hasattr(clip, "transform"):
            bg_clip = clip.transform(lambda gf, t: make_blurred_frame(gf, t, target_size))
        else:
            bg_clip = clip.fl(lambda gf, t: make_blurred_frame(gf, t, target_size))
        
        scale_w = target_w / orig_w
        foreground = safe_resize(clip, scale_w)
        foreground = safe_position(foreground, ("center", "center"))

        return CompositeVideoClip([bg_clip, foreground], size=target_size)

    else: # fit_black
        scale_w = target_w / orig_w
        foreground = safe_position(safe_resize(clip, scale_w), ("center", "center"))
        bg = safe_duration(ImageClip(np.zeros((target_h, target_w, 3), dtype=np.uint8)), clip.duration)
        return CompositeVideoClip([bg, foreground], size=target_size)

def render_shorts_highlight(
    video_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    subtitles: list = None,
    crop_mode: str = "speaker_tracking",
    subtitle_style: dict = None
):
    """
    지정된 구간(하이라이트)을 자르고 자막을 입혀 쇼츠 동영상 파일로 저장합니다.
    """
    print(f"\n[Shorts 제작 중] {start_time:.1f}s ~ {end_time:.1f}s -> {output_path}")
    
    full_video = VideoFileClip(video_path)
    sub_clip = safe_subclip(full_video, start_time, end_time)

    target_size = (1080, 1920)
    shorts_base = format_video_to_shorts(sub_clip, target_size=target_size, crop_mode=crop_mode)

    all_clips = [shorts_base]
    if subtitles:
        from src.subtitle_generator import generate_subtitle_clips
        sub_clips = generate_subtitle_clips(
            subtitles=subtitles,
            highlight_start=start_time,
            highlight_end=end_time,
            video_size=target_size,
            style_options=subtitle_style
        )
        all_clips.extend(sub_clips)

    final_video = CompositeVideoClip(all_clips, size=target_size)
    final_video.duration = sub_clip.duration
    
    if hasattr(sub_clip, "audio") and sub_clip.audio is not None:
        final_video.audio = sub_clip.audio

    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="fast",
        threads=4,
        logger=None
    )

    sub_clip.close()
    full_video.close()
    print(f"✅ 완성: {output_path}")
