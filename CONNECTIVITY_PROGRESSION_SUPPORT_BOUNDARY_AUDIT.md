# Connectivity / Progression ↔ Support 경계 감사

동결 기준: Connectivity v2 `0a78ac98bb52c054b0edc2c9eb893beeffa1bcb5`, Progression `128e0708ba17560a2ecce19bf8b7c073d5ef5be5`
감사일: 2026-09-12
성격: **설계·읽기 전용 감사**. 이 문서는 Support evaluator, JavaScript evaluator, UI, 역할 데이터 또는 동결된 평가기 의미를 추가·수정하지 않는다.

## 1. Support의 정의와 소유 범위

Support의 고유 질문은 다음이다.

> 한 선수가 전술적 위치에서 공을 받은 뒤, 플레이를 이어 갈 구조적 후속 선택지가 그 위치 주변에 있는가?

이는 링크·경로의 개수, 패스 성공률, 점유 품질, 선수 능력, 역할 조합의 화학작용을 뜻하지 않는다. Support는 전역 포메이션을 한 번에 평가하지 않고, **수신 상태(receiving state)** 별 후속 구조를 설명해야 한다.

| 차원 | 고유 질문 | Support와의 경계 |
|---|---|---|
| Connectivity | 관련 구성 위치 사이에 구조적 연결이 가능한가? | 그래프·링크·완결 경로·fallback 존재의 소유자다. |
| Progression | 그 연결을 통해 어디까지 전진하는가? | 전진 이벤트·도달선·정체·전진 의존도의 소유자다. |
| Support | 수신 뒤 어떤 방향으로 이어 갈 구조가 있는가? | 기존 그래프를 읽되 링크·전진·경로를 새로 만들지 않는다. |

## 2. 현재 Connectivity 항목 감사

| 현재 항목 | 분류 | Support에서의 허용 재사용 |
|---|---|---|
| `structural_links` | A. Connectivity 소유 구조 사실 / B. 재사용 primitive | 수신 노드에서 나가는 후속 선택지 후보로만 사용한다. |
| `same_line_support` | A / B | 같은 점유 라인의 구조적 fallback 존재로만 사용한다. Support 품질 그 자체가 아니다. |
| `recycle` | A / B | 더 낮은 구성 위치로 되돌리는 선택지의 존재로만 사용한다. |
| `support_recycle` | A / B | 각 노드의 same-line·backward outlet을 읽기 전용 입력으로 사용한다. |
| `progression_routes` | A / B | 의미 있는 중간 수신 상태를 후보화하는 문맥이다. 경로 존재 결론은 복제하지 않는다. |
| `network_regions`, 지역 경로군 | A / B | 지역별 수신자의 후속 방향을 묶는 범위로만 사용한다. 지역 경로 존재 문구를 재사용하지 않는다. |
| `connector_dependency` | A | Support dependency로 자동 승계하지 않는다. |
| `isolated_nodes` | A | Support isolation과 같지 않다. 수신 가능 여부와 수신 후 선택지를 별도 판정해야 한다. |
| display plan, 원시 경로 수 | D. UI/debug | Support의 근거나 품질에 사용하지 않는다. |

Connectivity의 support/recycle은 “구조적 fallback 연결이 존재한다”는 사실이다. 이를 “지원이 좋다”, “압박을 잘 벗어난다”, “공을 지킨다”로 해석하지 않는다.

## 3. 현재 Progression 항목 감사

| 현재 항목 | 소유/Support 재사용 |
|---|---|
| advancement events | Progression 소유. 도착 노드를 Support receiving-state 후보로 제공할 수 있다. |
| route profiles | Progression 소유. `advance_then_support`의 순서 문맥으로만 사용한다. |
| regional advancement | Progression 소유. 해당 지역에서 실제 수신 상태가 후보인지 확인하는 문맥일 뿐 Support의 지역 결론이 아니다. |
| lateral transfer before advancement | Progression 소유. Support는 수신 뒤의 lateral option과 구분한다. |
| `advance_then_stall` | Support 검사 후보일 뿐 Support 실패가 아니다. 정체 지점에 recycle/lateral 후속 구조가 있을 수 있다. |
| progression dependency | Support dependency로 자동 승계하지 않는다. |
| highest reachable line | 맥락 정보일 뿐 Support 품질/등급의 근거가 아니다. |

