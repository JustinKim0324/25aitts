# pages/02_다국어_번역_TTS.py
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="🌐 다국어 TTS", page_icon="🔊")

# 🔑 OpenAI 초기화
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 🌍 지원 언어(이모지 · 표시명 · 번역·TTS 코드)
LANGS = {
    "🇺🇸 영어 (English)":   {"code": "en",   "flag": "🇺🇸"},
    "🇨🇳 중국어 (中文)":     {"code": "zh-CN","flag": "🇨🇳"},
    "🇯🇵 일본어 (日本語)":   {"code": "ja",   "flag": "🇯🇵"},
    "🇹🇭 태국어 (ภาษาไทย)": {"code": "th",   "flag": "🇹🇭"},
}

VOICES = ["shimmer", "alloy", "echo", "fable", "onyx", "nova"]

# ---------------- UI ---------------- #
st.title("🔊 한국어 → 다국어 번역 + 음성")

korean_text = st.text_area("✍️ **한국어 문장을 입력하세요**",
    placeholder="예) 안녕하세요, AI가 만들어 주는 멀티 TTS 데모입니다!")

st.markdown("🎯 **번역·TTS할 언어를 체크하세요**")
selected_langs = [name for name in LANGS if st.checkbox(name, value=False)]

voice = st.selectbox("🎤 **음성을 고르세요**", VOICES, index=0)

if st.button("🚀 번역 & 음성 생성") and korean_text.strip() and selected_langs:
    for lang_name in selected_langs:
        lang_info = LANGS[lang_name]
        flag = lang_info["flag"]
        lang_code = lang_info["code"]

        # 1️⃣ 번역
        with st.spinner(f"{flag} {lang_name.split()[0]} 번역 중…"):
            translated = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role":"system",
                     "content":f"Translate the user's Korean sentence into {lang_name.split()[0]} only."},
                    {"role":"user","content":korean_text},
                ],
            ).choices[0].message.content.strip()

        # 2️⃣ TTS
        with st.spinner(f"{flag} 음성 생성 중…"):
            speech = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=translated,
                response_format="mp3",
            )
            audio_bytes = speech.content

        # 3️⃣ 결과 표시 (텍스트 + 오디오)
        st.subheader(f"{flag} {lang_name}")
        st.markdown(f"**📝 번역:**  \n{translated}")
        st.audio(audio_bytes, format="audio/mpeg")
        st.divider()
else:
    st.caption("☝️ 한국어 문장과 언어를 선택한 뒤 **[🚀 번역 & 음성 생성]** 버튼을 눌러주세요.")
