import streamlit as st, queue, time, io, wave
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
from openai import OpenAI
import av

st.set_page_config(page_title="🎙️ 실시간 STT (WebRTC)", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])
st.title("🎙️ 실시간 음성 인식 - WebRTC (지연≈0.8 s)")

# ─── 1) 오디오 캡처 & 16 kHz 변환 ───
class AudioProc(AudioProcessorBase):
    def __init__(self):
        self.buf = bytearray()
        self.last = 0
        self.ph = st.empty()

    def recv_audio(self, frame: av.AudioFrame):
        pcm = frame.reformat(format="s16", layout="mono", rate=16_000)
        self.buf += pcm.planes[0].to_bytes()

        # 1 s(32 kB) 단위로 Whisper 호출
        if len(self.buf) >= 32_000 and time.time() - self.last > .7:
            wav = io.BytesIO()
            with wave.open(wav, "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16_000)
                wf.writeframes(self.buf[:32_000])
            wav.seek(0)
            txt = client.audio.transcriptions.create(
                model="whisper-1",
                file=wav,
                language="ko",
                response_format="text",
                temperature=0
            ).strip()
            self.ph.markdown(f"📝 **{txt}**")
            self.buf.clear(); self.last = time.time()
        return frame

# ─── 2) WebRTC 스트림 (TURN 포함) ───
webrtc_streamer(
    key="stt-webrtc",
    audio_processor_factory=AudioProc,
    media_stream_constraints={"audio": True, "video": False},
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["turn:openrelay.metered.ca:80?transport=tcp"],
             "username": "openrelayproject", "credential": "openrelayproject"}
        ]
    },
    async_processing=True,
)

st.caption("Start 를 눌러 마이크 권한을 허용하면 1 초 내외로 자막이 표시됩니다.")
