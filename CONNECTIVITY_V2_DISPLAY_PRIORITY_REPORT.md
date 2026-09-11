# Connectivity v2 Display Priority Report

## 목적과 경계

표시 우선순위는 `connectivity_v2.structural_links`의 UI 전용 분류다. 링크 생성, 점유 라인 인접성, 경로 순회, 역할 근거, semantic, ERS, compatibility, 팀 지침 및 역할 카탈로그는 변경하지 않았다. 모든 구조 링크와 전진 경로는 분석 결과에 그대로 남는다.

## 결정론적 표시 규칙

`display_plan`은 기존 전진 경로를 좌·중앙·우 family로 묶는다. 각 family에서 노드 수가 가장 적은 완결 경로를 택하고, 동률이면 `route_id` 사전순으로 한 경로만 대표로 택한다. 나머지 경로는 `alternative_route_ids`로 기록한다. 이는 경로의 전술 품질 순위가 아니다.

* **PRIMARY**: family 대표 경로를 이루는 링크다. 기본 표시한다.
* **SECONDARY**: PRIMARY가 아닌 전진 링크다. 검증된 역할 semantic modifier가 있으면 기본 표시하고, 그 외에는 전체 연결 보기 또는 노드 선택 때 표시한다.
* **HIDDEN_DEFAULT**: recycle·support 등 나머지 구조 링크다. 기본 화면에서는 숨기되 분석 데이터와 전체 연결 보기에서는 유지한다.

`default_visible`과 `presentation_class`만 새 필드이며, `structural_links`의 수·ID·구조적 근거·route detection에는 영향을 주지 않는다.

## 7개 프리셋 표시 집계

아래는 역할 미지정 position-only 구조 기준이다. 전체 연결 수는 full-link 모드에서도 동일하다.

| 포메이션 | 전체 | PRIMARY | SECONDARY | HIDDEN_DEFAULT | 기본 표시 | 대표 family |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 4-2-3-1 | 38 | 5 | 10 | 23 | 5 | 좌, 우 |
| 4-3-3 | 40 | 5 | 13 | 22 | 5 | 좌, 우 |
| 4-4-2 | 42 | 4 | 16 | 22 | 4 | 좌, 우 |
| 4-2-4 | 38 | 4 | 14 | 20 | 4 | 좌, 우 |
| 3-4-2-1 | 42 | 6 | 12 | 24 | 6 | 좌, 우 |
| 3-4-3 | 38 | 6 | 11 | 21 | 6 | 좌, 우 |
| 3-5-2 | 48 | 5 | 14 | 29 | 5 | 좌, 우 |

해당 프리셋들은 route family 조건을 만족하는 순수 중앙 route가 없으므로 중앙 대표 family가 생성되지 않는다. 이는 중앙 연결이 없다는 전술 평가가 아니라, 현재 route family 규칙으로 대표할 완결 중앙 경로가 없다는 표시 결과다.

## UI 동작

피치 아래에 **주요 연결**과 **전체 연결** 제어를 추가했다. 기본은 주요 연결이며 PRIMARY와 역할 근거가 있는 SECONDARY를 보인다. 전체 연결은 모든 구조 링크를 표시한다. 선수 노드를 누르면 그 노드에 닿는 숨은 링크도 임시로 보여주고, 다시 누르면 선택을 해제한다. 보이는 링크를 누르면 기존 네 구역의 도구 설명을 보여준다: 구조적 연결, 역할 보정, 근거, 한계.

역할 modifier가 있는 링크에는 미세한 강조를 더하지만, 더 좋은 연결이라는 뜻으로 해석하지 않는다. 사용자용 평가는 숫자 중심 목록을 대표 경로·좌/중앙/우 진행 여부·공유 진행 연결점 중심 문장으로 바꿨다.

## 검증

`test_connectivity_engine_v2`에서 다음을 확인했다.

* 7개 프리셋의 구조 링크·전진 경로 수와 4-4-2/4-2-4 수리 결과 유지
* 표시 class 합계와 full-link 수가 구조 링크 수와 동일
* 기본 표시 수가 전체보다 작음
* representative route family 결정론성 및 역할 evidence 부재 시 PRIMARY 골격 유지
* recycle 링크가 엔진 출력에 유지됨
* Python과 browser v2 결과 완전 일치
* legacy Connectivity 61 edge 및 evidence completeness 회귀 유지

## 변경 파일

* `connectivity_engine_v2.py`
* `web/static/js/connectivity_engine_v2.js`
* `web/static/app.js`
* `web/static/index.html`
* `web/static/style.css`
* `test_connectivity_engine_v2.py`

## 알려진 한계

대표 경로는 configured position의 구조적 후보일 뿐 실제 패스·선수 능력·상대 압박·경기 결과를 나타내지 않는다. shared connector는 진짜 병목 검사가 아니며, 경로 제거 후 대체 경로 생존을 검사하는 별도 기능이 필요하다.

## Git 상태

이번 단계에서 commit과 push는 수행하지 않았다.
