import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="🎙️ STT → 번역 → TTS", page_icon="🎙️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ────────── UI ──────────
st.title("🎙️ 오디오 파일을 텍스트로 변환하고 원하는 언어로 읽어주기")

uploaded = st.file_uploader(
    "① 음성 파일 업로드 (mp3, wav, m4a, webm; 최대 25 MB)",
    type=["mp3", "wav", "m4a", "webm"]
)

langs = {
    "영어 (en)"  : "en",
    "중국어 (zh)": "zh-CN",
    "일본어 (ja)": "ja",
    "한국어 (ko)": "ko",
    "스페인어 (es)": "es",
}
target_lang_name = st.selectbox("② 번역 & 낭독할 언어 선택", list(langs.keys()), 0)
voice = st.selectbox("③ 낭독 음성", ["shimmer", "alloy", "echo", "fable", "onyx", "nova"], 0)

if st.button("🚀 STT → 번역 → TTS") and uploaded:
    # 1️⃣ STT (Whisper / gpt-4o-transcribe)
    with st.spinner("📝 음성을 텍스트로 변환 중…"):
        stt_resp = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",     # whisper-1 도 가능
            file=uploaded.read(),          # BytesIO
            response_format="text",        # 순수 텍스트
            temperature=0                  # 정확도 우선
        )
        korean_text = stt_resp.text.strip()
    st.success("✅ STT 완료")
    st.markdown(f"**원본(STT):** {korean_text}")

    # 2️⃣ 번역 (한국어 → target_lang)
    with st.spinner("🌐 번역 중…"):
        translated = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": f"Translate the user's Korean text to {target_lang_name.split()[0]} only."},
                {"role": "user", "content": korean_text}
            ],
        ).choices[0].message.content.strip()
    st.markdown(f"**번역 결과:** {translated}")

    # 3️⃣ TTS
    with st.spinner("🔈 TTS 생성 중…"):
        speech = client.audio.speech.create(
            model="tts-1",                 # 고음질은 tts-1-hd
            voice=voice,
            input=translated,
            response_format="mp3"
        )
        audio_bytes = speech.content
    st.audio(audio_bytes, format="audio/mpeg")

    # 다운로드
    st.download_button(
        "💾 MP3 다운로드", audio_bytes,
        file_name="translated_speech.mp3", mime="audio/mpeg"
    )
else:
    st.caption("☝️ 음성 파일을 올리고 버튼을 눌러 보세요!")