따라서 **전진의 거리·도달선·라인 건너뜀은 Progression이 계속 소유**한다. Support는 “전방 후속 선택지가 있다”까지만 말할 수 있으며, 그 선택지가 최전방까지 얼마나 전진하는지는 말하지 않는다.

## 4. 수신 상태와 방향 분류

미래 Support의 최소 단위는 다음 조건 중 하나를 만족하는 구성 노드다.

1. 유효한 기존 structural link의 target으로 도달한 노드
2. 기존 structural/progression route의 의미 있는 중간 노드

후속 선택지는 receiver에서 출발하는 기존 structural link만 대상으로 한다. 화면 좌표를 사용하지 않고 `vertical_index`, `lateral_slot`, configured-position relation을 사용한다.

| Support 방향 | 안전한 구조적 정의 |
|---|---|
| forward | receiver보다 높은 점유 세로 라인으로 향하는 기존 link |
| lateral | 같은 점유 라인에서 인접한 lateral region으로 향하는 기존 link |
| recycle | receiver보다 낮은 점유 세로 라인으로 향하는 기존 link |
| inside / outside | receiver의 `left/centre/right`와 target의 상대 관계가 명시될 때만 기록 |

현재 위치 ontology는 `left`, `centre`, `right`만 전역적으로 보장한다. centre/half-space/wide를 동등한 세부 구획으로 보장하지 않는다. 따라서 half-space 또는 touchline을 일반적인 Support 방향으로 만들지 않으며, 검증된 ERS 항목이 있는 역할에 한해 역할 보정 문맥으로만 남긴다.

## 5. 수신 뒤 Support와 terminal 안전 규칙

**Post-reception Support**는 receiver에서 출발하는 forward/lateral/recycle 선택지의 구조적 조합을 설명한다.

- forward + lateral + recycle: 서로 다른 후속 구조 방향이 존재한다.
- recycle only: 뒤로 되돌리는 선택지에 집중된다.
- one continuation: 후속 연결이 한 방향에 집중된다.
- terminal endpoint: 완결 Connectivity route의 마지막 노드이고 configured forward band인 노드다.
- support-isolated: 아래의 엄격한 조건을 모두 충족할 때만 가능하다.

**Terminal endpoint rule:** `vertical_band == "forward"`이고 기존 complete route의 종점인 노드는, 더 높은 forward option이 없다는 이유만으로 Support isolation으로 표시하지 않는다. 이는 두 스트라이커 포메이션의 CF/ST에도 동일하게 적용한다.

**Support isolation rule:** receiver가 (a) 기존 link를 통해 수신 가능하고, (b) terminal endpoint가 아니며, (c) receiver에서 출발하는 forward·same-line/lateral·recycle의 의미 있는 구조 link가 하나도 없을 때만 `support_isolated` 후보가 된다. 이는 incident link가 전혀 없는 Connectivity `isolated_node`와 다른 개념이다.

## 6. 다양성·단일 선택지·의존도

원시 option/link 수는 Support 품질이 아니다. 미래 출력은 방향 조합을 기술적으로 서술한다.

- `forward + lateral + recycle`
- `forward + recycle`
- `lateral only`
- `recycle only`
- `single direction`
- `single_option_support`

두 개 링크가 있어도 같은 구조 방향이면 다양성이 늘지 않는다. 링크 수가 적어도 서로 다른 방향이면 그 사실만 기록한다. “좋음/나쁨/강함/약함”, 점수·등급은 사용하지 않는다.

**Support dependency**는 Connectivity 또는 Progression dependency를 자동 상속하지 않는다. receiver를 기준으로 노드 제거 전후를 비교해, 유일한 forward·lateral·recycle **방향 범주**가 사라질 때만 별도 기록할 수 있다. shared connector도 이 범주 손실이 입증되지 않으면 dependency가 아니다.

## 7. 지역 Support와 advance-then-support

