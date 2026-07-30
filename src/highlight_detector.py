import os
import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile
try:
    import moviepy.editor as mp
except ImportError:
    import moviepy as mp

# FFmpeg PATH 설정
try:
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

def extract_audio_from_video(video_path: str, temp_audio_path: str = "temp_audio.wav") -> str:
    """비디오 파일에서 오디오를 추출하여 WAV 파일로 저장합니다."""
    video = mp.VideoFileClip(video_path)
    if video.audio is None:
        raise ValueError("입력 비디오에 오디오 트랙이 없습니다.")
    video.audio.write_audiofile(temp_audio_path, fps=16000, nbytes=2, codec='pcm_s16le', logger=None)
    video.close()
    return temp_audio_path


def detect_audio_energy_peaks(audio_path: str, window_sec: float = 0.5) -> tuple[np.ndarray, float]:
    """오디오 신호의 RMS 에너지(볼륨 크기)를 계산합니다."""
    sample_rate, data = wavfile.read(audio_path)
    if len(data.shape) > 1:
        data = data.mean(axis=1) # 모노 변환
    
    samples_per_window = int(sample_rate * window_sec)
    num_windows = len(data) // samples_per_window
    
    energies = []
    for i in range(num_windows):
        window = data[i * samples_per_window : (i + 1) * samples_per_window]
        rms = np.sqrt(np.mean(window.astype(np.float64) ** 2))
        energies.append(rms)
        
    energies = np.array(energies)
    if len(energies) > 0 and np.max(energies) > 0:
        energies = energies / np.max(energies) # 0~1 정규화
    return energies, window_sec

def find_best_highlights(
    video_path: str,
    whisper_segments: list = None,
    num_highlights: int = 3,
    target_duration: float = 30.0,
    min_duration: float = 15.0,
    max_duration: float = 55.0
) -> list[dict]:
    """
    오디오 볼륨 피크 및 Whisper 자막 밀도를 기반으로 최고의 하이라이트 구간을 선택합니다.
    
    Returns:
        [{"start": float, "end": float, "score": float}, ...]
    """
    temp_audio = extract_audio_from_video(video_path)
    try:
        energies, window_sec = detect_audio_energy_peaks(temp_audio)
    finally:
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except Exception:
                pass

    total_duration = len(energies) * window_sec
    if total_duration <= min_duration:
        # 비디오 전체가 너무 짧은 경우
        return [{"start": 0.0, "end": total_duration, "score": 1.0}]

    # 세그먼트별 스코어링 테이블 생성 (0.5초 단위)
    scores = np.copy(energies)

    # Whisper 세그먼트 정보가 있으면 말하는 구간/단어 밀도 점수 추가
    if whisper_segments:
        speech_mask = np.zeros_like(scores)
        for seg in whisper_segments:
            start_idx = int(seg['start'] / window_sec)
            end_idx = int(seg['end'] / window_sec)
            start_idx = max(0, min(len(speech_mask) - 1, start_idx))
            end_idx = max(0, min(len(speech_mask), end_idx))
            speech_mask[start_idx:end_idx] += 0.5 # 대화 구간 가산점
        scores = scores + speech_mask

    # 슬라이딩 윈도우 방식으로 가장 점수가 높은 구간 검색
    window_steps = int(target_duration / window_sec)
    half_step = window_steps // 2

    candidates = []
    num_total_windows = len(scores)

    for i in range(0, num_total_windows - window_steps, int(2.0 / window_sec)):
        chunk_score = np.sum(scores[i : i + window_steps])
        start_time = i * window_sec
        end_time = min(total_duration, start_time + target_duration)
        candidates.append({
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "score": round(float(chunk_score), 2)
        })

    # 점수 높은 순으로 정렬
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 중복(겹침) 없는 하이라이트 선택
    selected_highlights = []
    for cand in candidates:
        if len(selected_highlights) >= num_highlights:
            break
        
        # 기존 선택 구간과의 겹침 체크
        overlap = False
        for sel in selected_highlights:
            # 두 구간이 겹치는지 체크
            if not (cand["end"] <= sel["start"] or cand["start"] >= sel["end"]):
                overlap = True
                break
        
        if not overlap:
            selected_highlights.append(cand)

    # 시간순 정렬
    selected_highlights.sort(key=lambda x: x["start"])
    return selected_highlights
