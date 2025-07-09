import streamlit as st, base64, io, wave, ffmpeg, uuid
from openai import OpenAI

st.set_page_config(page_title="🎙️ STT · MediaRecorder", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])
st.title("🎙️ 실시간 음성 인식 (TURN 불필요)")

# ---------- 1) 브라우저 측 녹음 버튼 ---------- #
rec_key = f"rec-{uuid.uuid4()}"       # 세션마다 고유키
st.components.v1.html(
    f"""
<button id="rec">🎤 Start / Stop</button>
<script>
let rec=null,ch=[];
document.getElementById("rec").onclick=async () => {{
  if(rec && rec.state==="recording"){{rec.stop();return;}}
  const s=await navigator.mediaDevices.getUserMedia({{audio:true}});
  rec=new MediaRecorder(s,{{mimeType:"audio/webm"}});
  rec.ondataavailable=e=>{{ch.push(e.data);
    if(ch.length>=2){{
      const blob=new Blob(ch,{{type:"audio/webm"}}); ch=[];
      blob.arrayBuffer().then(buf=>{{
        const b64=btoa(String.fromCharCode(...new Uint8Array(buf)));
        fetch("/",{{method:"POST",
          headers:{{"x-streamlit-message":"{rec_key}", "Content-Type":"text/plain"}},
          body:b64}});
      }});
    }}
  }};
  rec.start(500);
}};
</script>
""",
    height=70,
)

# ---------- 2) POST 요청 수신 → Whisper ---------- #
if "headers" in st.session_state and st.session_state.headers.get("x-streamlit-message") == rec_key:
    b64 = st.session_state["body"]
    raw = base64.b64decode(b64)                 # webm bytes

    # webm → wav (16 kHz mono) 변환
    wav, _ = (
        ffmpeg
        .input("pipe:0")
        .output("pipe:1", format="wav", ac=1, ar="16k")
        .run(input=raw, capture_stdout=True, quiet=True)
    )

    # Whisper-1 STT
    text = client.audio.transcriptions.create(
        model="whisper-1",
        file=io.BytesIO(wav),
        language="ko",
        response_format="text"
    ).strip()

    # 화면 업데이트 (세션 상태 누적)
    st.session_state.setdefault("subs", "")
    st.session_state.subs += " " + text
    st.stop()                                  # 즉시 응답 끝

st.subheader("자막")                            # 최초 화면
st.markdown(st.session_state.get("subs", "🕒 대기 중…"))
