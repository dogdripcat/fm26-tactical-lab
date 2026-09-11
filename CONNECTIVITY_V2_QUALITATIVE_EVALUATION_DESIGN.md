# Connectivity v2 Qualitative Evaluation Model Audit

## 1. 범위와 결론

이 문서는 구현 계획과 감사 결과다. production Connectivity v2, public UI, 역할 카탈로그·행동·semantic·ERS·compatibility·팀 지침 데이터는 수정하지 않았다. 현재 피치의 `PRIMARY / SECONDARY / HIDDEN_DEFAULT`는 표시 계층일 뿐이며, 이 설계의 판단 입력은 언제나 **전체** `structural_links`와 `progression_routes`다.

Connectivity의 정성적 의미는 다음 한 문장으로 한정한다.

> 구성된 위치 관계에서 공이 전방으로 이어질 수 있는 구조적 후보와, 그 후보의 대안·의존·되돌림 구조를 설명한다.

이는 실제 패스 성공, 점유율, 찬스 품질, 선수 능력 또는 경기 결과를 예측하지 않는다.

## 2. 링크 수와 raw route 수가 품질이 아닌 이유

링크가 많으면 같은 라인의 support·뒤로 가는 recycle·동일 spine의 조합이 함께 늘어난다. route 수도 출발 수비수나 종점 공격수 한 명만 달라지는 조합으로 급증할 수 있다. 따라서 link/route 수는 디버그용 topology 규모일 뿐, 좋은 연결성의 근거가 될 수 없다.

이후 평가는 수치 합산이나 가중치를 사용하지 않고, 아래와 같은 명시적 구조 상태와 해당 사실의 근거를 출력해야 한다.

## 3. 기본 계층 분리

| 계층 | 입력 | 책임 | 평가에 사용하는 방식 |
| --- | --- | --- | --- |
| Engine topology | 전체 structural link와 progression route | 위치 기반 구조 후보 | 정성 평가의 유일한 그래프 입력 |
| Display graph | PRIMARY/SECONDARY/HIDDEN_DEFAULT | 피치 가독성 | 평가에 사용하지 않음 |
| Role adjustment | 검증된 role semantic·ERS | configured position과 다른 예상 점유·수신 맥락 | 그래프 변경 없이 별도 설명만 추가 |

## 4. 평가 차원과 결정론적 정의

### Line continuity

정렬된 configured vertical index의 연속된 두 점유 라인마다, 전자의 어떤 노드에서 후자의 어떤 노드로 향하는 forward structural link가 하나 이상 있으면 그 line transition은 `covered`다.

* 모든 인접 점유 라인이 covered: `continuous`
* 일부만 covered: `partially_continuous`
* 어느 인접 line transition도 covered하지 않거나 깊은 시작 구조에서 전방까지 완결 route가 없을 때: `structurally_interrupted`

DM·AM line의 존재는 요구하지 않는다. 4-4-2처럼 defence→midfield→forward가 되는 formation-specific sequence도 같은 규칙으로 처리한다.

### Progression availability

깊은 시작 구조에서 forward band의 configured terminal node로 이어지는 forward-only route가 있으면 `complete_route_present`다. 없으면 `no_complete_route_detected`다. 이후 route diversity가 하나의 spine만 남긴다고 판정할 근거가 있으면 `single_major_corridor`; 둘 이상의 structurally distinct family가 있으면 `multiple_structurally_distinct_routes`를 함께 기록한다. 이 표현은 찬스의 질을 말하지 않는다.

### Structurally distinct route

raw route는 다음 signature가 모두 같으면 같은 구조 family로 묶는다.

1. configured deep-origin region (`left`, `centre`, `right`)
2. dominant region: forward transition에서 가장 많이 점유한 region; 동률은 출발 region
3. final receiving region
4. ordered occupied-line transition sequence
5. 각 중간 occupied line에서 사용한 bridge node identity 집합

이 다섯 항목 가운데 하나라도 다르면 distinct candidate다. 단, 출발 수비수나 종점 forward만 바뀌고 2~5가 같다면 같은 family의 alternative다. 이는 CSS 좌표·화면상 선의 모양이 아니라 configured-position topology만 사용한다. 이 signature는 이후 작은 순수 함수로 검증해야 하며, 현재는 production output에 추가하지 않는다.

