import streamlit as st, base64, io, wave, time
from openai import OpenAI

st.set_page_config(page_title="🎙️ 실시간 STT (MediaRecorder)", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])
st.title("🎙️ 실시간 음성 인식 - MediaRecorder (지연≈1 s)")

# ─── JS 컴포넌트 (500 ms WebM 청크) ───
html_comp = """
<button id="rec">🎤 Start / Stop</button>
<script>
let rec=null, chunks=[];
document.getElementById("rec").onclick=async ()=>{
  if(rec && rec.state==="recording"){rec.stop(); return;}
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  rec=new MediaRecorder(stream,{mimeType:"audio/webm"});
  rec.ondataavailable=e=>{
    chunks.push(e.data);
    if(chunks.length>=2){       // ≈1 s
      const blob=new Blob(chunks,{type:"audio/webm"});
      chunks=[];
      const fr=new FileReader();
      fr.onload=()=>{window.parent.postMessage(fr.result,'*');};
      fr.readAsDataURL(blob);
    }
  };
  rec.start(500);
};
</script>
"""
st.components.v1.html(html_comp, height=80)

# ─── 메시지 수신 → Whisper 호출 ───
if "subs" not in st.session_state: st.session_state.subs=""
msg = st.experimental_get_query_params().get("streamlit_message")
# 위 방식 대신 postMessage → Streamlit 이벤트 처리용 JS <-> Py bridge 사용 시 @st.experimental_memo 로 변환 가능

st.subheader("자막")
st.markdown(st.session_state.subs or "🕒 대기 중…")

def handle_js_msg():
    import json, re
    raw = st.experimental_get_query_params().get("streamlit_message")
    if not raw: return
    m = re.match(r"data:audio\\/webm;base64,(.*)", raw)
    if not m: return
    wav = webm_to_wav(base64.b64decode(m.group(1)))   # ffmpeg-python 또는 av 사용
    txt = client.audio.transcriptions.create(
        model="whisper-1",
        file=io.BytesIO(wav),
        language="ko",
        response_format="text",
    ).strip()
    st.session_state.subs += " " + txt
    st.experimental_set_query_params(streamlit_message="")  # 메시지 소비

handle_js_msg()
