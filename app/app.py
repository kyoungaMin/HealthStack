"""
PubMed RAG 챗봇 - 의학 논문 기반 질의응답 시스템
강남 세브란스병원 의료인공지능 교육 실습 자료
"""

import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
import time
from typing import List, Dict, Any
import json

# 필수 라이브러리 임포트
try:
    from Bio import Entrez, Medline
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    import pandas as pd
except ImportError as e:
    st.error(f"""
    필수 라이브러리가 설치되지 않았습니다. 다음 명령어로 설치해주세요:
    
    ```bash
    pip install streamlit biopython langchain langchain-openai openai pandas
    ```
    
    누락된 라이브러리: {e}
    """)
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="🏥 PubMed RAG 챗봇",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 PubMed RAG 의료 챗봇")

# 스트리밍 콜백 제거 (권한 이슈로 기본 비스트리밍 경로 사용)

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'papers_data' not in st.session_state:
    st.session_state.papers_data = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# 사이드바 설정
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    
    # API 키 입력
    st.markdown("### 🔑 API 설정 (env)")
    
    email = st.text_input(
        "Email (PubMed API용)",
        value="your.email@example.com",
        help="PubMed API 사용을 위한 이메일 주소"
    )
    
    # 검색 설정
    st.markdown("### 🔍 검색 설정")
    
    # 검색 키워드 입력 제거: 챗봇 입력란에서 직접 검색합니다
    
    max_results = st.slider(
        "최대 검색 결과 수",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help="가져올 논문의 최대 개수"
    )
    
    # 날짜 필터
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input(
            "시작 연도",
            min_value=2000,
            max_value=2024,
            value=2020
        )
    with col2:
        end_year = st.number_input(
            "종료 연도",
            min_value=2000,
            max_value=2024,
            value=2024
        )
    
    # LLM 설정
    st.markdown("### 🤖 LLM 설정")
    
    model_name = st.selectbox(
        "모델 선택",
        ["gpt-5", "gpt-5-mini", "gpt-5-nano"],
        help="사용할 OpenAI GPT-5 계열 모델 선택"
    )
    
# 환경 변수 로딩
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY", "")
if not openai_api_key:
    st.warning(".env 파일에서 OPENAI_API_KEY를 찾지 못했습니다. 환경변수를 설정해주세요.")

# PubMed 검색 함수
def search_pubmed(query: str, email: str, max_results: int, start_year: int, end_year: int) -> List[Dict]:
    """PubMed에서 논문 검색"""
    Entrez.email = email
    
    # 날짜 필터를 포함한 검색 쿼리 구성
    date_filter = f" AND {start_year}:{end_year}[dp]"
    full_query = query + date_filter
    
    try:
        # 검색 수행
        handle = Entrez.esearch(
            db="pubmed",
            term=full_query,
            retmax=max_results,
            sort="relevance"
        )
        search_results = Entrez.read(handle)
        handle.close()
        
        id_list = search_results["IdList"]
        
        if not id_list:
            return []
        
        # 논문 상세 정보 가져오기
        handle = Entrez.efetch(
            db="pubmed",
            id=id_list,
            rettype="medline",
            retmode="text"
        )
        
        papers = []
        records = list(Medline.parse(handle))
        handle.close()
        
        for record in records:
            paper = {
                "pmid": record.get("PMID", ""),
                "title": record.get("TI", "제목 없음"),
                "abstract": record.get("AB", "초록 없음"),
                "authors": ", ".join(record.get("AU", ["저자 정보 없음"])),
                "journal": record.get("TA", "저널 정보 없음"),
                "year": record.get("DP", "연도 정보 없음").split()[0] if record.get("DP") else "연도 정보 없음",
                "doi": next((ref for ref in record.get("AID", []) if ref.endswith("[doi]")), "").replace("[doi]", ""),
                "types": record.get("PT", []),
            }
            
            # 전체 텍스트 구성
            # 초록이 비어있으면 개별 재조회 시도
            if not paper["abstract"] or paper["abstract"].strip() in {"", "초록 없음"}:
                try:
                    ah = Entrez.efetch(db="pubmed", id=paper["pmid"], rettype="abstract", retmode="text")
                    abstract_txt = ah.read()
                    ah.close()
                    if isinstance(abstract_txt, bytes):
                        abstract_txt = abstract_txt.decode("utf-8", errors="ignore")
                    if abstract_txt and abstract_txt.strip():
                        paper["abstract"] = abstract_txt.strip()
                except Exception:
                    pass

            paper["full_text"] = f"""
                제목: {paper['title']}
                저자: {paper['authors']}
                저널: {paper['journal']}
                연도: {paper['year']}
                PMID: {paper['pmid']}
                DOI: {paper['doi']}

                초록:
                {paper['abstract']}
            """
            papers.append(paper)
        
        return papers
        
    except Exception as e:
        st.error(f"PubMed 검색 중 오류 발생: {str(e)}")
        return []