지역 Support는 left/centre/right에 속한 수신 상태별로 다음만 기록한다: 후속 선택지가 같은 지역에 남는지, 다른 지역으로 전달되는지, forward/recycle/lateral 범주가 있는지, Support isolation 후보가 있는지, 특정 방향이 다른 지역 노드에 의존하는지.

`advance_then_support`의 미래 프로필은 Progression의 advancement receiver를 받아 다음을 함께 보일 수 있다.

```json
{
  "receiver_id": "IP:CM",
  "arrived_by_existing_advancement": true,
  "forward_continuation": [],
  "lateral_continuation": [],
  "recycle_continuation": [],
  "support_dependency": [],
  "terminal_endpoint": false,
  "limitations": []
}
```

이 구조는 `CB → CM`이 전진인지 여부를 다시 판단하지 않는다. Progression이 이미 정한 도착 receiver 뒤를 읽을 뿐이다.

## 8. 역할 semantic과 ERS 경계

모든 역할 semantic은 modifier-only다. baseline topology나 continuation link를 생성하지 않는다.

| 기존 검증 semantic | Support 관련 분류 | 제한 |
|---|---|---|
| `receive_between_lines`, `receive_centrally` | receiving-support modifier | 수신 위치 문맥을 보완할 뿐 실제 수신·link를 만들지 않는다. |
| `move_to_receive` | support-position modifier | 공을 받기 위한 이동 근거이며 수신 또는 배급을 증명하지 않는다. |
| `support_central_passing_links` | distribution-support modifier | 중앙 연결 보조의 역할 문맥이며 topology 변경 근거가 아니다. |
| `send_simple_pass`, `send_forward` | distribution-support modifier | 기존 outgoing option 설명에만 붙고, pass 성공·표적을 추론하지 않는다. |
| `hold_width`, `move_inside`, `open_space_for_fullback` | structural-space modifier | 역할별 예상 공간 문맥일 뿐 고정 좌표/새 구조 link가 아니다. |
| `attack_space_in_behind` | Support에 불충분 | Penetration 인접 문맥이며 Support continuation으로 승격하지 않는다. |

Configured Position은 baseline structural location이고, ERS는 검증된 expected occupation/reception/movement 해석이다. 미래 구조는 `BASE SUPPORT STRUCTURE + ROLE-ADJUSTED SUPPORT INTERPRETATION`으로 병렬 표기할 수 있지만 ERS가 노드 위치·링크·경로를 바꾸어서는 안 된다.

## 9. 다른 차원과의 경계

- **Partnerships:** Support는 receiver 주변의 구조를 묻는다. 역할쌍의 반복적 상호보완·화학작용·시너지는 다루지 않는다.
- **Penetration:** Support는 전방/측면 선택지의 존재까지만 말한다. 수비 블록 뒤·안쪽 위협은 Penetration의 미래 질문이다.
- **Chance Creation:** key pass, assist potential, chance quality를 말하지 않는다.
- **Player attributes / Team Instructions:** passing, vision, decision, technique, first touch, teamwork과 directness, tempo, width, build-up 등은 Support Phase 1 구조에 사용하지 않는다.

## 10. 합성 A–N 설계 fixture

| 사례 | 확인할 경계 |
|---|---|
| A | receiver에 forward + lateral + recycle가 있는 구조 |
| B | recycle only receiver |
| C | lateral only receiver |
| D | 정확히 하나의 continuation만 있는 receiver |
| E | 완결 경로의 terminal striker endpoint; isolation 아님 |
| F | non-terminal receiver가 수신 뒤 continuation 없음; support isolation 후보 |
| G | advancement receiver에 서로 다른 방향의 후속 구조 |
| H | midfield까지 전진했지만 recycle only; Progression 정체와 Support를 분리 |
| I | 가까운 단일 노드 제거로 유일 lateral 범주가 사라짐 |
| J | 많은 link가 하나의 방향에만 속함 |
| K | 더 적은 link가 여러 구조 방향에 걸침 |
| L | wide receiver가 centre에서만 지원받음 |
| M | centre receiver가 wide에서만 지원받음 |
| N | shared connector지만 방향 범주 손실이 없어 Support dependency 아님 |

