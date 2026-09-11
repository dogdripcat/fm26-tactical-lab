# Connectivity v2 Progression Model Repair Audit

## 결론

4-4-2의 0 progression route는 role evidence와 무관한 **structural link generation의 결함**이다. route traversal은 AM/DM band를 요구하지 않는다. 다만 defensive line(1)에서 midfield(4)으로 향하는 모든 candidate가 absolute `abs(vertical delta) <= 2` 조건에서 먼저 제거되므로, traversal에 전달될 forward edge가 없다.

일반적인 후보 수리는 `occupied-line adjacency`다. 이 문서는 그 후보를 source를 수정하지 않고 모의 계산했으며, 지침의 “REPORT FIRST”에 따라 아직 구현하지 않는다.

## 1. 4-4-2 정확한 추적

Configured positions는 `GK, LB, LCB, RCB, RB, ML, MCL, MCR, MR, ST, CF`다.

| Position group | family | vertical band/index | lane |
| --- | --- | --- | --- |
| GK | goalkeeper | goalkeeper / 0 | centre |
| LB, LCB | full_back, centre_back | defensive_line / 1 | left |
| RCB, RB | centre_back, full_back | defensive_line / 1 | right |
| ML, MCL | wide_midfield, midfield | midfield / 4 | left |
| MCR, MR | midfield, wide_midfield | midfield / 4 | right |
| ST, CF | forward | forward / 6 | centre |

현재 생성된 34 links는 다음으로 구성된다.

- `diagonal_progression` 12개: GK→수비 라인 4개, 그리고 각 left/right midfield node→ST/CF 8개
- `same_line_support` 10개: 수비 line 좌·우 pair, midfield line 좌·우 pair, ST↔CF
- `recycle` 12개: 수비→GK와 ST/CF→midfield
- `forward_progression` 0개

`defence → midfield`의 candidate는 예를 들어 `LCB(1,left) → MCL(4,left)`다. lateral relation은 same lane이지만 vertical delta는 `+3`이다. `connectivity_engine_v2._link()`의 `if ... abs(delta)>2: return None`에서 거부된다. `LCB→ML`, `RCB→MCR`, `RB→MR`도 같은 이유로 거부된다. 반면 `MCL(4,left) → ST(6,centre)`는 delta `+2`, adjacent lane이므로 `diagonal_progression`으로 수용된다.

따라서 midfielder→forward links는 존재하지만, defensive start node에서 midfield까지 갈 수 없으므로 complete route가 없다. `_routes()`는 vertical index 0 또는 1에서 시작해 forward band에서 종료할 뿐 AM/DM을 검사하거나 요구하지 않는다.

## 2. vertical band 모델

configured position registry의 `goalkeeper(0)`, `defensive_line(1)`, `wing_back_line(2)`, `defensive_midfield(3)`, `midfield(4)`, `attacking_midfield(5)`, `forward(6)`은 절대 거리용 전술 adjacency가 아니라 position classification line이다. 4-4-2처럼 DM/AM band를 사용하지 않는 formation에서 defensive line과 midfield line이 현재 formation의 인접 occupied line이 될 수 있다는 정보는 기존 `abs(delta) <= 2` 규칙에 없다.

## 3. 7 preset의 현재 결과

| preset | occupied vertical lines | nodes | structural links | forward | diagonal | routes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 4-2-3-1 | 0, 1, 3, 5, 6 | 11 | 38 | 7 | 8 | 16 |
| 4-3-3 | 0, 1, 3, 4, 5, 6 | 11 | 40 | 2 | 16 | 48 |
| 4-4-2 | 0, 1, 4, 6 | 11 | 34 | 0 | 12 | 0 |
| 4-2-4 | 0, 1, 4, 5, 6 | 11 | 34 | 2 | 12 | 0 |
| 3-4-2-1 | 0, 1, 2, 4, 5, 6 | 11 | 42 | 7 | 11 | 25 |
| 3-4-3 | 0, 1, 2, 4, 5, 6 | 11 | 38 | 7 | 10 | 20 |
| 3-5-2 | 0, 1, 2, 4, 6 | 11 | 48 | 7 | 12 | 40 |