### Regional progression과 cross-region access

각 region에 대해 deep-origin에서 forward terminal까지의 complete route 존재 여부와, structurally distinct family의 대안 존재 여부를 별도로 기록한다. 어느 route도 없는 region은 `progression_not_detected`이고, 이를 전술적 약점이라고 단정하지 않는다.

cross-region access는 전체 topology에서 인접 lane 사이(`left↔centre`, `centre↔right`)의 방향 있는 path 존재 여부를 검토한다. `left↔right`는 centre를 경유한 path만 인정한다. far-side 직접 link를 새로 만들거나 가정하지 않는다. 분석은 전진·support·recycle edge를 구분하여 “전진 중 교차”와 “순환을 포함한 구조 접근”을 따로 표현해야 한다.

### Support / recycle availability

전진 route의 **비종점** 노드마다 다음 중 하나가 있으면 fallback outlet 후보가 있다.

* 더 깊은 configured line으로 가는 recycle edge
* 같은 configured line의 support edge

둘 다 있으면 `multiple_fallback_types`, 하나면 `one_fallback_type`, 없으면 `fallback_not_detected`다. 이는 볼 보유 안정성의 예측이 아니라 구조적 되돌림/보조 선택지가 표현되었는지만 뜻한다.

### Connector dependency와 strict structural bottleneck

현재 `shared_progression_connector`는 단지 여러 raw route에 등장한다는 사실이다. dependency가 아니며 병목도 아니다.

후보 node dependency 분석은 다음 route-survival 절차를 사용한다.

1. 전체 topology에서 origin region별 complete progression family를 계산한다.
2. 한 node와 incident edge를 제거한다.
3. 같은 origin/region 정의로 family를 다시 계산한다.
4. baseline과 survivor를 비교한다.

보고 상태는 수치 없이 다음처럼 구분한다.

* `no_meaningful_impact`: origin-region progression family가 모두 남음
* `alternative_removed`: 적어도 하나의 distinct family가 사라지지만 각 baseline origin region의 complete progression은 남음
* `regional_progression_removed`: 기존에 complete progression이 있던 origin region 하나 이상이 모두 사라짐
* `all_complete_progression_removed`: 모든 baseline complete progression이 사라짐

node는 `structural_bottleneck_candidate`가 되려면 `regional_progression_removed` 또는 `all_complete_progression_removed`를 만족해야 한다. 후자는 “critical structural bridge”로 설명할 수 있다. 여러 route에 등장했다는 빈도만으로 이 상태를 만들지 않는다.

edge-removal은 node-removal과 다른 정보를 줄 수 있지만, 현재 phase에서는 구현하지 않는다. node survival 결과가 충분히 검증된 뒤에만 별도 비교 대상으로 검토한다.

### Dead end와 isolation

* `isolated_node`: configured topology에서 incident structural link가 전혀 없는 node다.
* `dead_end_candidate`: forward terminal이 아닌 node가 깊은 시작 구조에서 forward로 도달 가능하지만, forward terminal로 이어지는 path·support/recycle outlet·인접 region outlet이 모두 없다.
* `terminal_attacking_endpoint`: forward band node는 low degree여도 dead end가 아니다.
* `wide_unconnected_context`: wide node는 generic degree만으로 dead end/isolated라고 부르지 않는다. 위의 incident-link 및 route-reachability 조건을 충족할 때만 별도 후보가 된다.

따라서 degree가 작다는 사실만으로 위치를 고립 또는 문제로 분류하지 않는다.

## 5. 역할 modifier와 Expected Role Space의 경계

Configured position은 현재 baseline graph의 시작 위치다. Expected Role Space는 검증된 role behaviour가 제안하는 예상 점유·수신·이동 맥락이다. 둘을 하나의 graph로 합치지 않는다.

`move_inside`, `move_into_halfspace`, `hold_width`, `receive_between_lines`, `receive_centrally`, `support_central_passing_links`, `open_space_for_fullback`, `attack_space_in_behind`는 검증된 evidence가 있는 경우에 한해 `role_adjustments`에 다음과 같이 주석으로만 남길 수 있다.

