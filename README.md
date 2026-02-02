# 동의보감 기반 웰니스 앱

동의보감의 핵심 철학인 **식약동원(食藥同源)** 을 현대적으로 재해석하여,
일상 속 음식으로 건강을 관리할 수 있도록 돕는 웰니스 애플리케이션입니다.

---

## 🧭 프로젝트 개요

* 음식 중심의 예방적 건강 관리
* 증상/질환별 음식 추천
* 식재료 효능 정보 + 영상 콘텐츠
* 필요 시 신뢰 기반 외부 구매 링크 제공

> ⚠️ 본 서비스는 의료 행위를 대체하지 않으며, 모든 정보는 참고용입니다.

---

## 🧭 개발 루틴

이 프로젝트는 **Agent 기반 개발 루틴**을 기준으로 진행됩니다.

👉 아래 문서를 통해 **MVP 설계부터 배포까지의 전체 흐름**을 확인할 수 있습니다.

* 📄 [MVP → 배포까지 Agent 자동 루틴](docs/MVP_to_Deploy_Agent_Routine.md)

각 단계별로 사용되는 Agent와 체크 포인트가 정리되어 있어,
혼자 개발하더라도 팀 단위 개발처럼 일관된 흐름을 유지할 수 있습니다.

---

## 🛠 기술 스택 (예시)

* Frontend: Streamlit 또는 React + Tailwind CSS
* Backend: FastAPI (선택)
* Database: Supabase (PostgreSQL)
* Deployment: Streamlit Community Cloud / Vercel

---

## 🚀 로컬 실행 (예시)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📌 참고

* UI/UX는 동의보감 철학과 현대 웰니스 앱 감성을 결합하여 설계됩니다.
* 과장된 건강 표현이나 치료·완치 표현은 사용하지 않습니다.

---

## 📬 문의 / 기여

개선 제안이나 기여는 언제든 환영합니다.

## 🧭 개발 루틴

이 프로젝트는 **Agent 기반 개발 루틴**을 기준으로 진행됩니다.

- 📄 [MVP → 배포까지 Agent 자동 루틴](docs/MVP_to_Deploy_Agent_Routine.md)

각 단계별로 사용되는 Agent와 체크 포인트가 정리되어 있어,
혼자 개발하더라도 팀 단위 개발처럼 일관된 흐름을 유지할 수 있습니다.


This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
