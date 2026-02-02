# 디자인 가이드

## 10.A 컬러 토큰 정의

### 1) 컬러 토큰 (Design Tokens)

> 저채도 + 따뜻한 배경 + 깊은 그린을 기본으로, 포인트는 테라코타로 “약재/흙” 느낌을 주되 과하지 않게.
> 
- **Primary (Deep Pine Green)**
    - `-pine-900` : #0B2A24
    - `-pine-800` : #0F3A31
    - `-pine-700` : #165043
    - `-pine-600` : #1F6A59
- **Neutral (Warm Beige / Hanji)**
    - `-beige-50` : #FBF7F0
    - `-beige-100` : #F3EBDD
    - `-beige-200` : #E9DDC9
    - `-ink-900` : #1D1A16 (텍스트)
- **Accent (Warm Yellow)**
    - `-sun-400` : #F2C94C
    - `-sun-500` : #E7B93C
- **Point (Terracotta)**
    - `-terra-500` : #C86A4A
    - `-terra-600` : #B85B3E
- **Semantic**
    - 성공(회복/좋음): `-success` : #1F6A59 (pine-600 활용)
    - 경고(주의/부작용): `-warning` : #E7B93C (sun-500)
    - 위험(금기/중단): `-danger` : #B85B3E (terra-600)

### 2) 사용 규칙

- **배경**: beige-50~100 위주 (앱이 “따뜻한 종이 위에 쓰는 처방” 느낌)
- **주요 CTA 버튼**: pine-700 (가장 신뢰감)
- **주의/부작용 카드**: warning/danger는 “영역 강조”에만 사용(텍스트는 ink 유지)

---

## 10.B Tailwind 테마 설정 가이드

### 1) tailwind.config 확장 예시

```jsx
// tailwind.config.js
module.exports = {
theme: {
extend: {
colors: {
pine: {
900:"#0B2A24",
800:"#0F3A31",
700:"#165043",
600:"#1F6A59",
        },
beige: {
50:"#FBF7F0",
100:"#F3EBDD",
200:"#E9DDC9",
        },
sun: {
400:"#F2C94C",
500:"#E7B93C",
        },
terra: {
500:"#C86A4A",
600:"#B85B3E",
        },
ink: {
900:"#1D1A16",
700:"#3A342C",
500:"#5B5247",
        },
      },
borderRadius: {
xl2:"1.25rem",// 2xl 느낌의 둥근 카드
      },
boxShadow: {
soft:"0 8px 24px rgba(0,0,0,0.08)",
lift:"0 12px 32px rgba(0,0,0,0.10)",
      },
    },
  },
};

```

### 2) 기본 스타일 룰(추천)

- 카드: `bg-beige-50 border border-beige-200 rounded-xl2 shadow-soft`
- 섹션 타이틀: `text-2xl font-serif text-ink-900`
- 본문: `text-base font-sans text-ink-700 leading-7`
- CTA: `bg-pine-700 text-beige-50 hover:bg-pine-800`

---

## 10.C 타이포그래피 적용 규칙

### 1) 폰트 스택

- **Heading(Serif)**: `Nanum Myeongjo` 또는 `Noto Serif KR`
- **Body(Sans)**: `Pretendard` 또는 `Noto Sans KR`

### 2) 타입 스케일(모바일 기준)

- H1(페이지 타이틀): 22–24px / Serif / 700
- H2(섹션 타이틀): 18–20px / Serif / 700
- Body: 14–16px / Sans / 400–500
- Caption(보조): 12–13px / Sans / 400

### 3) 텍스트 톤

- “의학 용어”를 그대로 쓰기보다 **생활어 + 짧은 문장**
- 근거는 **접어두기(accordion)**로 제공(신뢰 + 피로도↓)

---

## 10.D 카드 컴포넌트 UI 규칙 (핵심 컴포넌트)

### 1) 공통 카드 구조

