import streamlit as st
from google import genai
from google.genai import types

# ---------- 기본 설정 ----------
st.set_page_config(page_title="AI 학습 도우미", page_icon="📚", layout="centered")

MODEL = "gemini-3.5-flash"  # 모델 이름이 안 맞으면 이 줄만 바꾸세요

STYLE_PROMPTS = {
    "쉬운 설명": "초보자도 이해할 수 있도록 쉬운 말과 비유로 설명하세요.",
    "단계별 풀이": "문제를 단계별로 나누어 차근차근 풀이하고, 각 단계의 이유를 설명하세요.",
    "퀴즈로 복습": "설명 후 이해도를 확인할 수 있는 짧은 퀴즈 1~2문제를 내고, 사용자가 답하면 피드백하세요.",
}


def build_system_prompt(subject: str, level: str, style: str) -> str:
    return (
        "당신은 친절한 한국어 학습 도우미입니다.\n"
        f"- 학습 과목: {subject}\n"
        f"- 학습자 수준: {level}\n"
        f"- 답변 방식: {STYLE_PROMPTS[style]}\n"
        "- 정답만 알려주기보다 학습자가 스스로 이해하도록 돕고, 답변은 너무 길지 않게 정리하세요.\n"
        "- 확실하지 않은 내용은 모른다고 솔직하게 말하세요."
    )


def to_gemini_contents(messages):
    """Streamlit 대화 기록을 Gemini 형식(user/model)으로 변환"""
    return [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]


# ---------- 사이드바 ----------
with st.sidebar:
    st.header("⚙️ 학습 설정")
    subject = st.selectbox("과목", ["경영학", "경제학", "통계/데이터분석", "영어", "수학", "프로그래밍", "기타"])
    level = st.radio("수준", ["입문", "중급", "심화"], horizontal=True)
    style = st.selectbox("답변 방식", list(STYLE_PROMPTS.keys()))

    api_key = st.secrets.get("GEMINI_API_KEY", "") or st.text_input(
        "Gemini API Key", type="password", help="배포 시에는 Streamlit Secrets에 저장하세요."
    )

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- 본문 ----------
st.title("📚 AI 학습 도우미")
st.caption("궁금한 개념이나 문제를 물어보세요. 왼쪽에서 과목·수준·답변 방식을 바꿀 수 있어요.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 표시
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 새 질문 처리
if prompt := st.chat_input("질문을 입력하세요 (예: 의사결정나무가 뭐야?)"):
    if not api_key:
        st.warning("왼쪽 사이드바에 Gemini API Key를 입력해 주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = genai.Client(api_key=api_key)
            stream = client.models.generate_content_stream(
                model=MODEL,
                contents=to_gemini_contents(st.session_state.messages),
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(subject, level, style),
                    max_output_tokens=1500,
                ),
            )
            answer = st.write_stream(chunk.text for chunk in stream if chunk.text)
        except Exception as e:
            answer = f"⚠️ 오류가 발생했어요: {e}"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