# PubMed 다이렉트 검색 기반 QA 함수
def answer_with_pubmed_direct(
    question: str,
    email: str,
    openai_api_key: str,
    model_name: str,
    max_results: int,
    start_year: int,
    end_year: int
):
    """간결 버전: 질문 → PubMed 검색 → 상위 3개 초록으로 맥락 구성 → 한 번 호출"""
    # 1) PubMed 검색 (초록 존재, 사설/서신 제외)
    q = f"({question}) AND hasabstract[text] NOT (Editorial[pt] OR Letter[pt] OR Comment[pt])"
    papers = search_pubmed(
        query=q,
        email=email,
        max_results=max_results,
        start_year=start_year,
        end_year=end_year
    )
    if not papers:
        return "관련 논문을 찾지 못했습니다.", []

    # 2) 맥락 구성 (상위 3개)
    top_papers = papers[:3]
    context_text = "\n\n".join(p.get("full_text", "") for p in top_papers if p.get("full_text"))

    # 3) 체인 구성 (LCEL)
    template = """
        당신은 의학 논문을 기반으로 정확한 정보를 제공하는 의료 AI 어시스턴트입니다.
        제공된 논문 정보만을 바탕으로 질문에 답하세요.
        반드시 출처(PMID, 저자, 연도)를 함께 제시하세요.

        Context:
        {context}

        Question:
        {question}
        """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI(api_key=openai_api_key, model=model_name)
    chain = prompt | llm | StrOutputParser()

    # 4) 답변 생성
    answer = chain.invoke({"context": context_text, "question": question}).strip()
    print(context_text)
    print(question)
    
    print('==========ANSWER==========')
    print(answer)
    print('='*90)
    # 5) 출처 정리
    sources = [
        {
            "title": p.get("title", ""),
            "authors": p.get("authors", ""),
            "journal": p.get("journal", ""),
            "year": p.get("year", ""),
            "pmid": p.get("pmid", ""),
            "abstract": p.get("abstract", "")
        }
        for p in top_papers
    ]

    return answer, sources

