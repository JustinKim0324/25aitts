import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import numpy as np
import whisper
import io
from pydub import AudioSegment
import os
import tempfile

# Whisper 모델 로드 (앱 시작 시 한 번만 로드하도록 캐싱)
@st.cache_resource
def load_model():
    # 모델 크기는 "tiny", "base", "small", "medium", "large" 중에서 선택 가능합니다.
    # "base" 모델이 속도와 정확도 면에서 적절한 시작점입니다.
    model = whisper.load_model("base")
    return model

model = load_model()

st.title("🎤 실시간 음성-텍스트 변환 앱")
st.write("아래 'START' 버튼을 누르고 마이크에 말하면 실시간으로 텍스트가 변환됩니다.")

# webrtc 스트리밍을 위한 오디오 처리 클래스
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = io.BytesIO()

    # webrtc로부터 오디오 프레임을 받습니다.
    def recv(self, frame):
        # pydub에서 처리할 수 있도록 numpy 배열을 AudioSegment로 변환
        sound = AudioSegment(
            data=frame.to_ndarray().tobytes(),
            sample_width=frame.format.bytes,
            frame_rate=frame.sample_rate,
            channels=len(frame.layout.channels),
        )
        # 받은 오디오 데이터를 버퍼에 누적
        self.audio_buffer.write(sound.raw_data)
        
        return frame

# webrtc_streamer 컴포넌트 설정
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY, # 마이크 입력만 받음
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"video": False, "audio": True},
)

# 텍스트 변환 결과를 표시할 영역
result_container = st.empty()
result_container.write("음성 인식 대기 중...")

if webrtc_ctx.audio_processor:
    st.write("마이크가 연결되었습니다. 이제 말씀하세요!")

    if st.button("지금까지의 음성을 텍스트로 변환"):
        # 오디오 버퍼에 데이터가 있는지 확인
        if webrtc_ctx.audio_processor.audio_buffer.getbuffer().nbytes > 0:
            with st.spinner("음성을 텍스트로 변환 중입니다..."):
                # 버퍼의 시작으로 이동
                webrtc_ctx.audio_processor.audio_buffer.seek(0)
                
                # pydub를 사용하여 버퍼에서 오디오 데이터 로드
                # webrtc에서 받은 raw 오디오 데이터이므로, 포맷 정보를 명시해줘야 합니다.
                audio_segment = AudioSegment.from_raw(
                    webrtc_ctx.audio_processor.audio_buffer,
                    sample_width=2, # 16-bit
                    frame_rate=48000, # webrtc의 기본 샘플링 레이트
                    channels=1
                )

                # Whisper가 처리할 수 있도록 임시 파일로 저장 (mp3 포맷 권장)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    audio_segment.export(tmp.name, format="mp3")
                    tmp_path = tmp.name

                # Whisper로 음성 인식
                result = model.transcribe(tmp_path, fp16=False)
                
                # 변환 결과 출력
                result_container.markdown(f"**변환 결과:**\n> {result['text']}")

                # 임시 파일 삭제
                os.remove(tmp_path)
        else:
            result_container.write("녹음된 음성이 없습니다. 먼저 마이크에 말씀하세요.")
else:
    st.write("START 버튼을 눌러 마이크 사용을 허용해주세요.")
