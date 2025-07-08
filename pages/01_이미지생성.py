# pages/03_텍스트_→_AI_이미지.py
import streamlit as st
from openai import OpenAI
import requests, zipfile, io

st.set_page_config(page_title="🖼️ AI 이미지 생성", page_icon="🖼️")

# 🔑 OpenAI
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ---------- UI ---------- #
st.title("🖼️ 한국어 텍스트 → AI 이미지")

korean_prompt = st.text_area(
    "🎨 **그리고 싶은 장면을 한국어로 묘사해 주세요!**",
    placeholder="예) 햇살 속 자전거를 타는 어린이, 따뜻한 파스텔 수채화 스타일",
    height=120,
)

col1, col2 = st.columns(2)
with col1:
    num_images = st.selectbox("🖼️ 이미지 개수", [1, 2, 3, 4], index=0)
with col2:
    size = st.selectbox("📐 해상도", ["1024x1024", "1024x1792", "1792x1024"], index=0)

# ---------- 실행 ---------- #
if st.button("🚀 이미지 생성") and korean_prompt.strip():
    # 1️⃣ GPT-4o가 영문 프롬프트 생성
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

    # 2️⃣ GPT-4o가 한국어 제목(20자 이내) 생성
    title = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "사용자 입력을 보고 어울리는 한국어 제목을 20자 이내로 지어 줘."},
            {"role": "user", "content": korean_prompt},
        ],
    ).choices[0].message.content.strip()

    st.markdown("✏️ **영문 프롬프트**")
    st.code(eng_prompt, language="markdown")

    # 3️⃣ 이미지 n장 순차 생성 + 즉시 표출
    zip_items = []                 # (filename, bytes) 튜플 모으기
    for idx in range(1, num_images + 1):
        with st.spinner(f"🎨 이미지 {idx}/{num_images} 생성 중…"):
            resp = client.images.generate(
                model="dall-e-3",
                prompt=eng_prompt,
                n=1,               # 必: DALL·E-3 는 n=1만 지원
                size=size,
                quality="standard",
            )
            url  = resp.data[0].url
            data = requests.get(url).content   # 다운로드해 ZIP에 넣을 바이트

        # 화면에 바로 추가
        st.image(url, caption=f"{title}", use_container_width=True)
        st.download_button(
            f"💾 이미지 {idx} 저장",
            data,
            file_name=f"ai_image_{idx}.png",
            mime="image/png",
        )
        st.divider()

        zip_items.append((f"ai_image_{idx}.png", data))

    # 4️⃣ 모든 이미지 ZIP 한꺼번에 다운로드
    if len(zip_items) > 1:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for fname, blob in zip_items:
                zf.writestr(fname, blob)
        zip_buf.seek(0)
        st.download_button(
            "📦 모든 이미지 ZIP 다운로드",
            zip_buf,
            file_name="ai_images.zip",
            mime="application/zip",
        )

else:
    st.caption("☝️ 먼저 장면을 입력하고 **[🚀 이미지 생성]** 버튼을 눌러 보세요.")
