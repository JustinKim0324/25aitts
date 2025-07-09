# pages/05_STT_debug.py
import streamlit as st, av, queue, time, wave, io, tempfile, threading
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from openai import OpenAI

st.set_page_config(page_title="STT DEBUG", page_icon="🔧")
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("🔧 Whisper-1 배치-STT 디버그 (1 초 주기)")

# 1. 오디오 캡처 & 16 kHz mono 변환
class AudioProc(AudioProcessorBase):
    def __init__(self):
        self.q = queue.Queue()
    def recv_audio(self, frame: av.AudioFrame):
        pcm16 = frame.reformat(format="s16", layout="mono", rate=16_000)
        self.q.put(pcm16.planes[0].to_bytes())
        return frame

ctx = webrtc_streamer(
    key="stt-debug",
    audio_processor_factory=AudioProc,
    media_stream_constraints={"audio": True, "video": False},
)

# 2. 1 초 버퍼 → Whisper-1  (Thread)
def stt_worker(q: queue.Queue, placeholder):
    buf = b""; last = 0
    while True:
        try:
            buf += q.get(timeout=0.1)
        except queue.Empty:
            pass
        # 32 000 byte ≈ 1 s @16 kHz mono 16-bit
        if len(buf) >= 32_000 and time.time() - last > 0.8:
            wav_bytes = io.BytesIO()
            with wave.open(wav_bytes, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16_000)
                wf.writeframes(buf)
            wav_bytes.seek(0)
            txt = client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_bytes,
                response_format="text",
                language="ko",
            ).strip()
            placeholder.markdown(f"📝 **{txt}**")
            st.sidebar.write(f"Chunk OK · {len(buf)} bytes")   # 실시간 로그
            buf = b""; last = time.time()

if ctx and ctx.state.playing:
    placeholder = st.empty()
    if "dbg_thread" not in st.session_state:
        st.session_state.dbg_thread = threading.Thread(
            target=stt_worker, args=(ctx.audio_processor.q, placeholder), daemon=True
        ).start()
    st.info("🎤 말하면 1 초 뒤 자막이 뜹니다 (Logs 탭에서 바이트 수 / API 호출 확인)")
else:
    st.warning("Start 버튼을 눌러 마이크 스트림을 켜 주세요.")