triangle, diamond, third-man은 이번 구조로 생산 적용하지 않는다. 세 노드의 시각적 연결만으로는 순서·중간 receiver·그 뒤 continuation을 보장하지 않는다. 기존 route data는 구조적 순서를 일부 보관하지만, 실제 수신 순서와 공의 실행을 증명하지 않으므로 football concept으로 명명하지 않고 **deferred**한다.

## 11. 7개 프리셋 읽기 전용 관측

아래 수치는 현재 동결된 position-only graph의 방향별 구조 link·fallback 분류를 읽은 값이다. Support 등급이나 포메이션 순위가 아니다.

| 프리셋 | forward / same-line / recycle | terminal endpoint | 안전한 Support 설계 관찰 |
|---|---:|---|---|
| 4-2-3-1 | 15 / 8 / 15 | ST | 여러 fallback 유형이 있는 중간 수신 상태와 one-fallback 상태가 함께 존재한다. terminal ST는 자동 불이익 대상이 아니다. |
| 4-3-3 | 18 / 4 / 18 | ST | DM의 Progression dependency는 Support dependency를 뜻하지 않는다. 중앙 Progression 도달선은 Support 결론이 아니다. |
| 4-4-2 | 20 / 10 / 12 | CF, ST | 두 terminal forward는 terminal rule로 보호한다. 중앙의 complete regional route 부재는 지역 Support 부재로 재서술하지 않는다. |
| 4-2-4 | 18 / 6 / 14 | CF, ST | sparse band를 라인 건너뜀/Support 결손으로 확대하지 않는다. |
| 3-4-2-1 | 18 / 6 / 18 | ST | 윙백/중앙 수신자의 inside/outside는 configured relation이 있을 때만 설명한다. |
| 3-4-3 | 17 / 4 / 17 | ST | 중앙의 intermediate advancement는 Support 실패를 뜻하지 않는다. |
| 3-5-2 | 19 / 10 / 19 | CF, ST | wide/centre transfer는 Support 손실이 아니라 방향 범주로 분리 기록한다. |

각 프리셋의 `advance_then_stall`은 현재 빈 배열이다. 이는 Support가 모두 충족됐다는 결론이 아니라, 정체 지점이 future Support 검사의 후보로 생성되지 않았다는 뜻이다. 두 스트라이커 체계는 terminal forward가 두 개여도 자동 Support isolation으로 표시되지 않는다.

## 12. 미래 출력 스키마와 구현 순서

제안 스키마(비생산, 변경 가능):

```json
{
  "support_evaluation": {
    "receiving_states": [],
    "regional_support": {"left": {}, "centre": {}, "right": {}},
    "support_isolations": [],
    "single_option_receivers": [],
    "support_dependencies": [],
    "advance_then_support": [],
    "role_adjustments": [],
    "observations": [],
    "limitations": []
  }
}
```

권장 순서:

1. A–N 순수 fixture로 receiving-state, terminal, isolation, direction-category 계약을 먼저 고정한다.
2. frozen Connectivity v2 output만 받는 pure evaluator prototype을 분리한다.
3. Support-specific direction-category removal test를 추가해 dependency를 별도 검증한다.
4. Progression advancement receiver와 `advance_then_support` 문맥을 read-only로 연결한다.
5. evaluator 계약 뒤에만 사용자 문구/UI를 설계한다.

deferred: triangle/diamond/third-man 명명, role-pair 효과, 선수 능력, Team Instruction 효과, 실행 품질, 수비 압박 대응, Penetration/Chance Creation/Goal Threat, 점수·등급·순위.

## 13. 동결 기준 확인·검사 파일·Git 상태

Connectivity v2와 Progression의 production semantics, role catalogue/evidence, ERS, team-instruction effects, UI를 변경하지 않았다. Inspect 대상은 `connectivity_engine_v2.py`, `connectivity_qualitative_evaluator.py`, `progression_evaluator.py`, `positional_relationships.py`, `expected_role_space.py`, `connectivity_semantic_vocabulary.json`, `role_behaviours.py`, 기존 baseline·boundary report와 관련 tests다.

이 감사의 유일한 변경은 본 문서다. commit/push는 수행하지 않는다.
