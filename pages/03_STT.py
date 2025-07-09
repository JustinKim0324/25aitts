import streamlit as st, base64, io, ffmpeg
from openai import OpenAI

st.set_page_config(page_title="🎙️ STT (TURN 無)", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])
st.title("🎙️ 실시간 음성 인식 (지연≈1 s)")

# ─────────────────── 1) JS 녹음 버튼 ─────────────────── #
b64_chunk = st.components.v1.html(
    """
<button id="rec">🎤 Start / Stop</button>
<script>
let rec=null, chunks=[];
document.getElementById("rec").onclick=async()=>{
  if(rec && rec.state==="recording"){rec.stop();return;}
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  rec=new MediaRecorder(stream,{mimeType:"audio/webm"});
  rec.ondataavailable=e=>{
    chunks.push(e.data);
    if(chunks.length>=2){                      // ≈1 s
      const blob=new Blob(chunks,{type:"audio/webm"}); chunks=[];
      const fr=new FileReader();
      fr.onload=()=>Streamlit.setComponentValue(fr.result.split(',')[1]);
      fr.readAsDataURL(blob);
    }
  };
  rec.start(500);                             // 0.5 s 청크
};
</script>
""",
    height=70,
)

# ─────────────────── 2) Python: base64 → Whisper ─────────────────── #
if b64_chunk:
    # 타입 보정
    if isinstance(b64_chunk, list):
        b64_chunk = b64_chunk[0]
    elif isinstance(b64_chunk, dict):
        b64_chunk = b64_chunk.get("data", "")
    if not isinstance(b64_chunk, str):
        st.error("base64 문자열이 아닙니다."); st.stop()

    # base64 → webm bytes
    try:
        webm_bytes = base64.b64decode(b64_chunk)
    except Exception as e:
        st.error(f"base64 디코딩 실패: {e}"); st.stop()

    # webm → wav(16kHz mono)
    wav_bytes, _ = (
        ffmpeg
        .input("pipe:0")
        .output("pipe:1", format="wav", ac=1, ar="16k")
        .run(input=webm_bytes, capture_stdout=True, quiet=True)
    )

    # Whisper-1 STT
    text = client.audio.transcriptions.create(
        model="whisper-1",
        file=io.BytesIO(wav_bytes),
        language="ko",
        response_format="text",
        temperature=0,
    ).strip()

    st.session_state.setdefault("subs", "")
    st.session_state["subs"] += " " + text

# ─────────────────── 3) 자막 출력 ─────────────────── #
st.subheader("자막")
st.markdown(st.session_state.get("subs", "🕒 대기 중…"))
