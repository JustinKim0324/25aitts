import streamlit as st
from openai import OpenAI
from io import BytesIO

# ---------- 기본 설정 ---------- #
st.set_page_config(page_title="한국어 → 다국어 번역 + OpenAI TTS", page_icon="🔊")
client = OpenAI(api_key=st.secrets["openai_api_key"])

LANG_OPTIONS = {
    "영어 (English)": "en",
    "중국어 (中文)": "zh-CN",
    "일본어 (日本語)": "ja",
    "태국어 (ภาษาไทย)": "th",
}

VOICE_DEFAULT = "shimmer"   # 사용자가 원하면 다른 음성으로 놔둘 수 있어요

# ---------- UI ---------- #
st.title("🔊 한국어 문장을 번역해서 음성으로 들어보세요")

korean_text = st.text_area(
    "① 한국어 문장을 입력하세요",
    placeholder="예) 안녕하세요, 좋은 하루 되세요!"
)
target_lang_name = st.selectbox("② 번역할 언어를 고르세요", list(LANG_OPTIONS.keys()), index=0)
voice = st.selectbox(
    "③ 음성을 선택하세요 (샘플: alloy · echo · fable · onyx · nova · shimmer)",
    options=["shimmer", "alloy", "echo", "fable", "onyx", "nova"],
    index=0,
)
if st.button("④ 번역 + TTS 실행 🔄🔈") and korean_text.strip():

    # ---------- 1단계: 번역 ---------- #
    with st.spinner("번역 중…"):
        translated = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate to {target_lang_name.split()[0]} only."
                },
                {"role": "user", "content": korean_text},
            ],
        ).choices[0].message.content.strip()

    st.success("✅ 번역 완료")
    st.markdown(f"**번역 결과:**  \n{translated}")

    # ---------- 2단계: TTS ---------- #
    with st.spinner("TTS 생성 중…"):
        response = client.audio.speech.create(
            model="tts-1",            # 실시간/저지연용; 품질 우선이면 "tts-1-hd"
            voice=voice,              # 사용자가 고른 음성
            input=translated,
            format="mp3"              # wav, flac 등도 가능
        )
        audio_bytes = response.read()   # SDK가 반환하는 BinaryIO 객체에서 바로 바이트 추출
        audio_buffer = BytesIO(audio_bytes)

    st.audio(audio_buffer, format="audio/mp3")
