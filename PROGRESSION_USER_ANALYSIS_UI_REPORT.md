# Progression User-Facing Analysis UI

## UI structure

기존 피치와 Connectivity 섹션은 유지했다. 그 아래에 컴팩트한 `전진성` 섹션을 추가했다. 섹션은 전진 구조 요약, 최고 도달 라인, 좌·중앙·우 카드, 전진 방식/정체/의존도 관측, 접힌 역할 보정과 근거·한계로 구성된다. 피치를 밀어내는 독립 대시보드는 추가하지 않았다.

## Presenter architecture

`web/static/js/progression_evaluation_presenter.js`는 `progression_evaluation`과 기존 Connectivity v2 링크를 입력으로 받아 한국어 표시 데이터를 만든다. 이 모듈은 엔진 상태를 번역·그룹화·대표 경로 선택만 하며 전진 이벤트, skip, dependency, stall, 최고 도달 라인을 계산하지 않는다. `app.js`는 presenter가 제공한 기존 route ID를 피치 강조 상태에 전달할 뿐이다.

## Summary, regional cards, line patterns

- 요약은 advancement continuity, evaluator의 최고 도달 라인, 지역 상태만 사용한다.
- 좌·중앙·우 카드는 전방 도달, 중간 라인 도달, 지원/측면 연결만 가능, 직접 전진 없음 상태를 점수 없이 보여준다.
- line gain은 한 라인씩 전진 또는 한 번에 두 점유 라인을 넘는 경로가 있는지 서술한다.
- line skip은 `점유한 중간 라인을 건너뛰는 전진 경로`라고만 표시한다. 성공·위협·품질 판단을 붙이지 않는다.

## Stall, dependency, role adjustments

엔진이 확인한 `advance_then_stall`만 표시하며 forward 종점은 표시하지 않는다. Progression dependency도 엔진의 제거 시뮬레이션 결과만 표시하며 Connectivity dependency나 공유 연결자 상태는 사용하지 않는다. 역할 보정은 접힌 영역에 표시되고, 기존 전진 구조를 설명할 뿐 링크·점유 라인·전진 경로를 바꾸지 않는다는 한계를 함께 명시한다.

## Pitch interaction

지역 카드를 누르면 해당 presenter가 선택한 `route_family_id`의 기존 대표 route ID만 청록색으로 피치에 강조한다. Progression dependency를 누르면 dependency 노드와 그 노드를 포함하는 기존 대표 경로를 강조한다. Connectivity 지역 선택과 Progression 강조는 동시에 중첩하지 않도록 서로의 선택을 해제한다. 포메이션 변경, 역할 변경, 초기화, 재분석은 Progression 선택·경로·노드 상태를 초기화한다.

## Responsive behaviour

데스크톱에서는 3개 지역 카드와 전진 관측을 가로로 배치한다. 좁은 화면에서는 지역 카드와 관측이 한 열로 전환되며 피치의 최대 폭과 기존 팀 지침 IP/OOP 탭 구조는 유지한다.

## Tests

`test_progression_user_analysis_ui.py`를 추가했다.

- 합성 A–L: 요약, skip, stall, dependency, 측면 전환, 점수 미사용을 확인
- 7개 프리셋: 요약, 최고 도달 라인, 좌/중앙/우 카드, false stall, raw route-count 문구 미사용을 확인
- 상호작용 상태: Progression 경로 선택, 강조 클래스, 포메이션/재분석 시 초기화 코드를 확인

## Regression and limitations

Connectivity v2 baseline은 4-2-3-1 `38/16`, 4-3-3 `40/48`, 4-4-2 `42/32`, 4-2-4 `38/32`, 3-4-2-1 `42/25`, 3-4-3 `38/20`, 3-5-2 `48/40`으로 유지된다.

UI는 실제 패스 성공률, 선수 능력치, 상대 압박, 경기 상황, 팀 지침 효과, Penetration, Chance Creation, Goal Threat를 분석하거나 표시하지 않는다. 미완성 ST 역할 카탈로그도 이번 작업에서 수정하지 않았다.

## Files changed

- `web/static/js/progression_evaluation_presenter.js`
- `web/static/js/progression_presentation_runner.mjs`
- `web/static/app.js`
- `web/static/index.html`
- `web/static/style.css`
- `test_progression_user_analysis_ui.py`
- 이 보고서

기존 Progression Phase 1 및 Acceptance Audit의 uncommitted 파일은 유지했다. 커밋과 push는 수행하지 않았다.

## Final checks

- 전체 unittest: 226 passed
- `python fm26lab.py self-test`: passed
- Python/JavaScript Progression parity: passed
- static browser runner: passed
- JavaScript syntax checks: passed
- `git diff --check`: passed
