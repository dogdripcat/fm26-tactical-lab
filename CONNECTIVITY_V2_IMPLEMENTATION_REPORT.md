# Connectivity v2 구현 보고

## 변경

- `connectivity_engine_v2.py`: Python 구조 기준 구현.
- `web/static/js/connectivity_engine_v2.js`: 정적 브라우저 동등 구현.
- `core/pipeline.py`: 기존 `connectivity`를 유지하고 병렬 `connectivity_v2`를 추가.
- `web/static/js/tactic_analysis.js`: 정적 분석 결과에 v2를 병렬 추가.
- `web/static/js/parity_runner_v2.mjs`, `test_connectivity_engine_v2.py`: Python–브라우저 parity와 구조 회귀 검증.

legacy `connectivity_engine.py`와 `connectivity_engine.js`는 변경하지 않았다. evidence completeness는 연구·설명 계층으로 유지된다.

## Leicester 4-2-3-1 예시

현재 샘플에서 v2는 노드 11개, 구조적 링크 38개, 전진 경로 16개, 공유 진행 연결점 9개를 생성한다. 이 수치는 점수나 경기 예측이 아니라 현재 positional ontology가 만드는 결정론적 구조 출력이다.

역할 modifier는 예를 들어 DLP의 `send_forward`, AM의 `receive_between_lines`처럼 기존 검증 semantic이 있는 경우에만 링크 설명에 붙는다. CFD의 semantic 부재는 ST와 AMC 사이의 구조적 후보 링크를 제거하지 않는다.

## 검증 범위

- 역할 behaviour를 제거한 복사 KB에서도 구조 링크가 유지됨
- semantic은 링크를 생성하는 대신 modifier로만 추가됨
- 3백 fixture의 dedicated wing-back 노드가 유지됨
- 팀 지침 변경이 v2 결과를 바꾸지 않음
- 4개 golden fixture에서 Python과 browser v2 출력이 동일함
- legacy Leicester graph는 61 edges / 2 semantic complete / 7 mixed / 4 compatibility only / 48 evidence missing을 유지함

## 제한

v2는 currently configured IP position 관계만 다룬다. 역할의 실제 경기 이동, 실제 수신 가능성, 패스 빈도·성공률, 상대 압박, OOP 편집 및 팀 지침 효과는 모델링하지 않는다. Forward catalogue는 현재 CFD·CHF만 selectable인 미해결 데이터 블로커이며 이번 작업에서 수정하지 않았다.
