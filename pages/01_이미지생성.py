# pages/03_텍스트_→_AI_이미지.py  (수정판)
import streamlit as st
from openai import OpenAI
from itertools import repeat

st.set_page_config(page_title="🖼️ AI 이미지 생성", page_icon="🖼️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("🖼️ 한국어 텍스트 → AI 이미지")

korean_prompt = st.text_area(
    "🎨 **그리고 싶은 장면을 한국어로 묘사해 주세요**",
    placeholder="예) 봄바람에 벚꽃잎이 흩날리는 한강 공원, 따뜻한 색감의 수채화 스타일",
    height=120,
)

col1, col2 = st.columns(2)
with col1:
    num_images = st.selectbox("🖼️ 이미지 개수", [1, 2, 3, 4], index=0)
with col2:
    size = st.selectbox("📐 해상도", ["1024x1024", "1024x1792", "1792x1024"], index=0)

if st.button("🚀 이미지 생성") and korean_prompt.strip():
    # 1️⃣ 한국어 → 영문 프롬프트
    with st.spinner("💬 프롬프트 작성 중…"):
        eng_prompt = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": ("You are a prompt engineer for DALL·E. "
                             "Rewrite the user's Korean description as an English prompt "
                             "of max 60 words, vivid and specific, no extra text.")},
                {"role": "user", "content": korean_prompt},
            ],
        ).choices[0].message.content.strip()

    st.markdown("✏️ **영문 프롬프트**")
    st.code(eng_prompt, language="markdown")

    # 2️⃣ 이미지 생성 (DALL·E 3 → 1장씩 요청)
    st.spinner("🎨 DALL·E-3로 이미지 그리는 중…")
    urls = []
    for _ in repeat(None, num_images):
        resp = client.images.generate(
            model="dall-e-3",
            prompt=eng_prompt,
            n=1,                 # ← 반드시 1
            size=size,
            quality="standard",
        )
        urls.append(resp.data[0].url)
    st.success("✅ 이미지 완성!")

    # 3️⃣ 결과 표시
    for i, url in enumerate(urls, 1):
        st.image(url, caption=f"결과 {i}", use_column_width=True)
        st.download_button(f"💾 결과 {i} 다운로드", url, file_name=f"ai_image_{i}.png", mime="image/png")
else:
    st.caption("☝️ 장면을 입력하고 **[🚀 이미지 생성]** 을 눌러 보세요.")
