# FM26 Tactical Lab Website MVP Publish Report

## 게시 결과

- 공개 기준 커밋: `13d9f3419559394e061b66cf3715364a6ca30a30` (`Polish published Website MVP`)
- Website MVP 게시 커밋: `cf1c46d5dbde068fe9c018c7a56dbd0ae6232dc7` (`Publish FM26 Tactical Lab website MVP`)
- 원격 동기화: 로컬 `HEAD`와 `origin/main`이 모두 `13d9f3419559394e061b66cf3715364a6ca30a30`
- GitHub Pages: 공개 페이지 접근 확인
- 공개 URL: https://dogdripcat.github.io/fm26-tactical-lab/

## 시각 폴리시

- 비활성 모드의 `hidden` 속성이 레이아웃 CSS보다 약하게 적용되어 분석 화면과 상대 비교 화면이 동시에 노출될 수 있던 문제를 수정했습니다.
- `[hidden] { display: none !important; }` 규칙으로 활성 모드만 표시되게 했습니다.
- 전술판, 포메이션 제어, 핵심 분석 카드, 연결성·전진성·지원 구조 영역과 상대 전술 비교 UI가 공개 페이지에서 로드되는 것을 확인했습니다.
- 상대 비교 화면은 구조 관찰만 표시하며 승률이나 등급을 표시하지 않습니다.

## 남은 가시적 제한

- 역할을 설정하고 분석하기 전에는 분석 카드에 결과 대신 안내 문구가 표시됩니다.
- 상대 비교는 현재 포메이션 구조 비교 범위이며 역할·경기 데이터가 없는 결과를 확정하지 않습니다.

## 검증 결과

- 전체 unittest: 243개, 통과
- `python fm26lab.py self-test`: 통과
- JavaScript 문법 검사: `web/static/app.js`, `support_evaluation_presenter.js`, `support_evaluator.js` 통과
- `git diff --check`: 통과
- 강제 푸시 없이 `main`에 푸시 완료

## 변경 범위

이번 폴리시에는 `web/static/style.css`의 표시 규칙만 변경했습니다. Connectivity, Progression, Support 평가 로직과 역할·근거 데이터는 변경하지 않았습니다.
