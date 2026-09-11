# Progression Evaluator Acceptance Audit

## 1. 감사 범위

Progression Evaluator Phase 1이 frozen Connectivity v2의 기존 노드·방향 링크·경로·정성 경로 패밀리만 해석하는지 점검했다. 사용자용 UI, HTML, CSS, 점수, 팀 지침 효과, 선수 능력치 효과는 추가하지 않았다.

감사 중 지역별 최고 도달 라인의 실제 결함을 발견했다. 좌측에서 중앙 최전방으로 향하는 기존 링크가 `advancement_to_forward`인데 좌측 최고 도달 라인이 AML로 남아 상태와 충돌했다. 지역에서 시작한 전진 이벤트의 도착 노드를 최고 도달 계산에 포함하도록 Python/JS에 동일한 최소 수정을 적용했다. Connectivity 파일은 변경하지 않았다.

## 2. 7개 프리셋 결과

| 포메이션 | 점유 라인 | 연속성 | 전체 최고 라인 | 좌/중/우 상태 | 스킵 | 정체 | 의존성 | 프로필/원시 경로 |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| 4-2-3-1 | GK, 수비, DM, AM, FW | continuous | forward | F/F/F | 0 | 0 | 없음 | 12/16 |
| 4-3-3 | GK, 수비, DM, CM, AM, FW | continuous | forward | F/I/F | 4 | 0 | DM | 36/48 |
| 4-4-2 | GK, 수비, CM, FW | continuous | forward | F/I/F | 0 | 0 | 없음 | 12/32 |
| 4-2-4 | GK, 수비, CM, AM, FW | continuous | forward | F/I/F | 4 | 0 | 없음 | 12/32 |
| 3-4-2-1 | GK, 수비, WB, CM, AM, FW | continuous | forward | F/F/F | 4 | 0 | 없음 | 22/25 |
| 3-4-3 | GK, 수비, WB, CM, AM, FW | continuous | forward | F/I/F | 4 | 0 | 없음 | 16/20 |
| 3-5-2 | GK, 수비, WB, CM, FW | continuous | forward | F/F/F | 2 | 0 | 없음 | 18/40 |

`F`는 해당 지역에서 시작한 구조적 전진이 forward에 도달함, `I`는 중간 점유 라인까지만 도달함을 뜻한다. 순위나 품질 평가는 포함하지 않는다.

## 3. 4-4-2 및 4-2-4 희소 라인 검증

4-4-2의 점유 순서는 `0 → 1 → 4 → 6`이다. 수비→중원과 중원→최전방은 각각 canonical band 차이가 아니라 점유 순서상 인접하므로 모두 gain 1이며, 실제 출력에서 line skip은 0개였다. 4-2-4도 수비→중원은 gain 1이다. 합성 C는 중원이 점유된 상태에서 수비→최전방 직결을 gain 2, 중원 스킵으로 확인했다. 합성 D는 canonical 번호 차이가 있어도 중간 점유 라인이 없으면 skip이 아님을 확인했다.

## 4. 라인 스킵 감사

모든 프리셋의 보고된 skip은 source/target 사이에 실제 `occupied_lines` 인덱스가 존재하는 경우만 기록됐다. 4-3-3, 4-2-4, 3백 프리셋의 skip 대상은 CM·AM·수비 라인처럼 실제 점유된 라인이다. display 좌표와 CSS 좌표는 evaluator에서 참조하지 않는다. false positive는 발견하지 못했다.

## 5. Advance-then-stall 감사

7개 프리셋에는 stall이 없었다. 합성 H는 수비→중원 전진 후, 중원에서 뒤로 되돌리는 링크만 있을 때만 stall을 기록했다. 해당 수신 위치는 forward가 아니고 이후 forward 링크가 없으며, recycle은 전진으로 계산되지 않는다. 합성 A는 연결된 support/recycle 구조이지만 전진이 없으므로 stall이 아니다. forward 종점은 stall에서 제외된다.

## 6. Progression dependency 및 shared connector

4-3-3의 `IP:DM`만 제거 시 `all_forward_line_access_removed`와 `highest_reachable_line_reduced`가 실제로 발생해 dependency로 기록됐다. 다른 프리셋에는 dependency가 없었다. 합성 K는 공유 중간 노드가 있어도 우회 경로가 남으므로 dependency가 없고, 합성 L은 제거 시 forward 접근이 사라져 dependency가 기록됐다. 경로 참여 빈도는 dependency 근거로 사용하지 않는다.

## 7. 경로 패밀리·지역·측면 전환

프로필은 raw route 수가 아니라 기존 qualitative route family를 우선 사용한다. 예를 들어 3-5-2는 원시 40개 경로를 18개 프로필로, 4-4-2는 32개를 12개로 표현했다. 더 많은 프로필이나 경로를 장점으로 해석하지 않는다.

같은 라인에서 좌/중/우로 향하는 support는 advancement event가 아니다. 합성 G는 명시적인 교차 지역 support가 첫 전진 구조에 선행할 때만 `lateral_transfers_before_advancement: 1`을 기록했다. 현재 frozen 구조만으로 해당 전환이 반드시 필요하다고 증명할 수 없는 경우 `requires_transfer_from_another_region`은 `null`로 유지한다.

## 8. 최고 도달 라인과 역할 조정

전체·지역 최고 도달 라인은 configured `vertical_index`와 기존 directed structural link만 사용한다. forward는 품질 등급이 아니다. Leicester에서는 검증된 `send_forward`, `receive_between_lines`, `receive_centrally`, `advance_to_attacking_midfield`, `move_into_halfspace`, `move_inside`, `attack_space_in_behind`만 설명용 modifier로 출력됐다. 이들은 링크·라인 이득·스킵·점유 라인을 만들거나 제거하지 않는다. half-space는 명시적 `move_into_halfspace` semantic이 있는 경우만 표시된다. ERS는 baseline topology와 분리돼 있다.

## 9. 합성 A–L

A 연결은 있으나 전진 없음, B 단계적 전진, C 실제 스킵, D 비스킵 canonical 간격, E 좌측 전진, F 중앙 전진, G 측면 전환 후 전진, H 전진 후 정체, I 동일 프로필로 경로 중복 축약, J 구별되는 프로필, K 공유 연결자 비의존, L 제거로 증명된 의존성을 모두 통과했다.

## 10. 경계와 회귀

Progression은 penetration, chance creation, goal threat, possession quality, pass success, press resistance, 경기 성과를 주장하지 않는다. Connectivity v2 baseline은 다음처럼 유지됐다.

| 4-2-3-1 | 4-3-3 | 4-4-2 | 4-2-4 | 3-4-2-1 | 3-4-3 | 3-5-2 |
| --- | --- | --- | --- | --- | --- | --- |
| 38/16 | 40/48 | 42/32 | 38/32 | 42/25 | 38/20 | 48/40 |

정렬은 Python과 JavaScript 모두에서 occupied lines, profiles, skip, dependency, observations, role adjustments에 대해 결정적으로 처리되며 Python/JS parity로 확인했다.

## 11. 변경 파일과 검사

수정: `progression_evaluator.py`, `web/static/js/progression_evaluator.js`, `test_progression_evaluator.py`.

추가 보고서: 이 파일. 기존 Phase 1 보고서와 boundary audit 문서는 untracked 상태로 유지된다. 커밋과 push는 하지 않았다.

- 전체 unittest: 223 passed
- self-test: passed
- Python/JS parity: Leicester, 합성 A–L, 7개 프리셋 passed
- static browser runner: passed
- JavaScript syntax check: passed
- `git diff --check`: passed

READY_FOR_PROGRESSION_UI