Route starts are currently GK and defensive-line nodes (index 0/1); ends are every `forward` band node. 4-2-4도 4-4-2와 같은 defensive_line(1)→midfield(4) 공백 때문에 route가 없다. 이는 formation-specific 문제가 아니다.

## 4. occupied-line adjacency 후보

후보는 기존 forward candidate 조건을 다음처럼 **추가**한다.

1. 현재 formation nodes에서 distinct occupied `vertical_index`를 깊은 쪽부터 정렬한다.
2. source/target의 band가 인접 occupied pair라면, absolute delta가 2를 넘어도 forward candidate를 허용한다.
3. 기존 `abs(delta) <= 2` forward candidates는 그대로 유지한다.
4. same-line support와 recycle의 current rule은 변경하지 않는다.
5. lateral delta는 계속 0 또는 1만 허용한다. left↔right direct link는 계속 거부된다.

이 방식은 special case가 아니며 단순히 현재 formation의 빈 band를 고려한다. 동일 레인 및 인접 레인만 수용하므로 모든 defender→midfielder, 모든 midfielder→forward를 연결하지 않는다.

모의 before/after 결과는 다음과 같다.

| preset | before links/routes | candidate links/routes | 변화 |
| --- | --- | --- | --- |
| 4-2-3-1 | 38 / 16 | 38 / 16 | 없음 |
| 4-3-3 | 40 / 48 | 40 / 48 | 없음 |
| 4-4-2 | 34 / 0 | 42 / 32 | defence→midfield 후보 추가 |
| 4-2-4 | 34 / 0 | 38 / 32 | defence→midfield 후보 추가 |
| 3-4-2-1 | 42 / 25 | 42 / 25 | 없음 |
| 3-4-3 | 38 / 20 | 38 / 20 | 없음 |
| 3-5-2 | 48 / 40 | 48 / 40 | 없음 |

이 비교는 source 수정 없이 만든 position-only simulation이다. 따라서 role behaviour 존재 여부가 결과를 만들지 않는다.

## 5. position-only topology 검토

candidate rule은 다음 topology에서 position-only link/path를 생성했다.

- `DC → MC → ST`: complete route 생성
- `DC → DM → AMC → ST`: existing complete route 유지
- `DC → wing_back_left → AML`: 두 structural progression link 생성. AML은 forward band가 아니므로 complete forward route는 생성하지 않음
- `DC → MCL → AML`: 두 structural progression link 생성. 동일 이유로 complete forward route는 생성하지 않음
- `LCB/DC/RCB → MCL/MCR → ST/CF`: left/centre/right lateral constraint 아래 complete routes 생성

이 결과는 패스 성공이나 역할 행동을 주장하지 않는다.

## 6. false-positive 위험과 보호 장치

occupied-line adjacency는 빈 band를 건너는 forward candidate를 추가할 수 있다. 위험은 같은 occupied line pair에 많은 노드가 있을 때 link 수가 늘어나는 것이다. 다음 제한이 이를 막는다.

- source와 target lane은 identical 또는 adjacent여야 한다.
- left↔right direct connection은 금지된다.
- only forward pair between adjacent **occupied** lines이 추가된다.
- existing same-line/recycle distance rule은 넓히지 않는다.
- route start/end 정의는 변경하지 않는다.

더 엄격한 alternative는 absolute-distance link를 모두 occupied-line rule로 교체하는 방식이다. 그러나 4-3-3의 DM→attacking-line처럼 현재 허용되는 bypass candidate를 삭제할 수 있으므로, 현 단계에서는 일반성 검증이 부족하다.

## 7. 구현 여부와 다음 단계

일반 rule 후보는 4-4-2와 4-2-4의 공통 원인을 해결하고 다른 5 preset의 모의 결과를 바꾸지 않았다. 하지만 요청의 “REPORT FIRST”에 따라 이번 단계에는 구현하지 않았다.

승인 후 최소 변경은 Python과 static JavaScript v2 link generator에 occupied-band context를 전달하고, position-only topology tests, 7-preset regression, Python↔JS parity test를 추가하는 것이다. legacy Connectivity와 role/evidence data는 수정 대상이 아니다.

## 8. 검증과 Git 상태

현재 baseline은 전체 unittest 197개와 `fm26lab.py self-test` 통과다. 이 audit은 report만 추가했으며 commit/push는 하지 않았다.