* 해당 configured node
* semantic ID와 evidence IDs
* 예상 점유/수신/이동의 한국어 설명
* “구조 링크를 생성·삭제하지 않음” limitation

role evidence coverage가 낮다는 사실은 tactical quality가 아니라 evidence limitation으로만 표시한다.

## 6. 7개 preset의 읽기 전용 비교

현재 position-only v2 topology를 읽어 확인했다. 모든 preset은 점유 line transition이 연속되고 complete forward route가 있다. 이는 formation 우열이 아니라, 현행 position registry와 occupied-line adjacency 규칙 아래의 구조 사실이다.

| Formation | line continuity | progression region | raw route 해석 | shared connector 해석 | support/recycle 구조 |
| --- | --- | --- | --- | --- | --- |
| 4-2-3-1 | continuous | 좌·우 representative route, 중앙 경유 route 존재 | 16개 raw route는 DML/DMR·AMC 등 공통 spine 조합을 포함 | 현재 shared 표시만 가능; survival 미실행 | support와 recycle edge 존재 |
| 4-3-3 | continuous | 좌·우 representative route, 중앙 DM 경유 | 48개는 여러 출발/종점 조합을 포함하므로 diversity와 동의어 아님 | DM 등은 shared일 수 있으나 dependency 미판정 | support와 recycle edge 존재 |
| 4-4-2 | continuous | 좌·우 representative route | 32개는 두 midfield/두 forward 조합을 포함 | 중간선 노드는 shared 표시만 가능 | support와 recycle edge 존재 |
| 4-2-4 | continuous | 좌·우 representative route | 32개; wide attacking node를 통과하는 route와 직접 forward route가 함께 있음 | 중간선/공격선 node의 dependency는 survival 필요 | support와 recycle edge 존재 |
| 3-4-2-1 | continuous | 좌·우 representative route, centre node를 통한 일부 교차 | 25개; 3CB 출발 조합은 raw route를 증가시킴 | wing-back/central midfield는 shared 표시만 가능 | support와 recycle edge 존재 |
| 3-4-3 | continuous | 좌·우 representative route | 20개; 역할이나 실제 전개 우열을 뜻하지 않음 | shared node는 bottleneck이 아님 | support와 recycle edge 존재 |
| 3-5-2 | continuous | 좌·우 representative route, 중앙 MC 경유 route 존재 | 40개; 여러 defender/forward 조합을 deduplicate해야 함 | MC 포함 shared node는 survival 전 후보일 뿐 | support와 recycle edge 존재 |

현재 display family에서 중앙 대표가 없는 preset도 있다. 이는 중앙 전술이 없다는 판정이 아니라, display classifier의 좌/우 우선 route-family 귀속 결과다. 정성 평가는 display family가 아닌 full topology의 region reachability와 distinct-route signature를 사용해야 한다.

## 7. Synthetic failure fixture 설계

아래 fixture는 future pure evaluator용 topology fixture다. 역할·semantic·실제 경기 효과를 포함하지 않는다.

| Fixture | 최소 구조 | 기대되는 정성 결과 |
| --- | --- | --- |
| A 단일 중앙 bridge | defence→MC→forward만 존재 | complete route, regional dependency audit에서 MC 제거 시 all complete progression removed |
| B 좌 연결·우 고립 | 좌 defence→left midfield→forward, 우 node 무incident | 좌 progression present, 우 isolated node, 우 progression not detected |
| C 한 미드필더만 전방 연결 | 여러 origin이 하나의 MC에만 합류 | MC가 regional 또는 all-progression survival loss를 일으키는지 검증 |
| D 독립 두 path | left chain과 right chain이 connector를 공유하지 않음 | 둘 이상의 structurally distinct family, 하나 제거 시 반대 region progression survives |
| E 링크는 많지만 완결 없음 | support/recycle은 많고 forward terminal route 없음 | structurally interrupted 또는 no complete route detected; link count로 보정 금지 |
| F 전진은 있으나 outlet 없음 | deep→mid→forward, mid의 recycle/support edge 없음 | complete route present + mid fallback_not_detected |
| G wide progression·central access 없음 | left chain만 있고 centre와 adjacent lane path 없음 | left progression present, cross-region access not detected |
| H central structure·wide outlet 없음 | centre chain만 있고 wide node/route 없음 | central progression present, wide progression not detected |

