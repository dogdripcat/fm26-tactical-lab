# Team Instruction Evidence Recovery v1

기준: 프로젝트 내부의 사용자 인게임 evidence registry, 현재/이전 카탈로그, 전술 유형 자료와 테스트 fixture만 읽기 전용으로 대조했다. FM24 자료나 역할명·전술 유형명으로 선택값을 추론하지 않았다.

## 결과

- 감사 카테고리: partial 22개 (IP 14, OOP 8)
- 새로 복구한 선택값: 0개
- complete로 승격한 카테고리: 없음
- 유지: complete 5개, partial 22개
- `미설정`: UI 전용 상태이며 selectable value가 아님

현재 evidence registry의 `USER_FM26_IP_TEAM_INSTRUCTIONS_001`, `USER_FM26_OOP_TEAM_INSTRUCTIONS_001`, `USER_FM26_IP_TEAM_INSTRUCTIONS_002`, `USER_FM26_TEAM_INSTRUCTION_OPTION_SETS_001`은 이미 해당 선택값의 provenance/source reference로 연결돼 있다. 전술 유형 자료에는 추가 선택값의 읽을 수 있는 원문 전사가 없었다.

## Partial 카테고리 감사

| 국면 | category id | 현재 확인된 선택값 | 근거 | 추가 복구 | 남은 상태 |
| --- | --- | --- | --- | --- | --- |
| IP | time_wasting | 덜 자주 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | attacking_transition | 연속 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | creativity | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | build_up_tactic | 압박 돌파 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | goal_kick | 짧게 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | goalkeeper_distribution | 센터백 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | attacking_involvement | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | dribbling | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | progression | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | passing_style | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | patience | 보통 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | long_shots | 균형 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | cross_style | 낮은 크로스 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| IP | goalkeeper_distribution_speed | 빠르게 배급하라 | USER_FM26_IP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | defensive_line | 보통 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | pressing_execution | 더 자주 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | defensive_transition | 역압박 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | tackling | 강하게 태클하라 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | cross_play | 균형 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | pressing_trap | 균형 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | goalkeeper_short_distribution | 예 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |
| OOP | defensive_line_action | 더 높은 위치로 | USER_FM26_OOP_TEAM_INSTRUCTIONS_001 | 없음 | partial / 그 외 선택값 unknown |

## Complete 카테고리 유지

`passing_directness`, `tempo`, `attacking_width`, `pressing_line`은 `USER_FM26_TEAM_INSTRUCTION_OPTION_SETS_001`로, `set_piece_inducement`는 `USER_FM26_IP_TEAM_INSTRUCTIONS_002`로 현재 전체 선택 집합을 뒷받침한다. 이번 감사에서는 이 집합을 확장하거나 효과 모델을 추가하지 않았다.
