"""
📖 성경 구절 → 어린이 설교 일러스트
────────────────────────────────
1. 성경 구절(본문 또는 장·절)을 입력
2. [일러스트 생성] 클릭
   ├─ GPT-4o : 장면 요약 + “완벽한” DALL·E-3 프롬프트 + 한국어 제목(≤15자) 생성
   └─ DALL·E-3 : 귀여운 Sunday-school 스타일 일러스트(1024×1024) 반환
3. PNG 다운로드 또는 ZIP 저장
"""

import streamlit as st
from openai import OpenAI
import requests, io, zipfile

# ──────────────────────────── 기본 설정 ──────────────────────────── #
st.set_page_config(page_title="📖 성경 일러스트", page_icon="📖")
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ──────────────────────────── UI ──────────────────────────── #
st.title("📖 성경 구절로 어린이용 일러스트 만들기")

verse = st.text_area(
    "📝 **성경 구절(본문 또는 장·절)을 입력하세요**",
    placeholder="예) 요한복음 6:9\n\n어떤 아이가 보리 떡 다섯 개와 물고기 두 마리를 가지고 왔습니다...",
    height=160,
)

col1, col2 = st.columns(2)
with col1:
    size = st.selectbox("📐 해상도", ["1024x1024", "1024x1792", "1792x1024"], 0)
with col2:
    style = st.selectbox(
        "🎨 스타일 프리셋",
        ["교회 공과책 느낌", "밝은 파스텔 수채화", "따뜻한 톤의 플랫툰", "연필 드로잉 + 채색"],
        0,
    )

# ──────────────────────────── 실행 ──────────────────────────── #
if st.button("🚀 일러스트 생성") and verse.strip():

    # 1️⃣ GPT-4o : DALL·E 프롬프트 & 한국어 제목 생성
    with st.spinner("📜 프롬프트 작성 중…"):
        sys_prompt = (
            "You are an elite prompt engineer for DALL·E 3.\n"
            "When the user provides a Bible verse or passage, "
            "return EXACTLY two lines in this format:\n"
            "PROMPT: <English prompt for DALL·E 3>\n"
            "TITLE : <Korean title ≤ 15 chars>\n\n"
            "# Prompt template (fill the [bracket] parts, keep the rest verbatim!)\n"
            "PROMPT MUST include the following 10 blocks *in order*, separated by comma:\n"
            "1) cute Sunday-school illustration, children’s picture-book style\n"
            "2) for Protestant elementary kids (age 6-8)\n"
            "3) [SCENE] ← vivid 40-word English scene derived from the verse\n"
            "4) smiling Jesus in off-white robe & soft red sash, joyful children with simple round eyes\n"
            "5) bright outdoor setting with soft hills, wildflowers, clear blue sky\n"
            "6) warm pastel (#FBEAD1, #F8D6D0, #CDEBF7)\n"
            "7) clean thick outlines, gentle watercolor shading\n"
            "8) eye-level perspective, balanced composition\n"
            "9) no text, no watermark, no copyright\n"
            "10) --ar 1:1 --size 1024x1024\n\n"
            "After the PROMPT line, output\n"
            "TITLE: <short Korean title summarising the message, max 15 chars>."
        )
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"{verse}\n\nRequested art style: {style}"},
        ]
        resp = client.chat.completions.create(model="gpt-4o", messages=messages)
        lines = resp.choices[0].message.content.splitlines()
        eng_prompt = lines[0].replace("PROMPT:", "").strip()
        ko_title   = lines[1].replace("TITLE:", "").strip()

    st.markdown("✏️ **DALL·E 프롬프트**")
    st.code(eng_prompt, language="markdown")

    # 2️⃣ DALL·E-3 : 이미지 생성
    with st.spinner("🎨 DALL·E-3가 그림을 그리는 중…"):
        img = client.images.generate(
            model="dall-e-3",
            prompt=eng_prompt,
            n=1,                # DALL·E-3는 n=1만 지원
            size=size,
            quality="standard",
        )
        url = img.data[0].url
        png = requests.get(url).content

    # 3️⃣ 결과 표시 + PNG 다운로드
    st.subheader(f"🖼️ {ko_title}")
    st.image(url, use_container_width=True)
    st.download_button(
        "💾 PNG 다운로드", png,
        file_name=f"{ko_title}.png", mime="image/png"
    )

    # 4️⃣ ZIP 다운로드 (단일 이미지지만 추후 다중 확장 대비 예시)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr(f"{ko_title}.png", png)
    zip_buf.seek(0)
    st.download_button(
        "📦 ZIP으로 저장", zip_buf,
        file_name="bible_illustration.zip", mime="application/zip"
    )

else:
    st.caption("☝️ 구절을 입력하고 **[🚀 일러스트 생성]** 버튼을 눌러 보세요!")
