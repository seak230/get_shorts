# 🎬 AI 유튜브 동영상 하이라이트 쇼츠(Shorts) 제작기

긴 동영상이나 유튜브 URL을 전달받아 **자동으로 최고 하이라이트 구간을 추출**하고, **실시간 발언자 얼굴 추적 9:16 수직 화면(유튜브 쇼츠, 틱톡, 릴스 포맷) 변환** 및 **쇼츠 자막(Captions)**을 합성해 주는 파이썬 프로젝트입니다.

---

## 🌟 주요 기능

1. **📥 유튜브 URL 자동 동영상 추출 (`get_video.py`)**
   - 유튜브 URL 하나로 최고 1080p 화질의 영상과 음성을 다운로드하고, 즉시 쇼츠 제작 파이프라인으로 연동합니다.

2. **🔍 AI 자동 하이라이트 구간 탐색 (`src/highlight_detector.py`)**
   - 오디오 RMS 음성 볼륨 피크(Energy Peak)와 Whisper 대화 밀도를 합성 계산하여 흥미도가 높은 하이라이트 구간(기본 30초)을 자동 선택합니다.

3. **🎥 실시간 발언자 얼굴 동적 추적 카메라 렌더링 (`src/video_processor.py`)**
   - **`speaker_tracking` (추천/기본값)**: OpenCV 다중 캐스케이드(Frontal + Profile) 모델로 팟캐스트나 대화 영상에서 **말하는 사람의 위치로 카메라인이 실시간 이동/스위칭**됩니다.
   - **`smart_face`**: 대표 인물의 얼굴 위치를 파악하여 9:16 중앙에 맞춰 크롭합니다.
   - **`fill_screen`**: 9:16 화면에 비디오를 꽉 채워 크롭합니다.
   - **`blur_background`**: 화면 중앙에 비디오 배치 및 상하 배경 블러(GaussianBlur) 처리.
   - **`fit_black`**: 상하 검은색 여백 레이아웃.

4. **🎙️ Whisper AI 음성 인식 & 멀티 언어 쇼츠 자막 (`src/subtitle_generator.py`)**
   - OpenAI Whisper 모델 기반으로 텍스트 및 정확한 타임스탬프를 추출합니다.
   - **다국어 지원**: 한국어(`ko`), 영어(`en`), 자동 감지(`auto`) 지원.
   - **영어 번역 모드**: 외국어 음성을 영어 자막으로 번역 변환(`--task translate`) 지원.
   - **이중화 백엔드**: OS 보안 정책(WinError 4551 등) 예외 발생 시 `SpeechRecognition` (Google STT) 백업 엔진으로 자동 전환되어 절대 다운되지 않습니다.
   - **쇼츠 시그니처 디자인**: 1~4단어 단위의 노란색 고대비 테두리 자막과 반투명 배경 알약 상자를 렌더링합니다.

5. **💻 CLI 및 웹 GUI(Gradio) 인터페이스 지원 (`main.py` / `app.py`)**

---

## 🛠️ 설치 방법

```bash
# 가상환경 접속 후 패키지 설치
pip install -r requirements.txt
```

> **참고**: `imageio-ffmpeg` 및 Windows 기본 폰트(맑은 고딕)가 내장되어 있어 별도의 외부 FFmpeg 인스톨러나 폰트 설치 없이 즉시 실행 가능합니다.

---

## 🚀 사용 방법

### 1. 유튜브 URL 입력하여 다운로드 + 쇼츠 자동 생성 (`get_video.py`)

```powershell
# 유튜브 영상 다운로드 및 실시간 발언자 추적 쇼츠 자동 생성 (영문/한국어 선택 가능)
python get_video.py --url "https://youtu.be/SwQhKFMxmDY" --make_shorts --crop_mode speaker_tracking --language auto
```

### 2. 파일로 직접 CLI 실행 (`main.py`)

```powershell
python main.py --video "input_videos/sample.mp4" --num_highlights 3 --duration 30 --crop_mode speaker_tracking --language ko
```

#### 📋 `main.py` 전체 옵션 목록:

