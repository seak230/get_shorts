import os
import gradio as gr
from main import process_video_to_shorts

def gradio_interface(
    video_file,
    num_highlights,
    target_duration,
    crop_mode,
    whisper_model,
    language,
    task
):
    if video_file is None:
        return "동영상 파일을 업로드해주세요.", []

    output_dir = "output_shorts_gradio"
    try:
        generated_files = process_video_to_shorts(
            video_path=video_file,
            output_dir=output_dir,
            num_highlights=num_highlights,
            target_duration=target_duration,
            crop_mode=crop_mode,
            whisper_model=whisper_model,
            language=language,
            task=task
        )
        return f"✅ 성공적으로 {len(generated_files)}개의 쇼츠 동영상을 생성했습니다!", generated_files
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}", []

def launch_app():
    with gr.Blocks(title="AI 동영상 하이라이트 쇼츠 제작기") as demo:
        gr.Markdown(
            """
            # 🎬 AI 동영상 하이라이트 쇼츠(Shorts) 제작기
            긴 동영상을 입력하면 **자동으로 하이라이트 구간을 추출**하고, **9:16 비율 화면 변환**과 **자막(Captions)**을 입혀 쇼츠 동영상을 생성합니다.
            """
        )
        with gr.Row():
            with gr.Column():
                video_input = gr.Video(label="동영상 업로드")
                num_highlights = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="추출할 하이라이트 개수")
                target_duration = gr.Slider(minimum=10, maximum=60, value=30, step=5, label="하이라이트 구간 길이 (초)")
                crop_mode = gr.Dropdown(
                    choices=[("🎬 실시간 발언자 동적 추적 스위칭 (추천)", "speaker_tracking"), ("👤 대표 얼굴 고정 꽉 채우기", "smart_face"), ("블러 배경", "blur_background"), ("화면 꽉 채우기 (단순 중앙)", "fill_screen"), ("검은색 여백", "fit_black")],
                    value="speaker_tracking",
                    label="9:16 비디오 화면 레이아웃"
                )



                whisper_model = gr.Dropdown(
                    choices=["tiny", "base", "small", "medium", "large"],
                    value="base",
                    label="Whisper 자막 인식 모델 크기"
                )
                language = gr.Dropdown(
                    choices=[("한국어 (Korean)", "ko"), ("영어 (English)", "en"), ("자동 감지 (Auto)", "auto")],
                    value="ko",
                    label="🌐 자막 생성 언어 선택"
                )
                task = gr.Dropdown(
                    choices=[("원본 언어로 자막 생성", "transcribe"), ("영어로 번역 자막 생성", "translate")],
                    value="transcribe",
                    label="📝 자막 모드 선택"
                )
                submit_btn = gr.Button("🚀 쇼츠 자동 제작 시작", variant="primary")

            with gr.Column():
                status_output = gr.Textbox(label="진행 상태", interactive=False)
                gallery_output = gr.Gallery(label="생성된 쇼츠 동영상 결과물", columns=2, height="auto")

        submit_btn.click(
            fn=gradio_interface,
            inputs=[video_input, num_highlights, target_duration, crop_mode, whisper_model, language, task],
            outputs=[status_output, gallery_output]
        )

    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)


if __name__ == "__main__":
    launch_app()
