"""
PubMed 논문 검색 서비스 모듈
E-utilities API를 사용하여 논문 검색 및 캐싱
"""
import os
import sys
import hashlib
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.supabase_client import get_supabase_client

load_dotenv()


@dataclass
class PubMedPaper:
    """PubMed 논문 정보"""
    pmid: str
    title: str
    abstract: str
    journal: str
    pub_year: int
    url: str
    summary_ko: Optional[str] = None


class PubMedService:
    """PubMed 논문 검색 서비스"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    
    def __init__(self):
        self.api_key = os.getenv("PUBMED_API_KEY", "")
        self.genai_key = os.getenv("API_KEY", "")
        self.db = get_supabase_client()
        
        # Configure GenAI for translation
        if self.genai_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.genai_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                print(f"GenAI Init Failed: {e}")
                self.model = None
        else:
            self.model = None

    async def translate_to_english(self, keyword_ko: str) -> str:
        """한글 의학/식재료 키워드를 영문(MeSH Term)으로 변환"""
        # 0. Try Google Translation API (REST) - User Suggestion
        if self.genai_key:
            try:
                url = "https://translation.googleapis.com/language/translate/v2"
                params = {
                    "q": keyword_ko,
                    "source": "ko",
                    "target": "en",
                    "format": "text",
                    "key": self.genai_key
                }
                # Using requests (sync) for simplicity, matching existing style
                resp = requests.post(url, params=params, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data and "translations" in data["data"]:
                        return data["data"]["translations"][0]["translatedText"]
                else:
                     print(f"Translation API Error: {resp.status_code} {resp.text}")
            except Exception as e:
                print(f"Google Translate API Failed: {e}")

        # 1. Try Gemini if available
        if self.model:
            try:
                prompt = f"""
                Translate the following Korean medical/food term into its most appropriate English scientific or MeSH term for PubMed search.
                Only return the English term. No explanation.
                
                Korean: {keyword_ko}
                English:
                """
                response = await self.model.generate_content_async(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"Gemini Translation error: {e}")
                # Fallthrough to OpenAI
        
        # 2. Try OpenAI Fallback
        try:
            import openai
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                client = openai.AsyncOpenAI(api_key=openai_key)
                response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Translate the Korean medical/food term to English MeSH term. Return only English text."},
                        {"role": "user", "content": keyword_ko}
                    ]
                )
                return response.choices[0].message.content.strip()
        except Exception as e_openai:
            print(f"OpenAI Translation Failed: {e_openai}")

        return keyword_ko

    
    async def search_papers(
        self, 
        query: str, 
        max_results: int = 3,
        use_cache: bool = True
    ) -> list[PubMedPaper]:
        """
        PubMed에서 논문 검색
        
        Args:
            query: 검색 쿼리 (영문)
            max_results: 최대 결과 수
            use_cache: 캐시 사용 여부
            
        Returns:
            list[PubMedPaper]: 논문 목록
        """
        if any(ord(char) > 127 for char in query):
            # 한글 포함 시 자동 번역
            translated_query = await self.translate_to_english(query)
            print(f"Translated '{query}' -> '{translated_query}'")
            query = translated_query

        # 캐시 확인
        if use_cache:
            cached = self._get_cached_papers(query)
            if cached:
                return cached[:max_results]
        
        # PubMed 검색
        pmids = self._search_pmids(query, max_results)
        if not pmids:
            return []
        
        # 논문 상세 정보 조회
        papers = self._fetch_paper_details(pmids)
        
        # 캐시 저장
        if papers:
            self._cache_papers(query, papers)
        
        return papers
    
    async def search_by_symptom_and_ingredient(
        self, 
        symptom_id: int, 
        rep_code: str
    ) -> list[PubMedPaper]:
        """
        증상-식재료 조합으로 논문 검색
        symptom_pubmed_map, ingredient_pubmed_map 테이블 활용
        """
        try:
            # 증상 키워드 조회
            symptom_result = self.db.table("symptom_pubmed_map").select(
                "keyword_en, mesh_term"
            ).eq("symptom_id", symptom_id).order("priority").limit(2).execute()
            
            # 식재료 키워드 조회
            ingredient_result = self.db.table("ingredient_pubmed_map").select(
                "ingredient_name_en, mesh_term, bioactive_compound"
            ).eq("rep_code", rep_code).order("priority").limit(2).execute()
            
            # 검색 쿼리 생성
            symptom_terms = []
            for row in symptom_result.data:
                if row.get("mesh_term"):
                    symptom_terms.append(f'"{row["mesh_term"]}"[MeSH]')
                elif row.get("keyword_en"):
                    symptom_terms.append(row["keyword_en"])
            
            ingredient_terms = []
            for row in ingredient_result.data:
                if row.get("mesh_term"):
                    ingredient_terms.append(f'"{row["mesh_term"]}"[MeSH]')
                elif row.get("ingredient_name_en"):
                    ingredient_terms.append(row["ingredient_name_en"])
                if row.get("bioactive_compound"):
                    ingredient_terms.append(row["bioactive_compound"])
            
            if not symptom_terms or not ingredient_terms:
                return []
            
            # AND로 조합
            query = f"({' OR '.join(symptom_terms)}) AND ({' OR '.join(ingredient_terms)})"
            
            return await self.search_papers(query, max_results=2)
            
        except Exception as e:
            print(f"증상-식재료 검색 오류: {e}")
            return []
    
    def _search_pmids(self, query: str, max_results: int) -> list[str]:
        """검색 쿼리로 PMID 목록 조회"""
        try:
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = requests.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
            
        except Exception as e:
            print(f"PMID 검색 오류: {e}")
            return []
    
    def _fetch_paper_details(self, pmids: list[str]) -> list[PubMedPaper]:
        """PMID로 논문 상세 정보 조회"""
        try:
            params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            }
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = requests.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            # XML 파싱 (간단 버전)
            return self._parse_xml_response(response.text, pmids)
            
        except Exception as e:
            print(f"논문 상세 조회 오류: {e}")
            return []
    
    def _parse_xml_response(self, xml_text: str, pmids: list[str]) -> list[PubMedPaper]:
        """XML 응답 파싱 (간단 구현)"""
        import re
        
        papers = []
        
        for pmid in pmids:
            try:
                # 제목 추출
                title_match = re.search(
                    r'<PMID[^>]*>' + pmid + r'</PMID>.*?<ArticleTitle>(.+?)</ArticleTitle>',
                    xml_text, re.DOTALL
                )
                title = title_match.group(1) if title_match else f"Paper {pmid}"
                title = re.sub(r'<[^>]+>', '', title)  # HTML 태그 제거
                
                # 저널 추출
                journal_match = re.search(
                    r'<PMID[^>]*>' + pmid + r'</PMID>.*?<Journal>.*?<Title>(.+?)</Title>',
                    xml_text, re.DOTALL
                )
                journal = journal_match.group(1) if journal_match else ""
                
                # 연도 추출
                year_match = re.search(
                    r'<PMID[^>]*>' + pmid + r'</PMID>.*?<PubDate>.*?<Year>(\d{4})</Year>',
                    xml_text, re.DOTALL
                )
                pub_year = int(year_match.group(1)) if year_match else 2024
                
                # 초록 추출
                abstract_match = re.search(
                    r'<PMID[^>]*>' + pmid + r'</PMID>.*?<Abstract>.*?<AbstractText[^>]*>(.+?)</AbstractText>',
                    xml_text, re.DOTALL
                )
                abstract = abstract_match.group(1) if abstract_match else ""
                abstract = re.sub(r'<[^>]+>', '', abstract)[:500]  # 500자 제한
                
                papers.append(PubMedPaper(
                    pmid=pmid,
                    title=title[:200],
                    abstract=abstract,
                    journal=journal[:100],
                    pub_year=pub_year,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                ))
                
            except Exception as e:
                print(f"PMID {pmid} 파싱 오류: {e}")
        
        return papers
    
    def _get_cached_papers(self, query: str) -> Optional[list[PubMedPaper]]:
        """캐시된 논문 조회"""
        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            result = self.db.table("pubmed_papers").select("*").filter(
                "pmid", "in", f"(SELECT pmid FROM pubmed_cache WHERE query_hash = '{query_hash}')"
            ).execute()
            
            # 간단히 DB에서 직접 조회
            # 실제로는 별도 캐시 테이블 필요
            return None
            
        except Exception:
            return None
    
    def _cache_papers(self, query: str, papers: list[PubMedPaper]):
        """논문 캐시 저장"""
        try:
            for paper in papers:
                self.db.table("pubmed_papers").upsert({
                    "pmid": paper.pmid,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "journal": paper.journal,
                    "pub_year": paper.pub_year,
                    "url": paper.url,
                    "updated_at": datetime.now().isoformat()
                }, on_conflict="pmid").execute()
        except Exception as e:
            print(f"캐시 저장 오류: {e}")


async def search_pubmed_papers(query: str, max_results: int = 2) -> list[dict]:
    """편의 함수: PubMed 논문 검색"""
    service = PubMedService()
    papers = await service.search_papers(query, max_results)
    
    return [
        {
            "pmid": p.pmid,
            "title": p.title,
            "abstract": p.abstract[:200] + "..." if len(p.abstract) > 200 else p.abstract,
            "journal": p.journal,
            "pub_year": p.pub_year,
            "url": p.url
        }
        for p in papers
    ]


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # 테스트
        queries = [
            "ginger digestive function",
            "도라지 기침",  # 한글 검색 테스트
            "radish stomach health"
        ]
        
        for query in queries:
            print(f"\n{'='*50}")
            print(f"검색: {query}")
            print("="*50)
            
            papers = await search_pubmed_papers(query)
            for p in papers:
                print(f"📄 {p['title'][:60]}...")
                print(f"   {p['journal']} ({p['pub_year']})")
                print(f"   {p['url']}")

    asyncio.run(main())
