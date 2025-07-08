# pages/03_텍스트_→_AI_이미지.py
"""
🖼️ 텍스트 기반 AI 이미지 생성 데모
--------------------------------
1) 한국어로 주제·상황·스타일을 자유롭게 적는다.
2) [이미지 생성] 버튼을 누르면
   ─ OpenAI GPT-4o가 영문 프롬프트(상세 설명) 자동 작성
   ─ DALL·E-3 모델이 1024×1024 PNG 이미지를 만든다.
"""

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="🖼️ AI 이미지 생성", page_icon="🖼️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ---------- UI ---------- #
st.title("🖼️ 한국어 텍스트 → AI 이미지")
korean_prompt = st.text_area(
    "🎨 **그리고 싶은 장면을 한국어로 묘사해 보세요!**",
    placeholder="예) 봄바람에 벚꽃잎이 흩날리는 한강 공원, 따뜻한 색감의 수채화 스타일",
    height=120,
)

col1, col2 = st.columns(2)
with col1:
    num_images = st.selectbox("🖼️ 이미지 개수", [1, 2, 3, 4], index=0)
with col2:
    size = st.selectbox("📐 해상도", ["1024x1024", "1024x1792", "1792x1024"], index=0)

generate_btn = st.button("🚀 이미지 생성")

# ---------- 로직 ---------- #
if generate_btn and korean_prompt.strip():
    # 1️⃣ 한글 → 영어 프롬프트 변환 (짧고 묘사 위주)
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

    # 2️⃣ 이미지 생성
    with st.spinner("🎨 DALL·E-3로 이미지 그리는 중… 잠시만요!"):
        img_resp = client.images.generate(
            model="dall-e-3",
            prompt=eng_prompt,
            n=num_images,
            size=size,
            quality="standard",   # 'hd' 도 가능(비용 ↑)
        )

    st.success("✅ 이미지 완성!")

    # 결과 표시
    for i, d in enumerate(img_resp.data, start=1):
        st.image(d.url, caption=f"결과 {i}", use_column_width=True)
        # 다운로드 버튼
        st.download_button(
            f"💾 결과 {i} 다운로드",
            data=d.url,   # Streamlit이 내부적으로 remote 이미지 → bytes 변환
            file_name=f"ai_image_{i}.png",
            mime="image/png",
        )

else:
    st.caption("☝️ 먼저 장면을 입력하고 **[🚀 이미지 생성]** 버튼을 눌러 보세요.")