fixture별 expectation은 boolean condition과 category만 검증한다. formation 점수나 통과 개수에 따른 overall grade는 만들지 않는다.

## 8. 사용자용 표현

* “수비선에서 전방까지 이어지는 구조적 진행 경로가 있습니다.”
* “왼쪽과 중앙 사이에 구조적으로 접근 가능한 경로가 확인됩니다.”
* “전진 경로의 대안은 있지만, 일부는 같은 중간 연결점을 공유합니다.”
* “이 연결점의 실제 의존 여부는 node 제거 뒤 경로 생존 검사가 필요합니다.”
* “전방 진입 경로는 있으나, 이 위치에서 되돌림 또는 같은 라인 지원 구조는 현재 확인되지 않습니다.”
* “역할 보정 근거는 예상 점유/수신의 설명이며, 구조 링크를 추가한 것은 아닙니다.”

피해야 할 표현은 “패스가 잘 된다”, “점유율이 높다”, “문제다”, “약점이다”, “이 선수가 반드시 공을 많이 받는다”다.

## 9. 향후 출력 schema 제안

```json
{
  "connectivity_evaluation": {
    "line_continuity": {"status": "continuous", "transitions": [], "limitations": []},
    "progression": {"status": "complete_route_present", "route_families": [], "limitations": []},
    "route_diversity": {"families": [], "alternatives": [], "limitations": []},
    "regional_connectivity": {"left": {}, "centre": {}, "right": {}},
    "cross_region_access": {"left_centre": {}, "centre_right": {}, "left_right_via_centre": {}},
    "support_recycle": {"nodes": [], "limitations": []},
    "connector_dependency": [],
    "structural_bottlenecks": [],
    "dead_ends": [],
    "isolated_nodes": [],
    "role_adjustments": [],
    "observations": [],
    "limitations": []
  }
}
```

각 status에는 source node/edge IDs와 configured position evidence를 포함해야 한다. role adjustment는 별도 evidence IDs만 포함하며 topology state를 덮어쓰지 않는다.

## 10. 오탐·누락 위험

* Position registry의 구조 후보는 실제 선수 간 거리, 압박, 능력, 지시 효과를 모른다.
* route survival은 node가 실제로 교체 불가능하다는 뜻이 아니라 configured topology에서의 대체 path만 검토한다.
* 같은 intermediate node가 있어도 다른 passing lane·역할 움직임은 현재 분리할 수 없다.
* Expected Role Space evidence가 없는 역할을 starting position대로만 표시해야 하며, 그 부재를 부정적 판단으로 바꾸면 안 된다.
* one-node terminal forward는 의도된 종점일 수 있어 dead end가 아니다.

## 11. 다음 구현 순서와 금지 항목

다음 단계는 production과 분리된 pure evaluator fixture에서 (1) line continuity, (2) route-family signature/deduplication, (3) node route-survival을 각각 검증하는 것이다. 그 뒤에만 read-only `connectivity_evaluation` 결과를 pipeline에 병렬 추가할지 결정한다.

이번 phase와 다음 prototype 전까지 구현하지 말아야 할 항목:

* 점수·등급·백분율·가중치
* shared connector를 병목/취약점으로 표시하는 UI
* role semantic으로 structural edge 생성·삭제
* partnership, penetration, chance creation, goal threat 결론
* display PRIMARY 수를 quality 입력으로 사용하는 평가
* production UI 재설계 또는 팀 지침 효과 모델

## 12. 검사한 파일과 Git 상태

검사 파일:

* `connectivity_engine_v2.py`
* `positional_relationships.py`
* `role_behaviours.py`
* `role_constraints.py`
* `test_connectivity_engine_v2.py`
* `web/static/js/connectivity_engine_v2.js`
* `web/static/app.js`
* `web/static/index.html`

Git working tree에는 이전 phase부터의 uncommitted 변경이 있다. 이 audit은 본 문서만 추가했고, commit/push는 수행하지 않았다.
