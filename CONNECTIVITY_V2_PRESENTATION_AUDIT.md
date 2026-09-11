# Connectivity v2 Presentation Audit

## 범위

이 문서는 읽기 전용 audit이다. v2 structural rule, 역할 데이터, behaviour, semantic, ERS, compatibility, 팀 지침 truth와 점수 체계는 바꾸지 않았다. legacy evidence graph도 그대로다.

## 1. 링크 밀도와 표시 문제

현행 정적 UI는 `connectivity_v2.structural_links` 전체를 동시에 렌더링한다. Leicester의 38개, 3-4-2-1의 42개 링크는 390px pitch에서 역할 노드와 겹치며, 링크가 많다는 구조적 사실을 전달하기보다 화면을 복잡하게 만든다. 특히 recycle 15~18개는 전진 경로 판단보다 시각적으로 먼저 눈에 들어온다.

유효한 structural link를 엔진에서 삭제해서는 안 된다. 표시 계층만 다음 세 그룹으로 분리하는 것이 적절하다.

1. **기본 표시**: representative progression spine. forward/diagonal link 중 각 defensive·midfield source에서 같은 레인 전진 후보를 우선 선택하고, 같은 레인 후보가 없을 때만 인접 레인의 후보를 선택한다. 같은 조건의 후보는 configured position ID 순서로 안정적으로 정렬한다.
2. **보조 표시**: 기본 spine에 포함되지 않은 forward/diagonal link와 representative same-line support. 사용자가 `전진 대안 보기`를 눌렀을 때 표시한다.
3. **숨김 기본값**: recycle 및 나머지 same-line support. 노드 또는 링크를 선택하면 해당 노드의 인접 링크로 공개한다.

이 규칙은 engine truth를 바꾸지 않고, display layer가 `structural_links`를 결정론적으로 필터링하도록 한다. 역할 근거 modifier는 별도 우선순위가 아니라 해당 링크의 강조 스타일로만 사용한다.

## 2. 전진 경로 표시

현재 route는 가능한 단순 경로의 열거여서 Leicester 16개, 4-3-3 48개가 된다. 사용자에게 모두 나열하면 중복된 출발/합류 차이만 반복된다.

표시는 route를 좌·중앙·우의 최초 레인 및 첫 전진 분기 기준으로 묶어 representative route 하나와 `대안 경로 있음` 상태로 요약하는 것이 적절하다. Leicester의 대표 예시는 다음과 같다.

- 좌측: `LCB → DML → AML 또는 AMC → ST`
- 우측: `RCB → DMR → AMR 또는 AMC → ST`
- 중앙: AMC를 경유하는 좌·우 대안의 합류 구간

`route_id`, 전체 route 목록, 그리고 정확한 중복 경로는 상세 보기에서만 유지한다. `recycle-dependent`는 forward route만으로 도달하지 못하고 recycle이 필요한 경우에만 표시한다. 현재 route generator는 forward edge만 사용하므로, 현 four fixtures에는 이 상태를 판정할 근거가 없다.

## 3. shared connector와 bottleneck

현재 `bottlenecks`는 두 route 이상에 내부 노드로 등장한 `shared_progression_connector`다. Leicester에서는 9개, 4-3-3에서는 9개, 3-4-2-1에서는 9개가 나온다. 이를 사용자에게 `병목`이라고 부르면 거의 모든 선수에 부정적 의미를 부여하게 된다.

따라서 현 출력의 사용자 명칭은 **공유 진행 연결점**이어야 한다. `high-dependency connector`는 representative route family의 모든 경로가 같은 노드를 통과할 때만 별도 표시할 수 있다. **구조적 병목**은 그 노드를 제거했을 때 특정 출발 레인에 전진 route family가 전혀 남지 않는다는 결정론적 검사가 있을 때만 사용한다. 현 v2에는 이 route-diversity 제거 검사가 없으므로, 네 formation 모두에서 `true structural bottleneck`은 확정하지 않는다.

## 4. 네 formation 비교

