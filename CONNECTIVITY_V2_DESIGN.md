# Connectivity v2 설계

## 의미와 경계

Connectivity v2는 구성된 IP 시작 위치의 전술적 밴드와 좌·중앙·우 레인을 사용해 공이 이어질 수 있는 **구조적 후보 경로**를 생성한다. 이는 실제 패스, 패스 성공률, 선수의 실제 움직임, 전술의 우열 또는 경기 결과를 뜻하지 않는다.

기존 evidence 기반 Connectivity는 역할 설명 근거의 완전성을 `connected`·`unknown` 등에 직접 반영했다. 이 값은 역할 근거의 수준을 투명하게 보여 주는 연구 정보이지만, 위치 구조 자체의 연결성을 대신할 수 없다. 따라서 legacy 엔진과 그 출력은 보존하고 v2와 섞지 않는다.

## 구조 모델

각 IP 노드는 configured position registry에서 `vertical_band`, `vertical_index`, `lateral_slot`을 얻는다. CSS 좌표는 전술 판단에 사용하지 않으며 전술판 표시 전용이다. 같은 레인 또는 인접 레인이고, 밴드 간 간격이 두 단계 이하인 노드 쌍만 후보로 남긴다.

| 관계 | 방향 | 용도 |
| --- | --- | --- |
| `same_line_support` | support | 같은 라인의 보조 연결 |
| `forward_progression` | forward | 같은 레인의 전진 연결 |
| `diagonal_progression` | forward | 인접 레인의 전진 연결 |
| `recycle` | backward | 후방 순환 연결 |

각 링크는 source/target, relation type, direction, progression value, lateral/vertical relation, structural basis를 가진다. 점수는 없다.

## 전진 경로·병목·네트워크

goalkeeper/defensive line에서 시작해 forward band에 도달하는 forward 링크의 단순 경로를 `progression_routes`로 기록한다. 둘 이상의 경로 내부에 반복되는 노드는 `shared_progression_connector`로 표시한다. 이는 위험 판정이 아닌 중립적 공유 연결점이다.

`network_regions.left|centre|right`는 configured lane으로 노드, 해당 레인을 지나는 링크·전진 경로를 정리한다. 표시 좌표와 무관하다.

## 역할·근거·Compatibility

검증된 `send` semantic은 source, `receive` semantic은 target structural link의 `role_modifiers`로 보존한다. semantic이 없으면 보정만 비어 있을 뿐 structural link는 지워지지 않는다. movement/space semantic은 노드 수준의 modifier로 유지한다.

Evidence는 modifier의 behaviour/evidence ID를 설명하는 provenance다. Compatibility registry는 여전히 연구 계층이며 production rule이 없는 상태에서 v2 링크를 생성하거나 강화하지 않는다.

## 출력과 한계

`connectivity_v2`에는 `nodes`, `structural_links`, `progression_routes`, `bottlenecks`, `network_regions`, `role_modifiers`, `observations`, `limitations`을 반환한다. 팀 지침은 현재 v2에 영향을 주지 않는다. future scoring은 검증 가능한 별도 규칙이 준비될 때만 검토한다.
