# Support Evaluator Acceptance Audit

## 1. 범위와 최종 정의

본 감사는 Support Phase 1 evaluator의 수용성만 다룬다. Support는 **기존 구조 링크로 수신한 위치에서, 그 뒤에 남는 구조적 continuation을 설명**한다. Connectivity는 receiver까지의 구조적 도달 가능성, Progression은 그 연결로의 전진과 도달선을 계속 소유한다.

Support 출력은 route existence, highest reachable line, 원시 링크/경로 수를 Support 결론으로 재진술하지 않는다. 점수·등급·포메이션 순위·선수 실행 성공·찬스/득점 주장은 없다.

## 2. 수신 상태와 post-reception 경계

`receiving_states`는 기존 structural link target 또는 기존 complete route의 중간 노드만 수집한다. ID는 정렬·중복 제거되고 각 profile의 `configured_position`, band, region은 동일 Connectivity node에서 온다. 역할 semantic만으로 receiver를 만들지 않는다.

수신을 증명하는 inbound link는 그 receiver의 후속 continuation으로 재사용하지 않는다. 예를 들어 `CB → CM`은 CM 수신만 증명하며, CM에서 출발하는 별도 link가 없으면 CM의 forward/lateral/recycle support는 비어 있다. 역방향 및 잘못 표기된 synthetic link도 위치 index를 재확인하므로 forward/recycle/lateral로 오분류되지 않는다.

## 3. continuation 분류

- **primary direction:** `forward`, `lateral`, `recycle`만 direction diversity와 dependency 손실 범주에 사용한다.
- `forward`: receiver보다 높은 configured occupied line으로 가는 기존 link.
- `lateral`: 같은 occupied line의 기존 same-line support link.
- `recycle`: receiver보다 낮은 configured occupied line으로 가는 기존 link.
- **relational descriptor:** `inside`, `outside`는 wide→centre / centre→wide의 position relation을 설명할 뿐, 별도 physical continuation·direction diversity·dependency category가 아니다.

display 좌표, half-space, underlap/overlap, diagonal occupation을 도입하지 않았다. cross-region support도 progression quality나 width quality로 표현하지 않는다.

## 4. terminal endpoint와 Support isolation

terminal endpoint는 세 조건을 모두 충족할 때만 true다: (1) 현재 가장 높은 configured occupied line, (2) `forward` band, (3) complete Connectivity route의 종점. no-forward-option만으로 terminal이 되지 않는다.

따라서 lone striker, CF/ST two-striker, forward-band wide endpoint는 continuation이 없더라도 terminal로 보호된다. terminal은 lateral/recycle을 가질 수도, 하나도 없을 수도 있으며 이 경우 Support quality를 판정하지 않는다. 반대로 striker 아래의 AM, 가장 높은 CM, sparse-formations의 non-forward highest receiver는 terminal 보호를 받지 않는다.

`support_isolated`는 수신 가능하고, terminal이 아니며, 어떠한 primary continuation도 없는 receiver만 뜻한다. 이는 Connectivity `isolated_node`와 다르다. Connectivity isolated/unreachable node는 normal receiving-state isolation으로 바꾸지 않는다.

## 5. single option, diversity, dependency

`single_option_support`는 **고유한 outgoing structural link가 정확히 하나**일 때 true다. 하나의 wide→centre same-line link가 `lateral`과 `inside` 설명을 함께 갖더라도 하나의 physical option이다. two forward targets는 direction diversity 하나지만 single option은 false다.

direction diversity는 primary direction의 존재 집합이다. three forward target은 하나의 primary direction이며, forward+lateral+recycle은 세 primary directions이다. 원시 link count를 quality 또는 diversity로 사용하지 않는다.

Support dependency는 candidate support node 제거 후 해당 receiver가 잃는 primary category 또는 새 support isolation을 비교해 별도로 입증한다. self-removal은 candidate에서 제외한다. Connectivity/Progression dependency, shared connector, route frequency, role explanation 변화는 상속 근거가 아니다.

## 6. advance-then-support, stall, 지역

`advance_then_support`는 Progression route-profile의 기존 advancement event target만 소비한다. Support는 prior edge가 advancement인지 재계산하지 않고, 도착 뒤 continuation·terminal·isolation·독립 dependency만 표시한다.

Progression `advance_then_stall`은 Support inspection 대상일 뿐 자동 Support failure가 아니다. stalled receiver에 lateral/recycle continuation이 있을 수 있고 terminal endpoint도 가능하다.

`regional_support`는 left/centre/right receiver 배열과 forward/lateral/recycle 보유자, isolation, single-option, cross-region relation만 집계한다. 지역 route 존재나 formation-wide link count를 재표현하거나 지역을 순위화하지 않는다.

