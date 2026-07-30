# 🎬 AI 동영상 하이라이트 쇼츠(Shorts) 제작기

긴 동영상을 전달하면 **자동으로 중요 하이라이트 구간을 추출**하고, **9:16 비율(유튜브 쇼츠, 틱톡, 리일스 포맷) 화면 변환** 및 **쇼츠 스타일 자막**을 입혀 최종 수직 동영상을 생성해주는 파이썬 프로젝트입니다.

---

## 🌟 주요 기능

1. **AI 자동 하이라이트 구간 탐색 (`src/highlight_detector.py`)**
   - 오디오 RMS 음성 볼륨 피크(Energy Peak)와 Whisper 대화 밀도를 결합하여 시청자 흥미도가 높은 하이라이트 구간(기본 30초)을 자동 추출합니다.
2. **Whisper 기반 자동 음성 인식 & 쇼츠 자막 생성 (`src/subtitle_generator.py`)**
   - OpenAI의 Whisper 모델을 활용하여 음성을 한글/영문 텍스트로 인식합니다.
   - 쇼츠 특유의 가독성을 높이기 위해 1~4단어 단위로 텍스트를 나눈 뒤, 가독성이 뛰어난 노란색 고대비 테두리 자막을 생성합니다.
3. **9:16 쇼츠 비율 자동 레이아웃 변환 (`src/video_processor.py`)**
   - `blur_background` (추천): 배경을 유기적으로 흐리게 블러 처리하고 중앙에 영상 배치
   - `center_crop`: 9:16 중앙 화면 크롭
   - `fit_black`: 검은색 여백 탑재
4. **CLI 및 웹 GUI(Gradio) 인터페이스 모두 지원**

---

## 🛠️ 설치 방법

```bash
# 1. 패키지 설치
pip install -r requirements.txt
```

> **참고**: `imageio-ffmpeg` 및 Windows 기본 폰트(맑은 고딕)가 포함되어 있어 별도의 외부 프로그램 설치 없이 바로 실행 가능합니다.

---

## 🚀 사용 방법

### 1. 명령줄 실행 (CLI)

```bash
python main.py --video "sample.mp4" --num_highlights 3 --duration 30 --crop_mode blur_background
```

#### 옵션 설명:
- `--video`: 입력 동영상 파일 경로 (필수)
- `--output_dir`: 결과물이 저장될 폴더 (기본값: `output_shorts`)
- `--num_highlights`: 추출할 하이라이트 동영상 개수 (기본값: `3`)
- `--duration`: 하이라이트 각 영상의 목표 길이(초) (기본값: `30`)
- `--crop_mode`: 화면 9:16 변환 방식 (`blur_background`, `center_crop`, `fit_black`)
- `--whisper_model`: 자막 인식 모델 (`tiny`, `base`, `small`, `medium`, `large`)
- `--language`: 음성 언어 (`ko`, `en`, `auto`)

### 2. 웹 UI 실행 (Gradio Web App)

```bash
python app.py
```
실행 후 웹 브라우저에서 `http://127.0.0.1:7860` 에 접속하여 드래그 앤 드롭으로 동영상을 올려서 클릭 한 번으로 쇼츠를 제작할 수 있습니다.

---

## 📁 프로젝트 구조

```
air/
├── main.py                    # CLI 실행 메인 파일
├── app.py                     # Gradio 웹 인터페이스 실행 파일
├── requirements.txt           # 필요 라이브러리 목록
├── README.md                  # 프로젝트 설명서
└── src/
    ├── __init__.py
    ├── highlight_detector.py  # 음성 에너지 & 대화 밀도 하이라이트 탐색
    ├── subtitle_generator.py # Whisper 음성 인식 & 쇼츠 자막 오버레이 생성
    └── video_processor.py    # 9:16 비디오 렌더링 & 자막 합성
```
