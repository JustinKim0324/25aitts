import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="번역+TTS 데모", page_icon="🔊")

client = OpenAI(api_key=st.secrets["openai_api_key"])

LANG_OPTIONS = {
    "영어 (English)": "en",
    "중국어 (中文)": "zh-CN",
    "일본어 (日本語)": "ja",
    "태국어 (ภาษาไทย)": "th",
}

st.title("🔊 한국어 문장을 번역해서 음성으로 듣기")

korean_text = st.text_area("① 한국어 문장을 입력하세요",
                           placeholder="예) 안녕하세요, 좋은 하루 되세요!")
target_lang_name = st.selectbox("② 번역 언어 선택",
                                list(LANG_OPTIONS.keys()), index=0)
voice = st.selectbox("③ 음성 선택",
                     ["shimmer", "alloy", "echo", "fable", "onyx", "nova"],
                     index=0)

if st.button("④ 번역 + 음성 생성 🔄🔈") and korean_text.strip():
    # 1) 번역
    with st.spinner("번역 중…"):
        translated = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": f"Translate the user's Korean sentence into "
                            f"{target_lang_name.split()[0]} only."},
                {"role": "user", "content": korean_text},
            ],
        ).choices[0].message.content.strip()
    st.success("✅ 번역 완료")
    st.markdown(f"**번역 결과:**  \n{translated}")

    # 2) TTS
    with st.spinner("TTS 생성 중…"):
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=translated,
            response_format="mp3",   # ← 수정된 부분
        )
        audio_bytes = response.content      # SDK가 바로 bytes 반환

    st.audio(audio_bytes, format="audio/mp3")
