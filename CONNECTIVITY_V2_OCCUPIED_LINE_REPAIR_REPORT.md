# Connectivity v2 Occupied-Line Adjacency Repair Report

## 변경 내용

`connectivity_engine_v2.py`와 `web/static/js/connectivity_engine_v2.js`는 현재 tactic의 유효한 `vertical_index`를 모아 오름차순 occupied line 목록을 만든다. 연속한 occupied line pair를 만들고, forward link의 absolute band delta가 2보다 큰 경우에도 이 pair에 속하면 link 생성을 허용한다.

이는 absolute-distance 규칙을 대체하지 않는 additive exception이다. delta가 2 이하인 기존 link는 유지된다. same-line support와 recycle은 기존 절대 거리 규칙을 그대로 사용한다.

## adjacency와 lateral safeguard

새 exception은 `delta > 0`일 때만 적용된다. source/target의 lateral slot이 같거나 인접해야 하며, left→right 또는 right→left direct progression은 계속 거부된다. 따라서 모든 defender→midfielder 또는 모든 midfielder→forward가 연결되지는 않는다.

new link는 기존 lateral rule로 `forward_progression` 또는 `diagonal_progression`으로 분류한다. 별도의 품질 category는 만들지 않았다.

`structural_basis`는 다음을 기록한다.

```json
{
  "adjacency_basis": "occupied_line_adjacency",
  "source_band": "defensive_line",
  "target_band": "midfield",
  "absolute_band_delta": 3
}
```

기존 absolute-distance link는 `adjacency_basis: "absolute_band_adjacency"`로 남는다. 이 값은 debug/provenance 용도이며 UI는 변경하지 않았다.

## seven-preset before/after

| Preset | Before links/routes | After links/routes |
| --- | ---: | ---: |
| 4-2-3-1 | 38 / 16 | 38 / 16 |
| 4-3-3 | 40 / 48 | 40 / 48 |
| 4-4-2 | 34 / 0 | 42 / 32 |
| 4-2-4 | 34 / 0 | 38 / 32 |
| 3-4-2-1 | 42 / 25 | 42 / 25 |
| 3-4-3 | 38 / 20 | 38 / 20 |
| 3-5-2 | 48 / 40 | 48 / 40 |

4-4-2는 새로 허용된 8개 forward link가 모두 occupied `defensive_line(1) → midfield(4)` pair에 속한다. 4-2-4도 동일한 formation-independent 이유로 repair를 받는다.

## position-only topology

역할 evidence 없이 다음을 검증했다.

- `DC → MC → ST` complete route
- `DC → DM → AMC → ST` complete route
- `LCB/DC/RCB → MCL/MCR → ST/CF` complete routes
- `DC → wing_back_left → AML` structural links
- `DC → MCL → AML` structural links

wide attacker topology는 endpoint가 forward band가 아니므로 structural link를 만들어도 complete route가 되지 않는다. 이는 traversal 변경이 아니라 start/end 정의의 의도된 결과다.

## regression and parity

- Python↔static JavaScript v2 parity: Leicester, 4-3-3, 4-4-2, 3-4-2-1 fixture 통과
- JavaScript syntax: 통과
- legacy Leicester Connectivity: 11/11 resolution, 61 edges, semantic_complete 2, mixed 7, compatibility_only 4, evidence_missing 48 유지
- route traversal은 변경하지 않았다.

## risk review

occupied-line adjacency는 비어 있는 ontology band를 건너는 전방 후보만 추가한다. lateral constraint와 forward-only guard가 cross-pitch 및 arbitrary recycle 생성을 막는다. route count는 topology 정보이며 전술 품질 점수나 예측이 아니다.

role catalogue, behaviour evidence, semantic vocabulary, ERS, compatibility, team-instruction data, position registry, display coordinates와 UI는 변경하지 않았다. 역할 evidence는 계속 modifier-only다.

## files

- `connectivity_engine_v2.py`
- `web/static/js/connectivity_engine_v2.js`
- `test_connectivity_engine_v2.py`
- `CONNECTIVITY_V2_OCCUPIED_LINE_REPAIR_REPORT.md`

commit과 push는 하지 않았다.
