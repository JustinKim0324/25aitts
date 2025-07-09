import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
from pydub import AudioSegment
import tempfile
import os

# 페이지 설정
st.set_page_config(
    page_title="실시간 음성 인식",
    page_icon="🎤",
    layout="wide"
)

# 세션 상태 초기화
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'audio_count' not in st.session_state:
    st.session_state.audio_count = 0

# 음성 인식 함수
def transcribe_audio(audio_bytes, language="ko-KR"):
    """오디오 바이트를 텍스트로 변환"""
    recognizer = sr.Recognizer()
    
    try:
        # 오디오 데이터를 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        # WAV 파일로 변환 (audio_recorder는 wav 형식으로 녹음)
        audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
        audio.export(tmp_file_path, format="wav")
        
        # 음성 인식
        with sr.AudioFile(tmp_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language)
        
        # 임시 파일 삭제
        os.unlink(tmp_file_path)
        
        return text
    
    except sr.UnknownValueError:
        return "음성을 인식할 수 없습니다."
    except sr.RequestError as e:
        return f"음성 인식 서비스 오류: {e}"
    except Exception as e:
        return f"오류 발생: {e}"

# 메인 앱
def main():
    st.title("🎤 실시간 음성 인식 (Real-time STT)")
    st.markdown("녹음 버튼을 클릭하고 말씀하세요. 녹음이 끝나면 자동으로 텍스트로 변환됩니다.")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 언어 선택
        language = st.selectbox(
            "인식 언어",
            ["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어"],
            index=0
        )
        
        language_map = {
            "한국어": "ko-KR",
            "영어": "en-US",
            "일본어": "ja-JP",
            "중국어": "zh-CN",
            "스페인어": "es-ES",
            "프랑스어": "fr-FR"
        }
        
        selected_language = language_map[language]
        
        # 녹음 설정
        st.subheader("🎙️ 녹음 설정")
        auto_submit = st.checkbox("자동 제출", value=True, help="녹음이 끝나면 자동으로 텍스트 변환")
        
        # 사용 안내
        st.markdown("### 📖 사용 방법")
        st.markdown("""
        1. 🎤 버튼을 클릭하여 녹음을 시작합니다
        2. 말씀을 마치면 다시 클릭하여 녹음을 중지합니다
        3. 자동으로 텍스트로 변환됩니다
        4. 계속해서 녹음하면 텍스트가 누적됩니다
        """)
        
        # 텍스트 관리
        st.markdown("### 📝 텍스트 관리")
        if st.button("🗑️ 전체 텍스트 지우기", use_container_width=True):
            st.session_state.transcribed_text = ""
            st.rerun()
    
    # 메인 컨텐츠
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("🎙️ 음성 입력")
        
        # 오디오 레코더
        st.markdown("아래 버튼을 클릭하여 녹음하세요:")
        
        audio_bytes = audio_recorder(
            text="클릭하여 녹음 시작/중지",
            recording_color="#e74c3c",
            neutral_color="#2c3e50",
            icon_name="microphone",
            icon_size="3x",
            auto_start=False,
            pause_threshold=2.0,
            sample_rate=16000,
            key=f"audio_recorder_{st.session_state.audio_count}"
        )
        
        # 오디오가 녹음되면 처리
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if auto_submit:
                with st.spinner("음성을 텍스트로 변환 중..."):
                    text = transcribe_audio(audio_bytes, selected_language)
                    if text and text not in ["음성을 인식할 수 없습니다.", "음성 인식 서비스 오류"]:
                        st.session_state.transcribed_text += text + " "
                        st.session_state.audio_count += 1
                        st.success("✅ 변환 완료!")
                        st.rerun()
                    else:
                        st.warning(text)
        
        # 수동 변환 버튼
        if not auto_submit and audio_bytes:
            if st.button("📝 텍스트로 변환", type="primary", use_container_width=True):
                with st.spinner("음성을 텍스트로 변환 중..."):
                    text = transcribe_audio(audio_bytes, selected_language)
                    if text:
                        st.session_state.transcribed_text += text + " "
                        st.success("✅ 변환 완료!")
                        st.rerun()
    
    with col2:
        st.header("📝 인식된 텍스트")
        
        # 실시간 텍스트 표시
        text_area = st.text_area(
            "누적된 텍스트:",
            value=st.session_state.transcribed_text,
            height=400,
            key="main_text_area"
        )
        
        # 버튼 그룹
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            # 복사 버튼 (클립보드 복사는 JavaScript 필요)
            if st.button("📋 복사", use_container_width=True):
                st.info("텍스트를 선택하고 Ctrl+C (또는 Cmd+C)를 눌러 복사하세요")
        
        with col_btn2:
            # 편집 모드
            if st.button("✏️ 편집", use_container_width=True):
                st.session_state.transcribed_text = text_area
                st.success("텍스트가 업데이트되었습니다!")
        
        with col_btn3:
            # 다운로드 버튼
            if st.session_state.transcribed_text:
                st.download_button(
                    label="📥 다운로드",
                    data=st.session_state.transcribed_text,
                    file_name="transcript.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        # 통계 정보
        if st.session_state.transcribed_text:
            st.markdown("### 📊 통계")
            word_count = len(st.session_state.transcribed_text.split())
            char_count = len(st.session_state.transcribed_text)
            
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("단어 수", f"{word_count:,}")
            with metric_col2:
                st.metric("문자 수", f"{char_count:,}")
    
    # 푸터
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Google Speech Recognition API를 사용합니다</p>
            <p>Made with ❤️ using Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