- **Header**: 아이콘 + 타이틀(Serif)
- **Body**: 2~4줄 요약(가독성)
- **Actions**: 저장/공유/지도/구매 등 1~2개만

### 2) 카드 종류 & 목적

1. **SymptomCard**
    - 입력한 증상을 “정리/요약”해서 보여줌
    - 예: “소화불량 + 피로” → “비위 기능 저하 가능성”
2. **FoodRecommendationCard**
    - 음식명, 핵심효과 2개, 추천 이유 1문장
    - “왜 추천?” 버튼 → 근거 펼치기
3. **IngredientSafetyCard** (효능/부작용)
    - 효능(✅) / 부작용(⚠️) / 금기(⛔)를 **명확히 분리**
    - 사용자는 안전정보를 “찾지 않아도 보이게” 해야 함
4. **VideoCard**
    - 3개만 노출(과다 노출 금지)
    - 태그(효능/조리/주의)로 빠른 판단
5. **ProductLinkCard**
    - 쿠팡/네이버 버튼을 “광고”가 아니라 **실천 버튼**으로 디자인
    - 예: “이 재료로 시작하기”

### 3) 카드 밀도 가이드

- 한 화면에 카드 1~2개만 “완전 읽기” 가능하도록
- 더보기로 확장

---

## 10.E 지도 화면 디자인 가이드 🗺️

### 1) 화면 레이아웃 (추천)

- 상단: 검색/필터 바 (고정)
- 중단: 지도(60%)
- 하단: 리스트 카드(40%) → 드래그로 확장(Bottom Sheet)

### 2) 지도 UX 규칙

- 마커 클릭 → **Bottom Sheet에 해당 음식점 카드 포커스**
- “추천 음식 포함”은 **라벨로 강조** (예: “생강차” “삼계탕”)

### 3) 필터(최소 필수)

- 거리(1km/3km/5km)
- 건강식/한식/약선/카페(생강차 등)
- 평점/리뷰수(가능하면)
- “추천 음식 포함” 토글

### 4) 음식점 카드 구성

- 이름 + 카테고리
- 대표 메뉴(추천 음식과 연결)
- 거리 + 영업중 여부(가능하면)
- 버튼: 길찾기 / 전화 / 저장

---

## 10.F 모바일 퍼스트 레이아웃 규칙 📱

### 1) 섹션형 스크롤(탭 ❌)

**섹션 순서 고정**이 핵심이야:

1. 증상 입력
2. 추천 음식
3. 효능·부작용
4. 영상
5. 구매
6. 지도

### 2) 상단 고정 요소

- “증상 입력창”만 sticky 가능
- 나머지는 스크롤 흐름 유지

### 3) 버튼 정책

- 화면당 Primary CTA는 1개만
    - 예: 추천 섹션에서는 “저장”
    - 지도 섹션에서는 “근처 찾기”

### 4) 게스트 → 회원 전환 UI(자연스럽게)

- 저장/히스토리에서만 로그인 유도
- 문구 예시:
    - “이 추천을 저장할까요? (1초 로그인)”

---

## 10.G 컴포넌트 네이밍 & 상태 디자인(개발 친화)

### 1) 컴포넌트(권장)

- `SymptomInput`
- `RecommendationSection`
- `FoodCard`
- `IngredientSafetyCard`
- `VideoCarousel`
- `ProductLinks`
- `MapSection`
- `RestaurantBottomSheet`

### 2) 상태(Empty/Loading/Error)

- Empty: 따뜻한 안내 + 예시 프롬프트 버튼 3개
- Loading: skeleton (카드 형태 유지)
- Error: “다시 시도” + “증상을 더 짧게” 힌트

---

## 10.H 바로 적용 가능한 UI 문구 톤(샘플)

- “오늘 어떤 증상이 제일 불편해요?”
- “이 음식이 도움이 될 수 있어요”
- “왜 이 음식을 추천하나요?”
- “주의해야 할 경우도 있어요”
- “근처에서 바로 먹을 수 있어요”