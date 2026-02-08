# Golden Questions Analysis Results (2026-02-08)

Date: 2026-02-08
Test Script: `docs/test/verify_golden_questions.py`
Scope: Golden Questions A, B, C, D Category Samples

---

## 1. Test Summary
- **Total Questions**: 5
- **Passed**: 5
- **Failed**: 0
- **Pass Rate**: 100%

| ID | Query | Category | Result | Confidence |
|---|---|---|---|---|
| **A1** | 식후 더부룩하고 트림이 잦아... | Digestion | ✅ PASS | Medium (Similarity) |
| **A2** | 속쓰림/역류가 있는데... | Digestion | ✅ PASS | Medium (Similarity) |
| **B1** | 잠이 얕고 새벽에 자주 깨... | Sleep | ✅ PASS | Medium (Similarity) |
| **C1** | 감기 기운(목 따가움)이 있어... | Immunity | ✅ PASS | Medium (Similarity) |
| **D1** | 혈압이 경계선. 짠맛 줄이기 말고... | Chronic | ✅ PASS | Medium (Similarity) |

---

## 2. Detailed Execution Log

```text
Running Golden Questions Analysis Test (5 Questions)...
============================================================

[Question A1] 식후 더부룩하고 트림이 잦아. 바로 먹으면 좋은 음식 3개와 피해야 할 음식 3개?
  -> Summary: '소화불량' 증상과 유사합니다.
  -> Confidence: medium
  -> Source: similarity
  -> Matched Symptom: 소화불량
  -> Ingredients Found: 3
     1. 율무 (good) - 율무는 소화기능을 강화하고 습을 제거합니다
     2. 찹쌀 (caution) - 찹쌀은 소화에 부담될 수 있습니다
     3. 우유 (caution) - 우유는 소화가 어려울 수 있으니 적당히 드세요
  -> Recipes Found: 3
     1. 생강차 (tea) - 생강차는 위장을 따뜻하게 하여 소화를 촉진합니다
     2. 무생채 (anytime) - 무생채는 소화효소가 풍부하여 체한 것을 풀어줍니다
     3. 매실차 (tea) - 매실차는 식욕을 돋우고 소화를 도웁니다
  -> Result: PASS

[Question A2] 속쓰림/역류가 있는데 매운 음식 말고 대체 레시피 추천해줘.
  -> Summary: '소화불량' 증상과 유사합니다.
  -> Confidence: medium
  -> Source: similarity
  -> Matched Symptom: 소화불량
  -> Ingredients Found: 3
     1. 율무 (good) - 율무는 소화기능을 강화하고 습을 제거합니다
     2. 찹쌀 (caution) - 찹쌀은 소화에 부담될 수 있습니다
     3. 우유 (caution) - 우유는 소화가 어려울 수 있으니 적당히 드세요
  -> Recipes Found: 3
     1. 생강차 (tea) - 생강차는 위장을 따뜻하게 하여 소화를 촉진합니다
     2. 무생채 (anytime) - 무생채는 소화효소가 풍부하여 체한 것을 풀어줍니다
     3. 매실차 (tea) - 매실차는 식욕을 돋우고 소화를 도웁니다
  -> Result: PASS

[Question B1] 잠이 얕고 새벽에 자주 깨. 저녁 식단/피해야 할 것?
  -> Summary: '불면증' 증상과 유사합니다.
  -> Confidence: medium
  -> Source: similarity
  -> Matched Symptom: 불면증
  -> Ingredients Found: 3
     1. 대추 (recommend) - 대추는 심신을 안정시키고 숙면을 돕습니다
     2. 연자(연자육) (recommend) - 연자(연자육)는 심장을 편안하게 하고 불면을 다스립니다
     3. 상추 (recommend) - 상추에는 수면 유도 성분(락투신)이 있습니다
  -> Recipes Found: 3
     1. 대추차 (tea) - 대추차는 심신을 안정시켜 숙면에 도움됩니다
     2. 연자죽 (dinner) - 연자죽은 마음을 편안하게 하여 불면에 좋습니다
     3. 상추겉절이 (dinner) - 상추의 락투신 성분이 수면을 유도합니다
  -> Result: PASS

[Question C1] 감기 기운(목 따가움)이 있어. 자극 없는 음식/차 추천.
  -> Summary: '기침' 증상과 유사합니다.
  -> Confidence: medium
  -> Source: similarity
  -> Matched Symptom: 기침
  -> Ingredients Found: 3
     1. 배 (recommend) - 배는 폐를 윤택하게 하고 기침을 진정시킵니다
     2. 연근 (good) - 연근은 폐를 맑게 하고 가래를 삭입니다
     3. 꿀 (good) - 꿀은 목을 부드럽게 하고 기침을 완화합니다
  -> Recipes Found: 3
     1. 배숙 (snack) - 배숙은 기침을 멎게 하고 폐를 윤택하게 합니다
     2. 도라지배즙 (tea) - 도라지배즙은 기관지를 보호합니다
     3. 연근차 (tea) - 연근차는 폐를 맑게 하고 가래를 삭입니다
  -> Result: PASS

[Question D1] 혈압이 경계선. 짠맛 줄이기 말고 '칼륨' 중심 식단 예시.
  -> Summary: '고혈압' 증상과 유사합니다.
  -> Confidence: medium
  -> Source: similarity
  -> Matched Symptom: 고혈압
  -> Ingredients Found: 2
     1. 메밀 (good) - 메밀은 루틴 성분이 있어 혈관 건강에 좋습니다
     2. 연근 (recommend) - 연근은 혈압 조절에 도움을 줄 수 있습니다
  -> Recipes Found: 0
  -> Result: PASS
```

---

## 3. Analysis & Improvements Made

### Issues Resolved
1. **Sorting Logic Fixed**: Use `priority DESC` to ensure recommended items appear before cautioned items.
2. **Missing Data Added**: Seeded `Hypertension` (고혈압) and `Diabetes` (당뇨) data to pass D1 test case.
3. **Keyword Mapping Enhanced**: Added synonyms for "속쓰림" -> "Digestive", "감기" -> "Respiratory" to improve match rates.

### Future Work
1. **Chronic Disease Recipes**: Add low-sodium/diabetic-friendly recipes for D-category.
2. **Drug Interaction (D6)**: Implement logic to check for drug-food interactions (e.g., Hypertension meds + Grapefruit).
3. **AI Integration**: Connect actual LLM for questions creating complex scenarios not covered by DB rules.
