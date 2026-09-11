# Connectivity v2 Qualitative Evaluator Phase 1

## 1. 아키텍처와 pipeline 연결

새 evaluator는 `connectivity_engine_v2`의 출력만 읽는 순수 계층이다.

```text
configured tactic → Connectivity v2 full topology → qualitative evaluator → JSON result
```

`structural_links`, `progression_routes`, display priority, role evidence와 역할 데이터는 mutation하지 않는다. Python pipeline에는 기존 `connectivity`, `connectivity_v2`를 유지한 채 `connectivity_evaluation`을 병렬 추가했다. browser/static도 같은 순서로 실행하며, public UI는 바꾸지 않았다.

## 2. Line continuity

정렬된 occupied vertical index의 매 인접 쌍에 forward structural link가 하나 이상 있는지 확인한다.

* 전부 존재: `continuous`
* 일부만 존재: `partial`
* 하나도 없거나 complete route가 없는 구조: `interrupted`

DM과 AM 같은 명명된 line을 요구하지 않으므로 defence→midfield→forward와 defence→DM→AM→forward를 같은 원리로 처리한다.

## 3. Route family와 regional progression

raw route는 다음 topology signature로만 family화한다.

* 첫 non-centre lane으로 구한 origin region
* lane 점유가 가장 큰 dominant region
* 마지막 non-centre lane으로 구한 final region
* occupied-line sequence
* 시작과 종점을 제외한 ordered major connector

같은 signature의 수비수 출발 또는 forward 종점 변형은 한 family의 raw alternative다. raw route count와 family count는 `debug`에만 있으며 품질 판단에 사용하지 않는다.

`regional_connectivity`는 좌·중앙·우마다 `no_complete_regional_route_detected`, `complete_route_present`, `multiple_structurally_distinct_route_families` 중 하나를 출력한다. shared connector는 계속 구조적 사실일 뿐 dependency가 아니다.

## 4. Route survival, dependency, bottleneck

전진 route의 중간 node마다 node와 incident edge를 제거하고 complete progression family를 다시 계산한다.

* `no_meaningful_impact`: 각 기존 region의 complete progression이 남음
* `removes_one_alternative`: 일부 family는 사라져도 각 region에는 완결 경로가 남음
* `regional_progression_removed`: 기존 region 하나 이상이 완결 경로를 잃음
* `all_complete_progression_removed`: 모든 complete progression이 사라짐

마지막 두 상태만 evaluator의 `structural_bottlenecks`에 기록한다. `regional_structural_bridge` 또는 `critical_structural_bridge`는 configured topology의 node-removal 결과이며, 전술적 취약점이나 실제 경기의 선수 대체 불가능성을 뜻하지 않는다.

## 5. Support/recycle, dead-end, isolation

전진 route의 비종점 node에서 backward recycle edge 또는 same-line support edge를 검사해 `multiple_fallback_types`, `one_fallback_type`, `fallback_not_detected`를 출력한다. 이는 볼 보유·압박 저항·패스 성공을 추정하지 않는다.

dead-end 후보는 reachable한 중앙 non-forward relay node에만 제한하고, complete progression route·forward/support/recycle escape가 모두 없을 때만 만든다. configured forward endpoint와 wide node는 이 안전 규칙에서 제외한다. isolation은 incident structural link가 전혀 없는 configured node만 의미한다.

## 6. Cross-region access와 role modifier 경계

기존 structural links에서 방향성 path를 찾아 left→centre, centre→left, centre→right, right→centre를 기록한다. far-side는 left↔right path가 centre를 실제로 경유할 때만 `via_centre` 결과로 기록한다.

검증된 role semantic은 `role_adjustments`에서만 사람 친화적 근거로 표시한다. 예: 중앙 이동 근거, 하프스페이스 이동 근거, 폭 유지 근거. 이 해석은 baseline edge를 추가·삭제·강화하지 않으며, evidence 부재도 baseline 결과를 낮추지 않는다.

## 7. Synthetic fixture 검증

| Fixture | 검증 결과 |
| --- | --- |
| A 단일 중앙 bridge | MC 제거 시 `all_complete_progression_removed`와 `critical_structural_bridge` |
| B 좌 연결 / 우 고립 | 오른쪽 node만 `isolated_configured_node` |
| C 한 미드필더만 전방 연결 | MC 제거의 all-progression survival loss |
| D 독립 두 path | 좌·우 regional complete progression이 분리되어 유지 |
| E 링크는 많고 완결 없음 | `no_complete_route_detected` |
| F 전진·되돌림 없음 | 중간 node `fallback_not_detected` |
| G wide progression·central access 없음 | left→centre `access_not_detected` |
| H central progression·wide outlet 없음 | 좌·우 regional route `not detected` |

별도 fixture는 shared connector가 independent central alternative가 있을 때 `removes_one_alternative`일 뿐 bottleneck이 아님을 검증한다.

## 8. 7개 preset 결과

아래 값은 position-only topology의 설명용 상태다. formation 순위가 아니며 raw route 수는 user-facing quality에 사용하지 않는다.

| Formation | continuity | region progression | debug: raw/family | strict bridge 후보 | dead end / isolated |
| --- | --- | --- | --- | ---: | --- |
| 4-2-3-1 | continuous | 좌·중앙·우 multiple family | 16 / 12 | 3 | 0 / 0 |
| 4-3-3 | continuous | 좌·중앙·우 multiple family | 48 / 36 | 1 | 0 / 0 |
| 4-4-2 | continuous | 좌·우 multiple family, 중앙 미검출 | 32 / 12 | 0 | 0 / 0 |
| 4-2-4 | continuous | 좌·우 multiple family, 중앙 미검출 | 32 / 12 | 2 | 0 / 0 |
| 3-4-2-1 | continuous | 좌·중앙·우 multiple family | 25 / 22 | 4 | 0 / 0 |
| 3-4-3 | continuous | 좌·중앙·우 multiple family | 20 / 16 | 5 | 0 / 0 |
| 3-5-2 | continuous | 좌·중앙·우 multiple family | 40 / 18 | 2 | 0 / 0 |

“중앙 미검출”은 현재 signature의 dominant region으로 complete family가 분류되지 않았다는 뜻이며, 중앙 전술이 없거나 더 나쁘다는 판정이 아니다.

## 9. Python / JS parity와 회귀

`qualitative_parity_runner.mjs`로 Leicester, 4-3-3, 4-4-2, 3-4-2-1 fixture에서 Python `connectivity_v2 + connectivity_evaluation`과 browser 결과의 완전 동등성을 검증한다. 기존 display priority·occupied-line repair·legacy Connectivity를 변경하지 않았다.

## 10. 변경 파일

* `connectivity_qualitative_evaluator.py`
* `web/static/js/connectivity_qualitative_evaluator.js`
* `core/pipeline.py`
* `web/static/js/tactic_analysis.js`
* `web/static/js/qualitative_parity_runner.mjs`
* `test_connectivity_qualitative_evaluator.py`

## 11. 알려진 한계와 미구현 범위

node survival은 위치 topology의 대체 path만 검사한다. 선수 능력, 역할 움직임의 실제 실행, 상대 압박, 팀 지침, 패스 성공, chance creation과 경기 결과는 포함하지 않는다. edge-removal survival, partnership 평가, overall score/grade, public summary UI 재설계는 구현하지 않았다.

## 12. Git 상태

이번 phase에서 commit과 push는 수행하지 않았다.