## 7. 역할 semantic과 ERS

현재 적용 semantic은 verified evidence가 있는 `receive_between_lines`, `receive_centrally`, `move_to_receive`, `support_central_passing_links`, `send_simple_pass`, `send_forward`, `hold_width`, `move_inside`, `open_space_for_fullback`이다.

| semantic 유형 | Support 해석 |
|---|---|
| receiving | receiver 설명 보정 |
| move-to-receive | support-position 보정 |
| send/simple/central links | distribution-support 보정 |
| width/move-inside/open-space | structural-space 보정 |

각 semantic은 evidence ID를 유지하는 역할 설명일 뿐 structural option, terminal, isolation, dependency, direction diversity를 변경하지 않는다. ERS도 configured-position topology를 이동시키거나 inside/outside/forward option을 만들지 않는다.

## 8. 합성 A–W 수용성 결과

| 사례 | 결과 |
|---|---|
| A–D | forward+lateral+recycle, recycle-only, lateral-only, single structural option을 검증. |
| E–F | lone/two-striker terminal 보호와 non-terminal isolation을 검증. |
| G–H | advancement receiver의 다방향 continuation과 recycle-only 후속 구조를 검증. |
| I | 유일 lateral support node 제거로 primary lateral category 손실을 검증. |
| J–K | 많은 same-direction link와 적은 다방향 link를 raw count와 분리. |
| L–M | wide↔centre relation을 inside/outside descriptor로만 검증. |
| N | shared connector가 category loss 없이 dependency가 아님을 검증. |
| O–P | Connectivity/Progression dependency가 Support dependency로 자동 상속되지 않음을 검증. |
| Q | node removal이 receiver isolation을 만드는 실제 Support dependency를 검증. |
| R–S | lateral+inside의 동일 target은 primary lateral 하나이며, two forward targets도 primary forward 하나임을 검증. |
| T–U | zero-continuation terminal과 non-forward highest CM을 검증. |
| V–W | progression stall receiver의 lateral/recycle 후속 구조는 Support failure와 동치가 아님을 fixture 규칙으로 검증. |

## 9. 확정된 버그와 최소 수정

**발견된 문제:** 초기 Phase 1은 `inside`/`outside`를 `support_directions`에 넣고 dependency의 lost category에도 포함했다. 예를 들어 same physical link가 `lateral + inside`이면 두 independent continuation처럼 보일 수 있었다.

**위반 규칙:** inside/outside는 relational descriptor이며 primary direction이 아니다.

**수정:** Python과 JavaScript에서 `support_directions` 및 dependency comparison을 `forward/lateral/recycle`으로 제한했다. `support_options.inside/outside`는 provenance 설명으로 유지했다. 이어서 동일 edge, two-forward-target, malformed label, reversal, self-removal 회귀를 추가했다. Connectivity/Progression에는 수정이 없다.

## 10. 7개 프리셋과 동결 회귀

7개 preset에서 receiving state 11개가 결정적으로 생성됐다. 4-4-2·4-2-4·3-5-2의 CF/ST는 모두 terminal endpoint로 처리되며 false isolation이 없다. 모든 preset에서 Support isolation과 single-option receiver는 빈 배열이다. 이 사실은 구조적 관측이며 전술 평가나 우열이 아니다.

Connectivity baseline은 그대로다: 4-2-3-1 `38/16`, 4-3-3 `40/48`, 4-4-2 `42/32`, 4-2-4 `38/32`, 3-4-2-1 `42/25`, 3-4-3 `38/20`, 3-5-2 `48/40`.

Progression의 occupied-line advancement/gain/skip, regional highest line, advance-then-stall, progression dependency는 기존 회귀로 유지했다.

## 11. 한계와 변경 파일

Support는 pass success, possession safety, press resistance, player attributes, Team Instruction effects, third-man/triangle/diamond, Partnerships, Penetration, Chance Creation, Goal Threat를 모델링하지 않는다. Support UI도 없다.

변경: `support_evaluator.py`, `web/static/js/support_evaluator.js`, `core/pipeline.py`, `web/static/js/tactic_analysis.js`, `test_support_evaluator.py`, parity runner와 Phase 1/본 acceptance report. Frozen Connectivity/Progression production code는 변경하지 않았다.

## 12. 검사와 Git 상태

전체 unittest **238 passed**, self-test 통과, Python↔JavaScript parity 통과, static browser runner 통과, JavaScript syntax 통과, `git diff --check` 통과를 확인했다. 요청대로 commit/push는 수행하지 않는다.

READY_FOR_SUPPORT_UI