# 메인 앱
def main():
    # 탭 생성
    tab1, tab2 = st.tabs(["💬 챗봇", "📜 검색 기록"])
    
    # 논문 검색 탭 제거됨
    
    with tab1:
        st.markdown("### 💬 의학 논문 기반 Q&A")
        
        # 채팅 인터페이스 (벡터DB 없이 다이렉트 PubMed)
        chat_container = st.container()
            
        # 메시지 표시
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # 출처 표시
                    if "sources" in message:
                        st.markdown("---")
                        st.markdown("**📚 참고 논문:**")
                        for source in message["sources"]:
                            st.markdown(f"- **{source['title']}**  ")
                            st.caption(f"저자: {source['authors']} | 저널: {source['journal']} ({source['year']}) | PMID: {source['pmid']}")
        
        # 질문 입력
        if prompt := st.chat_input("의학 관련 질문을 입력하세요..."):
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI 응답 생성 (PubMed 다이렉트 검색) + 스트리밍
            with st.chat_message("assistant"):
                    with st.spinner("답변 생성 중..."):
                        try:
                            # 스트리밍용 플레이스홀더
                            stream_placeholder = st.empty()
                            partial_text = ""

                            # 비스트리밍 생성을 먼저 얻고, 표시만 스트리밍처럼 이어붙이기
                            answer, sources = answer_with_pubmed_direct(
                                question=prompt,
                                email=email,
                                openai_api_key=openai_api_key,
                                model_name=model_name,
                                max_results=max_results,
                                start_year=start_year,
                                end_year=end_year
                            )
                            print('==========ANSWER==========')
                            print(answer)
                            
                            # 스트리밍은 콜백으로 실시간 출력되므로 최종 확정 텍스트만 보정 표시
                            if answer and answer.strip():
                                stream_placeholder.markdown(answer)
                            else:
                                stream_placeholder.markdown("답변을 생성하지 못했습니다.")
                            
                            # 출처 표시 + 초록 미리보기
                            if sources:
                                st.markdown("---")
                                st.markdown("**📚 참고 논문:**")
                                for idx, source in enumerate(sources, 1):
                                    with st.expander(f"{idx}. {source['title']} (PMID: {source['pmid']})"):
                                        st.markdown(f"저자: {source['authors']}")
                                        st.markdown(f"저널: {source['journal']} ({source['year']})")
                                        abstract_text = source.get("abstract", "") or "초록 없음"
                                        st.markdown("**초록:**")
                                        st.text_area("초록", abstract_text, height=180, disabled=True, key=f"src_abs_{idx}", label_visibility="collapsed")
                                        pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{source['pmid']}/"
                                        st.markdown(f"[🔗 PubMed에서 보기]({pubmed_url})")
                            
                            # 메시지 저장
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": answer,
                                "sources": sources
                            })
                            
                        except Exception as e:
                            st.error(f"답변 생성 중 오류 발생: {str(e)}")
            
        # 대화 초기화 버튼
        if st.button("🔄 대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    
    with tab2:
        st.markdown("### 📜 검색 기록")
        
        if st.session_state.search_history:
            # 검색 기록을 데이터프레임으로 변환
            history_df = pd.DataFrame(st.session_state.search_history)
            history_df = history_df.sort_values('timestamp', ascending=False)
            
            # 표시
            for idx, row in history_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**검색어:** {row['query']}")
                    
                    with col2:
                        st.markdown(f"**시간:** {row['timestamp']}")
                    
                    with col3:
                        st.markdown(f"**결과:** {row['results']}개")
                    
                    st.markdown("---")
            
            # 검색 기록 다운로드
            csv = history_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 검색 기록 다운로드 (CSV)",
                data=csv,
                file_name=f"search_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # 기록 초기화 버튼
            if st.button("🗑️ 검색 기록 초기화"):
                st.session_state.search_history = []
                st.rerun()
        else:
            st.info("검색 기록이 없습니다.")

# 앱 정보
with st.expander("ℹ️ 앱 사용 방법"):
    st.markdown("""
    ### 🎯 PubMed RAG 챗봇 사용 가이드
    
    1. **논문 검색**: 키워드와 검색 옵션을 설정한 후 논문을 검색합니다
    2. **챗봇 사용**: 검색된 논문을 바탕으로 의학 관련 질문을 합니다
    
    ### 📚 주요 기능
    - **PubMed 실시간 검색**: 최신 의학 논문 검색
    - **RAG 기반 Q&A**: 논문 내용 기반 정확한 답변
    - **출처 제공**: 답변의 근거가 되는 논문 정보 표시
    
    """)

if __name__ == "__main__":
    main()