| Fixture | 구조 링크 | 현재 기본 표시 링크 | 전진 route | 공유 연결점 | 사용자 표시 판단 |
| --- | ---: | ---: | ---: | --- | --- |
| Leicester 4-2-3-1 | 38 | 38 | 16 | 9 | 과밀. 좌·우 progression family와 AMC 합류를 대표 표시해야 함 |
| 4-3-3 | 40 | 40 | 48 | 9 | 가장 과밀. 48 route를 3개 레인 family로 접어야 함 |
| 4-4-2 | 34 | 34 | 0 | 0 | 과밀이지만 progression summary는 ‘구조적 전진 경로를 현재 rule로 생성하지 못함’이어야 함 |
| 3-4-2-1 | 42 | 42 | 25 | 9 | 과밀. wing-back을 포함한 좌·우 representative route를 우선 표시해야 함 |

4-4-2의 0 route는 v2 rule의 `vertical band` 간 허용 거리 때문에 defensive line에서 midfield로 직접 이어지는 경우가 전진 route로 열거되지 않는 현 모델 한계다. configured position registry가 잘못됐다는 증거는 없으므로 이번 audit에서 core를 수정하지 않는다. 다만 user-facing UI는 0을 ‘전술 단절’로 번역하면 안 되며, ‘현재 구조 규칙으로는 전진 경로를 요약하지 못함’으로 제한해야 한다.

## 5. summary·tooltip 문구

권장 summary 예시:

> 구성된 위치 관계에서 좌측과 우측의 전진 후보 경로가 있으며, AMC는 두 경로가 만나는 공유 진행 연결점입니다. 역할 근거는 일부 링크의 설명을 보강하지만 실제 패스 성공을 뜻하지 않습니다.

권장 링크 tooltip:

- **구조적 연결**: `수비형 미드필드와 공격형 미드필드 사이의 전진 연결 경로`
- **역할 보정**: `딥라잉 플레이메이커의 전방 배급 근거와 공격형 미드필더의 라인 사이 수신 근거가 이 경로 설명을 보강합니다.`
- **근거**: compact evidence ID 또는 source title
- **한계**: `실제 경기의 패스 성공률, 선수 능력, 상대 압박은 반영하지 않습니다.`

`semantic_complete`, `compatibility_only`, `evidence_missing`, raw relation ID는 debug/evidence detail에만 남긴다.

## 6. 팀 지침과 전술판 확인

로컬 정적 사이트에서 IP/OOP tab을 확인했다. IP 탭은 18개 카테고리만, OOP 탭은 9개 카테고리만 노출했다. OOP 탭 전환 뒤 IP long list가 accessibility tree에서 제거되어 한 panel만 보이는 것을 확인했다. 탭의 `aria-selected`도 함께 전환된다. 선택값은 `tactic.ip_team_instructions` 및 `tactic.oop_team_instructions`에 별도로 저장하는 기존 코드와 regression test가 보장한다.

390px maximum-width pitch는 narrow viewport에서도 11개 node label과 football marking을 읽을 수 있었다. 다만 narrow viewport에서는 team instruction panel이 pitch 아래로 이동한다. 일반 desktop에서는 CSS grid가 pitch와 right panel을 함께 배치하도록 되어 있다. 실제 연결선은 현재 blank initial state에서는 렌더링되지 않으므로, 링크 밀도 판단은 four fixture의 v2 output을 사용했다.

## 7. 남은 UX 작업

- proposed display-priority layer와 route-family grouping은 아직 구현하지 않았다.
- 현재 `공유 진행 연결점` 목록은 대표 route 기준으로 축소해야 한다.
- 4-4-2의 route 0은 UI에서 부정 평가로 읽히지 않도록 별도 limitation 문구가 필요하다.
- evidence ID 대신 사람이 읽을 source title을 표시하는 compact evidence view가 필요하다.

## 8. 검증과 Git 상태

이 audit 이전의 v2 회귀는 Python↔browser golden fixture 4개가 일치했고 전체 unittest 197개 및 `fm26lab.py self-test`가 통과했다. 이 문서는 source code나 data 변경 없이 추가된 audit 결과다. commit과 push는 하지 않았다.