| 옵션명 | 필수 여부 | 기본값 | 선택 가능 값 | 설명 |
| :--- | :---: | :---: | :--- | :--- |
| **`--video`** | **필수** | - | 동영상 파일 경로 | 입력 원본 동영상 파일 경로 |
| **`--crop_mode`** | 선택 | `speaker_tracking` | `speaker_tracking`<br>`smart_face`<br>`fill_screen`<br>`blur_background`<br>`fit_black` | **9:16 비디오 화면 레이아웃 변환 모드**<br>• `speaker_tracking`: 실시간 발언자 동적 추적<br>• `smart_face`: 인물 대표얼굴 고정 꽉 채우기<br>• `fill_screen`: 화면 꽉 채우기 (단순 중앙)<br>• `blur_background`: 중앙 배치 + 상하 블러 배경<br>• `fit_black`: 상하 검은색 여백 |
| **`--language`** | 선택 | `ko` | `ko`, `en`, `auto` | **자막 음성 언어** (`ko`: 한국어, `en`: 영어, `auto`: 자동감지) |
| **`--task`** | 선택 | `transcribe` | `transcribe`<br>`translate` | **자막 모드** (`transcribe`: 원본 자막, `translate`: 영어로 번역) |
| **`--whisper_model`** | 선택 | `base` | `tiny`, `base`, `small`, `medium`, `large` | **Whisper AI 모델 크기** (`tiny` 사용 시 속도가 3배 이상 빠름) |
| **`--num_highlights`**| 선택 | `3` | 숫자 | 추출할 하이라이트 쇼츠 동영상 개수 |
| **`--duration`** | 선택 | `30.0` | 초 단위 숫자 | 각 쇼츠 동영상 목표 길이(초) |
| **`--output_dir`** | 선택 | `output_shorts` | 폴더 경로 | 저장 폴더 경로 |

### 3. 웹 화면 UI 실행 (`app.py`)

```powershell
python app.py
```
실행 후 웹 브라우저에서 `http://127.0.0.1:7860` 에 접속하여 드래그 앤 드롭으로 영상을 올리고 언어 및 레이아웃 모드를 클릭 한 번으로 선택하여 제작할 수 있습니다.

---

## 📁 프로젝트 구조

```text
air/
├── main.py                    # CLI 메인 파이프라인 실행 파일
├── get_video.py               # 유튜브 URL 동영상 추출 & 연동 실행 파일
├── app.py                     # Gradio 웹 인터페이스 실행 파일
├── requirements.txt           # 패키지 의존성 목록
├── README.md                  # 프로젝트 종합 설명서
└── src/
    ├── __init__.py            # FFmpeg 바이너리 PATH 자동 등록
    ├── highlight_detector.py  # 음성 에너지 & 대화 밀도 기반 하이라이트 탐색
    ├── subtitle_generator.py # Whisper / SpeechRecognition 음성 인식 & 쇼츠 자막 오버레이
    └── video_processor.py    # MoviePy v1/v2 호환, 9:16 발언자 추적 & 비디오 렌더링
```

---

## 📚 사용된 라이브러리 요약

- **`yt-dlp`**: 유튜브 고화질 동영상/오디오 스트림 추출
- **`imageio-ffmpeg`**: 독립형 FFmpeg 바이너리 엔진 (시스템 PATH 무관)
- **`openai-whisper`**: OpenAI 음성 인식 & 단어 단위 타임스탬프 분석 AI
- **`SpeechRecognition`**: OS 보안 정책 우회용 Google STT 백업 엔진
- **`opencv-python`**: 인물 얼굴 인식 및 실시간 발언자 동적 카메라 추적
- **`moviepy`**: 9:16 비디오 변환, 이중 레이어 합성 및 MP4 인코딩
- **`Pillow` (`PIL`)**: 노란색 고대비 쇼츠 자막 드로잉 & 블러 효과
- **`numpy` / `scipy`**: 사운드 RMS 에너지 분석 및 이동 평균 스무딩
- **`gradio`**: 인터랙티브 웹 UI 프레임워크
