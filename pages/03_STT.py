import streamlit as st, base64, io, wave, ffmpeg
from openai import OpenAI

st.set_page_config(page_title="🎙️ 실시간 STT (TURN 불필요)", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("🎙️ 실시간 음성 인식 (TURN 불필요 · 지연≈1 s)")

# ───────────────────── 1) 브라우저 녹음 + Base64 전송 ───────────────────── #
b64_chunk = st.components.v1.html(
    """
<button id="rec">🎤 Start / Stop</button>
<script>
let rec=null, chunks=[];
document.getElementById("rec").onclick = async () => {
  if(rec && rec.state==="recording"){ rec.stop(); return; }           // STOP
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  rec = new MediaRecorder(stream, {mimeType:"audio/webm"});
  rec.ondataavailable = e => {
      chunks.push(e.data);
      if(chunks.length >= 2){                                         // ≈1 s
          const blob = new Blob(chunks, {type:"audio/webm"});
          chunks = [];
          const fr = new FileReader();
          fr.onload = () => {
              const b64 = fr.result.split(',')[1];                    // data:…;base64,
              Streamlit.setComponentValue(b64);                       // 🔑 Python으로 전달
          };
          fr.readAsDataURL(blob);
      }
  };
  rec.start(500);                                                     // 0.5 s 청크
};
</script>
""",
    height=70,
)

# ───────────────────── 2) Python — Base64 → Whisper ───────────────────── #
if b64_chunk:                                         # 값이 들어오면
    # WebM ▶︎ WAV(16 kHz mono) 변환
    webm_bytes = base64.b64decode(b64_chunk)
    wav_bytes, _ = (
        ffmpeg
        .input("pipe:0")
        .output("pipe:1", format="wav", ac=1, ar="16k")
        .run(input=webm_bytes, capture_stdout=True, quiet=True)
    )
    # Whisper STT
    text = client.audio.transcriptions.create(
        model="whisper-1",
        file=io.BytesIO(wav_bytes),
        language="ko",
        response_format="text",
        temperature=0,
    ).strip()

    # 자막 세션 상태 누적
    st.session_state.setdefault("subs", "")
    st.session_state["subs"] += " " + text

# ───────────────────── 3) 자막 출력 ───────────────────── #
st.subheader("자막")
st.markdown(st.session_state.get("subs", "🕒 대기 중…"))
