import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="번역+TTS", page_icon="🔊")
client = OpenAI(api_key=st.secrets["openai_api_key"])

langs = {"영어": "en", "중국어": "zh-CN", "일본어": "ja", "태국어": "th"}

txt   = st.text_area("한국어 문장 입력")
lang  = st.selectbox("번역 언어", list(langs.keys()))
voice = st.selectbox("음성", ["shimmer","alloy","echo","fable","onyx","nova"])

if st.button("번역+TTS"):
    # 1) 번역
    translated = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system",
             "content":f"Translate to {lang} only."},
            {"role":"user","content":txt},
        ]
    ).choices[0].message.content.strip()
    st.write("**번역 결과**:", translated)

    # 2) TTS
    speech = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=translated,
        response_format="mp3"        # OK: 서버 → MP3 바이트
    )
    audio_bytes = speech.content

    # 3) 재생 (← 여기 MIME 타입 중요!)
    st.audio(audio_bytes, format="audio/mpeg")
