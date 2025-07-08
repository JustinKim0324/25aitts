# pages/03_텍스트_→_AI_이미지.py
import streamlit as st
from openai import OpenAI
from itertools import repeat

st.set_page_config(page_title="🖼️ AI 이미지 생성", page_icon="🖼️")
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("🖼️ 한국어 텍스트 → AI 이미지")

korean_prompt = st.text_area(
    "🎨 **그리고 싶은 장면을 한국어로 묘사해 주세요!**",
    placeholder="예) 햇살 속에서 자전거 타는 어린이, 픽사 스타일",
    height=120,
)

col1, col2 = st.columns(2)
with col1:
    num_images = st.selectbox("🖼️ 이미지 개수", [1, 2, 3, 4], index=0)
with col2:
    size = st.selectbox("📐 해상도", ["1024x1024", "1024x1792", "1792x1024"], index=0)

# ------------------------------------------------------------
def make_eng_prompt(ko: str) -> str:
    """GPT-4o로 한국어 설명 → 60단어 이내 영문 프롬프트 변환"""
    rsp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": ("You are a prompt engineer for DALL·E-3. "
                         "Rewrite the user's Korean description as a vivid, specific "
                         "English prompt of max 60 words. No extra text.")},
            {"role": "user", "content": ko},
        ],
    )
    return rsp.choices[0].message.content.strip()


def make_title(ko: str) -> str:
    """GPT-4o로 ‘그림에 어울리는 한국어 제목’ 한 줄 생성"""
    rsp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": ("You are a creative copywriter. "
                         "Write a short, poetic Korean title (max 12 words) "
                         "that would suit an illustration of the following scene.")},
            {"role": "user", "content": ko},
        ],
    )
    return rsp.choices[0].message.content.strip()

# ------------------------------------------------------------
if st.button("🚀 이미지 생성") and korean_prompt.strip():
    # 1) 한글 → 영문 프롬프트
    with st.spinner("💬 프롬프트 작성 중…"):
        eng_prompt = make_eng_prompt(korean_prompt)

    st.markdown("✏️ **영문 프롬프트**")
    st.code(eng_prompt, language="markdown")

    # 2) 이미지 + 제목 1장씩 실시간 생성·표시
    st.markdown("## 결과")
    placeholder = st.empty()             # 첫 이미지용 빈 공간
    for idx in repeat(None, num_images):
        with st.spinner(f"🎨 {len(st.session_state)+1}/{num_images} 그리는 중…"):
            img = client.images.generate(
                model="dall-e-3",
                prompt=eng_prompt,
                n=1,                      # DALL·E-3는 n=1만 지원
                size=size,
                quality="standard",
            ).data[0].url
            title = make_title(korean_prompt)

        # 현재 placeholder에 이미지+캡션 출력 후,
        # 다음 이미지를 위해 새로운 placeholder 준비
        placeholder.image(img, caption=title, use_column_width=True)
        placeholder = st.empty()

else:
    st.caption("☝️ 장면을 입력하고 **[🚀 이미지 생성]** 버튼을 눌러 보세요.")
