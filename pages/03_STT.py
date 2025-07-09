# ↑ 파일 첫머리: 추가 import
import threading, asyncio, queue, av
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from openai import OpenAI
import streamlit as st

# ---------- OpenAI & Streamlit 기본 설정 ----------
st.set_page_config(page_title="🎙️ 실시간 STT", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])
st.title("🎙️ 실시간 음성 인식 (한국어)")

# ---------- 1) 오디오 프로세서 ----------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.q = queue.Queue()

    def recv_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        mono16 = frame.reformat(format="s16", layout="mono", rate=16000)
        self.q.put(mono16.planes[0].to_bytes())
        return frame


processor = webrtc_streamer(
    key="stt-demo",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

# ---------- 2) 백그라운드 event-loop (한 번만 생성) ----------
if "bg_loop" not in st.session_state:
    st.session_state.bg_loop = asyncio.new_event_loop()
    threading.Thread(
        target=st.session_state.bg_loop.run_forever,
        daemon=True
    ).start()

# ---------- 3) STT 스트리밍 코루틴 ----------
async def transcribe_loop(audio_q: queue.Queue):
    st_placeholder = st.empty()
    aggregator = b""
    async with client.audio.transcriptions.with_stream(
        model="gpt-4o-transcribe",
        response_format="text",
        language="ko"
    ) as streamer:
        while True:
            try:
                chunk = audio_q.get(timeout=0.1)
                aggregator += chunk
                # 0.25 초 이상 모으면 전송
                if len(aggregator) > 8000:
                    await streamer.send_chunk(aggregator)
                    aggregator = b""
            except queue.Empty:
                pass
            async for text in streamer.iter_text(timeout=0):
                st_placeholder.markdown(f"📝 **{text.strip()}**")

# ---------- 4) 마이크 켜지면 코루틴 등록 ----------
if processor and processor.state.playing:
    if "stt_future" not in st.session_state:
        st.session_state.stt_future = asyncio.run_coroutine_threadsafe(
            transcribe_loop(processor.audio_processor.q),
            st.session_state.bg_loop
        )
    st.info("🎤 마이크가 켜졌습니다. 말을 하면 자막이 실시간으로 나타납니다.")
else:
    st.warning("▶️ 상단의 **Start** 버튼을 눌러 마이크 스트림을 켜 주세요.")
