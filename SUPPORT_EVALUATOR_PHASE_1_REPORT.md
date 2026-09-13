# Support Evaluator Phase 1

## 1. 아키텍처와 입력 경계

`support_evaluator.py`와 `web/static/js/support_evaluator.js`는 normalization → role resolution → frozen Connectivity v2 → Connectivity qualitative evaluation → frozen Progression → Support 순서의 마지막 읽기 단계다. `core/pipeline.py`와 정적 `tactic_analysis.js`에는 `support_evaluation`만 병렬 추가했다.

Support는 기존 `connectivity_v2.structural_links`를 새로 계산하지 않고 소비한다. Progression의 기존 route-profile advancement event는 `advance_then_support`의 receiver 문맥으로만 소비한다. 따라서 Connectivity의 topology·route existence·dependency와 Progression의 line gain·line skip·highest reachable line·stall·dependency 의미는 변경하지 않았다.

## 2. 수신 상태와 post-reception Support

수신 상태는 기존 structural link의 target이거나 기존 complete route의 중간 노드인 configured position이다. 각 profile에는 inbound link context, configured position, band, region, terminal 상태와 receiver에서 출발하는 후속 선택지가 있다.

`forward`는 더 높은 점유 라인으로 향하는 기존 link, `recycle`은 더 낮은 라인으로 향하는 기존 link, `lateral`은 기존 same-line support link다. `inside`와 `outside`는 left/centre/right ontology가 명확한 경우에만 wide→centre 또는 centre→wide 관계로 병렬 기록한다. 화면 좌표·half-space 추정은 사용하지 않는다.

이 방향들은 continuation category이지 Support 품질이나 점수가 아니다. 같은 방향 link가 여러 개여도 direction diversity가 늘지 않는다. `single_option_support`는 고유한 후속 link가 정확히 하나일 때만 true다.

## 3. terminal, isolation, dependency

terminal endpoint의 결정 규칙은 다음 세 조건의 동시 충족이다: configured forward band, 현재 가장 높은 점유 라인, 기존 complete Connectivity route의 종점. 따라서 lone striker, two-striker CF/ST, forward band의 wide endpoint는 더 높은 forward option이 없다는 이유만으로 support-isolated가 되지 않는다. terminal endpoint도 lateral/recycle option은 별도로 보존한다.

`support_isolated`는 수신 가능하고 terminal이 아니면서 forward/lateral/recycle/inside/outside 중 어느 후속 structural option도 없는 receiver만 뜻한다. 이는 incident link 자체가 없는 Connectivity `isolated_node`와 다르다.

Support dependency는 receiver의 target node를 하나 제거한 뒤 기존 continuation category가 사라지거나 receiver가 support-isolated가 되는지를 비교해 별도로 입증한다. Connectivity dependency, Progression dependency, shared connector, route 참여 횟수는 자동 근거가 아니다.

## 4. advance-then-support, 지역, 역할 보정

`advance_then_support`는 Progression이 이미 확정한 advancement event의 target receiver에서만 생성한다. prior edge가 전진인지 다시 판정하지 않고, 그 뒤 forward/lateral/recycle continuation, direction diversity, terminal/isolation, Support dependency만 기록한다.

`regional_support`는 left/centre/right별 receiver ID와 각 direction category 보유자, isolation/single-option receiver, cross-region support 존재를 배열/boolean으로 제공한다. route existence나 raw count를 지역 품질로 표현하지 않는다.

검증된 role semantic은 `receiving_support_interpretation`, `distribution_support_interpretation`, `support_position_interpretation`, `structural_space_interpretation`으로 표시할 수 있다. `receive_between_lines`, `receive_centrally`, `move_to_receive`, `support_central_passing_links`, `send_simple_pass`, `send_forward`, `hold_width`, `move_inside`, `open_space_for_fullback`만 해당한다. 모두 modifier-only이며 link, dependency, terminal status, topology를 만들거나 삭제하지 않는다. ERS도 configured position을 이동시키지 않는 병렬 해석이다.

## 5. 합성 A–Q 및 terminal 테스트

테스트는 다음 경계를 검증한다.

- A–D: forward/lateral/recycle 구조 방향, recycle-only, lateral-only, single-option.
- E–F: lone striker와 two-striker terminal endpoint, non-terminal support isolation.
- G–N: advancement receiver의 다방향 후속 구조, centre↔wide support, shared connector 비자동 dependency.
- O–Q: Connectivity/Progression dependency 비상속, category removal로 입증된 Support dependency, isolation 변화.
- terminal 특수 사례: lone striker, CF/ST two-striker, forward-band endpoint, endpoint의 lateral/no-support 경우를 fixture에서 검증한다. advanced midfield는 forward-band endpoint가 아니므로 terminal 규칙을 받지 않는다.

third-man, triangle, diamond, role-pair synergy는 구현하지 않았다.

## 6. 7개 프리셋 읽기 전용 관측

| 프리셋 | receiving states | terminal endpoint | Support isolation | single option | advance-then-support | Support dependencies |
|---|---:|---|---|---|---:|---:|
| 4-2-3-1 | 11 | ST | 없음 | 없음 | 15 | 21 |
| 4-3-3 | 11 | ST | 없음 | 없음 | 18 | 16 |
| 4-4-2 | 11 | CF, ST | 없음 | 없음 | 16 | 14 |
| 4-2-4 | 11 | CF, ST | 없음 | 없음 | 14 | 16 |
| 3-4-2-1 | 11 | ST | 없음 | 없음 | 18 | 16 |
| 3-4-3 | 11 | ST | 없음 | 없음 | 17 | 17 |
| 3-5-2 | 11 | CF, ST | 없음 | 없음 | 16 | 13 |

모든 프리셋에서 지역별 cross-region support 가능 구조가 관측되지만, 이는 구조적 category 사실일 뿐 전술 우열·실행 성공·지원 품질을 뜻하지 않는다. terminal forward가 하나 또는 둘인 포메이션은 그 사실만으로 불이익을 받지 않는다.

## 7. 동결 회귀와 parity

Connectivity topology는 그대로다: 4-2-3-1 `38/16`, 4-3-3 `40/48`, 4-4-2 `42/32`, 4-2-4 `38/32`, 3-4-2-1 `42/25`, 3-4-3 `38/20`, 3-5-2 `48/40`.

Progression의 occupied-line gain, true occupied-line skip, regional highest line, advance-then-stall, progression dependency 계약도 기존 테스트로 유지했다. Python/JavaScript Support 결과는 synthetic fixture, 7개 프리셋, Leicester sample에서 일치한다.

## 8. 제한과 비범위

Support는 pass success, possession safety, press resistance, player attributes, Team Instruction 효과, third-man/combination pattern, Partnerships, Penetration, Chance Creation, Goal Threat를 모델링하지 않는다. score, grade, formation ranking, UI panel도 만들지 않았다.

## 9. 변경 파일과 테스트

- `support_evaluator.py`
- `web/static/js/support_evaluator.js`
- `web/static/js/support_parity_runner.mjs`
- `core/pipeline.py`
- `web/static/js/tactic_analysis.js`
- `test_support_evaluator.py`
- `SUPPORT_EVALUATOR_PHASE_1_REPORT.md`

후속 acceptance audit에서 primary direction과 inside/outside descriptor를 분리한 뒤 전체 unittest **238 passed**, self-test 통과, Python↔JavaScript parity 통과, static website runner 통과, JavaScript syntax check 통과, `git diff --check` 통과를 확인했다. commit/push는 수행하지 않는다.
