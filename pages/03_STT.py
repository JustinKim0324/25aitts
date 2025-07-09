import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from openai import OpenAI
import av, asyncio, queue

st.set_page_config(page_title="🎙️ 실시간 STT 데모", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("🎙️ 실시간 음성 인식 (한국어 ▶ 텍스트)")

# ── ① 프론트엔드 오디오 캡처 & 전송 ────────────────────────── #
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.q = queue.Queue()

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().tobytes()            # 16-bit PCM little-endian
        self.q.put(pcm)                               # 청크를 내부 큐로 전달
        return frame

processor = webrtc_streamer(
    key="stt-demo",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# ── ② 백엔드: 큐에 쌓인 바이트 → OpenAI STT 스트림 호출 ─────── #
if processor and processor.state.playing:

    # 스트리밍 STT 코루틴 한 번만 실행
    if "stt_task" not in st.session_state:
        async def transcribe_loop(audio_q: queue.Queue):
            st_placeholder = st.empty()
            aggregator = b""

            async with client.audio.transcriptions.with_stream(
                model="gpt-4o-transcribe",
                response_format="text",
                language="ko"
            ) as streamer:
                while True:
                    # 0.1초마다 큐에서 청크 수거
                    try:
                        chunk = audio_q.get(timeout=0.1)
                        aggregator += chunk
                        # 8000 bytes ≈ 0.25 s @16 kHz 16-bit 1-ch → 전송
                        if len(aggregator) > 8000:
                            await streamer.send_chunk(aggregator)
                            aggregator = b""
                    except queue.Empty:
                        pass

                    # API 측에서 도착한 자막 스트림 표시
                    async for text in streamer.iter_text(timeout=0):
                        st_placeholder.markdown(f"📝 **{text.strip()}**")

        st.session_state.stt_task = asyncio.create_task(
            transcribe_loop(processor.audio_processor.q)
        )

    st.info("🎤 마이크가 켜졌습니다. 말을 하면 위에 자막이 실시간으로 뜹니다.")
else:
    st.warning("▶️ 상단의 **Start** 버튼을 눌러 마이크 스트림을 켜 주세요.")
