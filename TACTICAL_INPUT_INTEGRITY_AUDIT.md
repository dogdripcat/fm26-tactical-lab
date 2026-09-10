# FM26 Tactical Lab — Tactical Input Integrity Audit

생성일: 2026-09-10. 이 문서는 카탈로그·레지스트리·프리셋·웹 어댑터를 읽어 만든 감사 결과다. 역할, 행동, semantic, ERS, compatibility rule은 추가하거나 수정하지 않았다.

## 요약

- configured position: 27개
- catalog role: 69개 (IP 37, OOP 32)
- CRITICAL: Wing-Back family의 configured position ID가 없다.
- CRITICAL: 3백 프리셋 3개가 ML/MR(`wide_midfield`)를 사용한다.
- Web MVP: IP role selector만 있고 team-instruction 입력/API/catalog은 없다.

## A. Configured position registry

| ID | family | vertical band | lateral slot |
|---|---|---|---|
| GK | goalkeeper | goalkeeper | centre |
| LB | full_back | defensive_line | left |
| DL | full_back | defensive_line | left |
| LCB | centre_back | defensive_line | left |
| CB | centre_back | defensive_line | unknown |
| DC | centre_back | defensive_line | centre |
| D(C) | centre_back | defensive_line | centre |
| RCB | centre_back | defensive_line | right |
| RB | full_back | defensive_line | right |
| DR | full_back | defensive_line | right |
| DML | defensive_midfield | defensive_midfield | left |
| DM | defensive_midfield | defensive_midfield | centre |
| DMR | defensive_midfield | defensive_midfield | right |
| MCL | midfield | midfield | left |
| MC | midfield | midfield | centre |
| CM | midfield | midfield | centre |
| MCR | midfield | midfield | right |
| ML | wide_midfield | midfield | left |
| WL | wide_midfield | midfield | left |
| MR | wide_midfield | midfield | right |
| WR | wide_midfield | midfield | right |
| AML | attacking_midfield | attacking_midfield | left |
| AMC | attacking_midfield | attacking_midfield | centre |
| AM | attacking_midfield | attacking_midfield | centre |
| AMR | attacking_midfield | attacking_midfield | right |
| ST | forward | forward | centre |
| CF | forward | forward | centre |

`wing_back` family ID는 0개다. `LB/DL`, `RB/DR`, `ML/WL`, `MR/WR`, `DC/D(C)`는 동일·유사 위치를 나타내는 후보지만 explicit alias/canonical 필드는 없다. 현재는 둘 다 canonical처럼 레지스트리에 존재한다.

## B–C. Preset audit

| preset | position IDs | CB line | wide node family | finding |
|---|---|---:|---|---|
| 4-2-3-1 | GK, LB, LCB, RCB, RB, DML, DMR, AML, AMC, AMR, ST | 2 | — | No three-back wide-midfield conflict detected. |
| 4-3-3 | GK, LB, LCB, RCB, RB, DM, MCL, MCR, AML, AMR, ST | 2 | — | No three-back wide-midfield conflict detected. |
| 4-4-2 | GK, LB, LCB, RCB, RB, ML, MCL, MCR, MR, ST, CF | 2 | ML, MR | No three-back wide-midfield conflict detected. |
| 4-2-4 | GK, LB, LCB, RCB, RB, MCL, MCR, AML, AMR, ST, CF | 2 | — | No three-back wide-midfield conflict detected. |
| 3-4-2-1 | GK, LCB, CB, RCB, ML, MR, DML, DMR, AML, AMC, ST | 3 | ML, MR | CRITICAL: the two wide nodes are ML/MR, registered as wide_midfield; they are not a verified Wing-Back configured position. |
| 3-4-3 | GK, LCB, CB, RCB, ML, MR, DML, DMR, AML, AMR, ST | 3 | ML, MR | CRITICAL: the two wide nodes are ML/MR, registered as wide_midfield; they are not a verified Wing-Back configured position. |
| 3-5-2 | GK, LCB, CB, RCB, ML, MR, DML, DMR, AMC, ST, CF | 3 | ML, MR | CRITICAL: the two wide nodes are ML/MR, registered as wide_midfield; they are not a verified Wing-Back configured position. |

3백 프리셋의 back three는 `LCB, CB, RCB`이다. `ML, MR`는 registry상 `wide_midfield`이며 selector도 Wide Midfield 역할만 반환한다. 따라서 이 노드는 실제 Wing-Back 시작 위치로 사용할 수 없다. 이는 좌표만의 문제가 아니라 role availability, positional relationship, Connectivity node family에 이어진다.

## D–E. Role catalogue and selector

- phase별: IP 37, OOP 32
- IP role family counts: AM 5, CM 6, Centre-Back 6, DM 5, FW 2, Full-Back 5, Goalkeeper 3, Wide Midfield 4, Wing-Back 4, Winger 6
- OOP role family counts: AM 3, CM 4, Centre-Back 6, DM 3, Full-Back 3, Goalkeeper 3, Wide Midfield 3, Wing-Back 3, Winger 4

Web selector (`web/api.py`)는 해당 configured ID의 starting-position label과 role family가 모두 교집합일 때만 role을 반환한다. `LB/RB`는 Full-Back과 Wing-Back 양쪽을 허용하지만 `ML/MR`는 Wide Midfield만 허용한다. `DL/DR/WL/WR/DC/D(C)/MC/CM/AM` 등 registry ID는 selector context가 없어 Web selector에서는 직접 사용되지 않는다.

### Forward 특별 검사

- IP `ST` selector: `catalog:ip:fw:cfd`, `catalog:ip:fw:chf` 두 identity만 반환한다.
- 이 결과는 behaviour evidence filter 때문이 아니다. current `role_catalog.json`의 IP FW identity 자체가 2개이며 current source coverage도 그 범위다.
- 공식 staging/research에 Wide Outlet Winger, Tracking Centre Forward, Target Forward 이름이 나타나지만, 이 감사에서 catalog identity match는 확인되지 않았다. 자동 생성·번역·매핑은 하지 않았다.

역할 존재(identity)와 behaviour evidence는 별도다. selector는 확인된 identity를 보일 수 있고, evidence가 없으면 분석은 unknown/evidence insufficient이어야 한다.

## F. Team instruction audit

Web UI/API에 team instruction 입력 모델이나 `team_instruction_catalog.json`은 없다. `tactic_analysis.py`는 `ip_team_instructions`/`oop_team_instructions`를 의미 추론 없이 보존하며, legacy `fm26lab.py diagnose()`는 unphased `team_instructions`를 읽는다.

### IP — 18 verified category names

- 패스 방식: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 템포: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 시간 보내기: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 공격 전환: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 공격 폭: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 세트피스 유도: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 창조성: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 빌드업 전술: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 골킥: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 골키퍼 배급: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 공격 가담: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 드리블: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 전진: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 패스 스타일: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 참을성: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 중거리 슛: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 크로스 스타일: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 골키퍼 배급(속도): selectable values `[]`, value verification `unknown`, analysis status `unknown`

### OOP — 9 verified category names

- 압박 기준선: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 수비 라인: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 압박 실행: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 수비 전환: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 태클: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 크로스 플레이: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 압박 트랩: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 골키퍼 짧은 볼 배급: selectable values `[]`, value verification `unknown`, analysis status `unknown`
- 수비 라인 행동: selectable values `[]`, value verification `unknown`, analysis status `unknown`

## G. Proposed backward-compatible tactic schema

```json
{
  "in_possession": {
    "formation": [],
    "roles": {},
    "team_instructions": {}
  },
  "out_of_possession": {
    "formation": [],
    "roles": {},
    "team_instructions": {}
  },
  "compatibility_note": "Keep existing ip_roles, oop_roles, ip_formation, oop_formation and legacy team_instructions accepted until an explicit migration is approved."
}
```

이 구조는 설계안일 뿐이다. 기존 Leicester sample, `ip_roles`/`oop_roles`, `ip_formation`/`oop_formation`, legacy `team_instructions`는 Repair Phase 승인 전 변경하지 않는다.

## H. Benchmark notes

- Rate My Tactic: 접근 가능한 페이지가 JavaScript 필요 안내만 반환했다. formation + roles + instructions를 하나의 입력으로 다루는 제품 구조 참고 대상으로만 기록한다. FM24 로직·점수·UI를 복제하지 않는다.
- Fan Football Scout FM26: 제공 URL은 이 검사 환경에서 안전하게 열리지 않았다. formation/roles/instructions/manager presentation 참고 대상으로만 남기며 데이터 truth로 사용하지 않는다.

## 권장 Repair 순서

- 1. Confirm canonical configured-position identities and specifically the actual Wing-Back position IDs from user game UI.
- 2. Add an explicit canonical-position/legacy-alias layer only after that evidence exists.
- 3. Correct the three-back preset position arrays and selector contexts against verified position identities.
- 4. Expand catalogue identities from verified sources; keep behaviour coverage independent.
- 5. Add a team-instruction category catalog with empty/unverified selectable values, then a backward-compatible tactic input migration.
- 6. Enable OOP editing only after phase-specific positions, roles and instructions are verified.

## E. Starting-position selector matrix

아래는 현재 Web selector가 실제로 반환하는 catalog identity다. 이 목록은 FM26 전체 역할 목록이 아니라 `POSITION_CONTEXTS`와 catalog 교집합의 결과다.

### IP

| configured position | selector context | roles |
|---|---|---|
| GK | G / o / a / l / k / e / e / p / e / r | 볼 플레잉 골키퍼 (`catalog:ip:goalkeeper:bgk`), 골키퍼 (`catalog:ip:goalkeeper:goalkeeper`), 안정형 골키퍼 (`catalog:ip:goalkeeper:stable-goalkeeper`) |
| LB | F / u / l / l / - / B / a / c / k /   / + /   / W / i / n / g / - / B / a / c / k | 윙백 (`catalog:ip:wing-back:wb`), 인사이드 윙백 (`catalog:ip:wing-back:iwb`), 전진형 윙백 (`catalog:ip:wing-back:advanced-wing-back`), 플레이메이킹 윙백 (`catalog:ip:wing-back:playmaking-wing-back`), 풀백 (`catalog:ip:full-back:full-back`), 인사이드 풀백 (`catalog:ip:full-back:inside-full-back`) |
| RB | F / u / l / l / - / B / a / c / k /   / + /   / W / i / n / g / - / B / a / c / k | 윙백 (`catalog:ip:wing-back:wb`), 인사이드 윙백 (`catalog:ip:wing-back:iwb`), 전진형 윙백 (`catalog:ip:wing-back:advanced-wing-back`), 플레이메이킹 윙백 (`catalog:ip:wing-back:playmaking-wing-back`), 풀백 (`catalog:ip:full-back:full-back`), 인사이드 풀백 (`catalog:ip:full-back:inside-full-back`) |
| LCB | D / ( / C / ) | 중앙 수비수 (`catalog:ip:centre-back:cb`), 전진형 센터백 (`catalog:ip:centre-back:acb`), 와이드 센터백 (`catalog:ip:centre-back:wcb`), 오버래핑 센터백 (`catalog:ip:centre-back:ocb`), 볼 플레잉 센터백 (`catalog:ip:centre-back:ball-playing-centre-back`), 안정형 센터백 (`catalog:ip:centre-back:stable-centre-back`) |
| CB | D / ( / C / ) | 중앙 수비수 (`catalog:ip:centre-back:cb`), 전진형 센터백 (`catalog:ip:centre-back:acb`), 와이드 센터백 (`catalog:ip:centre-back:wcb`), 오버래핑 센터백 (`catalog:ip:centre-back:ocb`), 볼 플레잉 센터백 (`catalog:ip:centre-back:ball-playing-centre-back`), 안정형 센터백 (`catalog:ip:centre-back:stable-centre-back`) |
| RCB | D / ( / C / ) | 중앙 수비수 (`catalog:ip:centre-back:cb`), 전진형 센터백 (`catalog:ip:centre-back:acb`), 와이드 센터백 (`catalog:ip:centre-back:wcb`), 오버래핑 센터백 (`catalog:ip:centre-back:ocb`), 볼 플레잉 센터백 (`catalog:ip:centre-back:ball-playing-centre-back`), 안정형 센터백 (`catalog:ip:centre-back:stable-centre-back`) |
| DML | D / M | 딥라잉 플레이메이커 (`catalog:ip:dm:dlp`), 박스 투 박스 플레이메이커 (`catalog:ip:dm:bbp`), 박스 투 박스 미드필더 (`catalog:ip:dm:box-to-box-midfielder`), 수비형 미드필더 (`catalog:ip:dm:defensive-midfielder`), 하프백 (`catalog:ip:dm:half-back`) |
| DM | D / M | 딥라잉 플레이메이커 (`catalog:ip:dm:dlp`), 박스 투 박스 플레이메이커 (`catalog:ip:dm:bbp`), 박스 투 박스 미드필더 (`catalog:ip:dm:box-to-box-midfielder`), 수비형 미드필더 (`catalog:ip:dm:defensive-midfielder`), 하프백 (`catalog:ip:dm:half-back`) |
| DMR | D / M | 딥라잉 플레이메이커 (`catalog:ip:dm:dlp`), 박스 투 박스 플레이메이커 (`catalog:ip:dm:bbp`), 박스 투 박스 미드필더 (`catalog:ip:dm:box-to-box-midfielder`), 수비형 미드필더 (`catalog:ip:dm:defensive-midfielder`), 하프백 (`catalog:ip:dm:half-back`) |
| MCL | C / M | 공격형 미드필더 (`catalog:ip:am:am`), 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`), 채널 미드필더 (`catalog:ip:am:channel-midfielder`), 중앙 미드필더 (`catalog:ip:cm:central-midfielder`), 미드필드 플레이메이커 (`catalog:ip:cm:midfield-playmaker`), 와이드 중앙 미드필더 (`catalog:ip:cm:wide-central-midfielder`) |
| MC | C / M | 공격형 미드필더 (`catalog:ip:am:am`), 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`), 채널 미드필더 (`catalog:ip:am:channel-midfielder`), 중앙 미드필더 (`catalog:ip:cm:central-midfielder`), 미드필드 플레이메이커 (`catalog:ip:cm:midfield-playmaker`), 와이드 중앙 미드필더 (`catalog:ip:cm:wide-central-midfielder`) |
| MCR | C / M | 공격형 미드필더 (`catalog:ip:am:am`), 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`), 채널 미드필더 (`catalog:ip:am:channel-midfielder`), 중앙 미드필더 (`catalog:ip:cm:central-midfielder`), 미드필드 플레이메이커 (`catalog:ip:cm:midfield-playmaker`), 와이드 중앙 미드필더 (`catalog:ip:cm:wide-central-midfielder`) |
| ML | W / i / d / e /   / M / i / d / f / i / e / l / d | 인사이드 윙어 (`catalog:ip:winger:inside-winger`), 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`), 윙어 (`catalog:ip:winger:winger`), 와이드 미드필더 (`catalog:ip:wide-midfield:wide-midfielder`) |
| MR | W / i / d / e /   / M / i / d / f / i / e / l / d | 인사이드 윙어 (`catalog:ip:winger:inside-winger`), 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`), 윙어 (`catalog:ip:winger:winger`), 와이드 미드필더 (`catalog:ip:wide-midfield:wide-midfielder`) |
| AML | W / i / n / g / e / r | 인사이드 포워드 (`catalog:ip:winger:if`), 와이드 포워드 (`catalog:ip:winger:wfd`), 플레이메이커 윙어 (`catalog:ip:winger:pw-legacy-name`), 인사이드 윙어 (`catalog:ip:winger:inside-winger`), 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`), 윙어 (`catalog:ip:winger:winger`) |
| AMC | A / M | 공격형 미드필더 (`catalog:ip:am:am`), 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`), 채널 미드필더 (`catalog:ip:am:channel-midfielder`), 프리 롤 (`catalog:ip:am:free-role`), 세컨드 스트라이커 (`catalog:ip:am:second-striker`) |
| AMR | W / i / n / g / e / r | 인사이드 포워드 (`catalog:ip:winger:if`), 와이드 포워드 (`catalog:ip:winger:wfd`), 플레이메이커 윙어 (`catalog:ip:winger:pw-legacy-name`), 인사이드 윙어 (`catalog:ip:winger:inside-winger`), 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`), 윙어 (`catalog:ip:winger:winger`) |
| ST | F / W | 센터 포워드 (`catalog:ip:fw:cfd`), 채널 포워드 (`catalog:ip:fw:chf`) |
| CF | F / W | 센터 포워드 (`catalog:ip:fw:cfd`), 채널 포워드 (`catalog:ip:fw:chf`) |

### OOP

| configured position | selector context | roles |
|---|---|---|
| GK | G / o / a / l / k / e / e / p / e / r | 골키퍼 (`catalog:oop:goalkeeper:goalkeeper`), 라인 홀딩 키퍼 (`catalog:oop:goalkeeper:line-holding-keeper`), 스위퍼 키퍼 (`catalog:oop:goalkeeper:sweeper-keeper`) |
| LB | F / u / l / l / - / B / a / c / k /   / + /   / W / i / n / g / - / B / a / c / k | 홀딩 윙백 (`catalog:oop:wing-back:holding-wing-back`), 압박형 윙백 (`catalog:oop:wing-back:pressing-wing-back`), 윙백 (`catalog:oop:wing-back:wing-back`), 풀백 (`catalog:oop:full-back:full-back`), 홀딩 풀백 (`catalog:oop:full-back:holding-full-back`), 압박형 풀백 (`catalog:oop:full-back:pressing-full-back`) |
| RB | F / u / l / l / - / B / a / c / k /   / + /   / W / i / n / g / - / B / a / c / k | 홀딩 윙백 (`catalog:oop:wing-back:holding-wing-back`), 압박형 윙백 (`catalog:oop:wing-back:pressing-wing-back`), 윙백 (`catalog:oop:wing-back:wing-back`), 풀백 (`catalog:oop:full-back:full-back`), 홀딩 풀백 (`catalog:oop:full-back:holding-full-back`), 압박형 풀백 (`catalog:oop:full-back:pressing-full-back`) |
| LCB | D / ( / C / ) | 중앙 수비수 (`catalog:oop:centre-back:centre-back`), 스토핑 센터백 (`catalog:oop:centre-back:stopping-centre-back`), 커버링 센터백 (`catalog:oop:centre-back:covering-centre-back`), 와이드 센터백 (`catalog:oop:centre-back:wide-centre-back`), 스토핑 와이드 센터백 (`catalog:oop:centre-back:stopping-wide-centre-back`), 커버링 와이드 센터백 (`catalog:oop:centre-back:covering-wide-centre-back`) |
| CB | D / ( / C / ) | 중앙 수비수 (`catalog:oop:centre-back:centre-back`), 스토핑 센터백 (`catalog:oop:centre-back:stopping-centre-back`), 커버링 센터백 (`catalog:oop:centre-back:covering-centre-back`), 와이드 센터백 (`catalog:oop:centre-back:wide-centre-back`), 스토핑 와이드 센터백 (`catalog:oop:centre-back:stopping-wide-centre-back`), 커버링 와이드 센터백 (`catalog:oop:centre-back:covering-wide-centre-back`) |
| RCB | D / ( / C / ) | 중앙 수비수 (`catalog:oop:centre-back:centre-back`), 스토핑 센터백 (`catalog:oop:centre-back:stopping-centre-back`), 커버링 센터백 (`catalog:oop:centre-back:covering-centre-back`), 와이드 센터백 (`catalog:oop:centre-back:wide-centre-back`), 스토핑 와이드 센터백 (`catalog:oop:centre-back:stopping-wide-centre-back`), 커버링 와이드 센터백 (`catalog:oop:centre-back:covering-wide-centre-back`) |
| DML | D / M | 드롭핑 수비형 미드필더 (`catalog:oop:dm:dropping-defensive-midfielder`), 수비형 미드필더 (`catalog:oop:dm:defensive-midfielder`), 스크리닝 수비형 미드필더 (`catalog:oop:dm:screening-defensive-midfielder`) |
| DM | D / M | 드롭핑 수비형 미드필더 (`catalog:oop:dm:dropping-defensive-midfielder`), 수비형 미드필더 (`catalog:oop:dm:defensive-midfielder`), 스크리닝 수비형 미드필더 (`catalog:oop:dm:screening-defensive-midfielder`) |
| DMR | D / M | 드롭핑 수비형 미드필더 (`catalog:oop:dm:dropping-defensive-midfielder`), 수비형 미드필더 (`catalog:oop:dm:defensive-midfielder`), 스크리닝 수비형 미드필더 (`catalog:oop:dm:screening-defensive-midfielder`) |
| MCL | C / M | 중앙 미드필더 (`catalog:oop:cm:central-midfielder`), 압박형 중앙 미드필더 (`catalog:oop:cm:pressing-central-midfielder`), 스크리닝 중앙 미드필더 (`catalog:oop:cm:screening-central-midfielder`), 와이드 커버링 중앙 미드필더 (`catalog:oop:cm:wide-covering-central-midfielder`) |
| MC | C / M | 중앙 미드필더 (`catalog:oop:cm:central-midfielder`), 압박형 중앙 미드필더 (`catalog:oop:cm:pressing-central-midfielder`), 스크리닝 중앙 미드필더 (`catalog:oop:cm:screening-central-midfielder`), 와이드 커버링 중앙 미드필더 (`catalog:oop:cm:wide-covering-central-midfielder`) |
| MCR | C / M | 중앙 미드필더 (`catalog:oop:cm:central-midfielder`), 압박형 중앙 미드필더 (`catalog:oop:cm:pressing-central-midfielder`), 스크리닝 중앙 미드필더 (`catalog:oop:cm:screening-central-midfielder`), 와이드 커버링 중앙 미드필더 (`catalog:oop:cm:wide-covering-central-midfielder`) |
| ML | W / i / d / e /   / M / i / d / f / i / e / l / d | 측면 지향 와이드 미드필더 (`catalog:oop:wide-midfield:wide-oriented-wide-midfielder`), 추적형 와이드 미드필더 (`catalog:oop:wide-midfield:tracking-wide-midfielder`), 와이드 미드필더 (`catalog:oop:wide-midfield:wide-midfielder`) |
| MR | W / i / d / e /   / M / i / d / f / i / e / l / d | 측면 지향 와이드 미드필더 (`catalog:oop:wide-midfield:wide-oriented-wide-midfielder`), 추적형 와이드 미드필더 (`catalog:oop:wide-midfield:tracking-wide-midfielder`), 와이드 미드필더 (`catalog:oop:wide-midfield:wide-midfielder`) |
| AML | W / i / n / g / e / r | 인사이드 지향 윙어 (`catalog:oop:winger:inside-oriented-winger`), 추적형 윙어 (`catalog:oop:winger:tracking-winger`), 윙어 (`catalog:oop:winger:winger`), 측면 지향 윙어 (`catalog:oop:winger:wide-oriented-winger`) |
| AMC | A / M | 공격형 미드필더 (`catalog:oop:am:attacking-midfielder`), 중앙 지향 공격형 미드필더 (`catalog:oop:am:central-oriented-attacking-midfielder`), 추적형 공격형 미드필더 (`catalog:oop:am:tracking-attacking-midfielder`) |
| AMR | W / i / n / g / e / r | 인사이드 지향 윙어 (`catalog:oop:winger:inside-oriented-winger`), 추적형 윙어 (`catalog:oop:winger:tracking-winger`), 윙어 (`catalog:oop:winger:winger`), 측면 지향 윙어 (`catalog:oop:winger:wide-oriented-winger`) |
| ST | F / W | — |
| CF | F / W | — |

## D. Role-family evidence matrix

각 row는 role existence와 analysis evidence를 분리한다. `identity_only`는 selector 존재 여부를 막는 값이 아니며, behaviour/semantic/ERS가 부족하면 분석은 unknown으로 남아야 한다.

### IP

#### AM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 공격형 미드필더 (`catalog:ip:am:am`) | AM, CM | user_ingame_verified | resolved | partial | receive | supported |
| 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`) | AM, CM | unverified | resolved | identity_only | — | unknown |
| 채널 미드필더 (`catalog:ip:am:channel-midfielder`) | AM, CM | unverified | resolved | identity_only | — | unknown |
| 프리 롤 (`catalog:ip:am:free-role`) | AM | unverified | resolved | identity_only | — | unknown |
| 세컨드 스트라이커 (`catalog:ip:am:second-striker`) | AM | unverified | resolved | identity_only | — | unknown |

#### CM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 공격형 미드필더 (`catalog:ip:am:am`) | AM, CM | user_ingame_verified | resolved | partial | receive | supported |
| 전진형 플레이메이커 (`catalog:ip:am:advanced-playmaker`) | AM, CM | unverified | resolved | identity_only | — | unknown |
| 채널 미드필더 (`catalog:ip:am:channel-midfielder`) | AM, CM | unverified | resolved | identity_only | — | unknown |
| 중앙 미드필더 (`catalog:ip:cm:central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |
| 미드필드 플레이메이커 (`catalog:ip:cm:midfield-playmaker`) | CM | unverified | resolved | identity_only | — | unknown |
| 와이드 중앙 미드필더 (`catalog:ip:cm:wide-central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |

#### Centre-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 중앙 수비수 (`catalog:ip:centre-back:cb`) | D(C) | user_ingame_verified | resolved | partial | send | unknown |
| 전진형 센터백 (`catalog:ip:centre-back:acb`) | D(C) | user_ingame_verified | resolved | identity_only | — | unknown |
| 와이드 센터백 (`catalog:ip:centre-back:wcb`) | D(C) | user_ingame_verified | resolved | identity_only | — | unknown |
| 오버래핑 센터백 (`catalog:ip:centre-back:ocb`) | D(C) | user_ingame_verified | resolved | identity_only | — | unknown |
| 볼 플레잉 센터백 (`catalog:ip:centre-back:ball-playing-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 안정형 센터백 (`catalog:ip:centre-back:stable-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |

#### DM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 딥라잉 플레이메이커 (`catalog:ip:dm:dlp`) | DM | user_ingame_verified | resolved | partial | send, space | supported |
| 박스 투 박스 플레이메이커 (`catalog:ip:dm:bbp`) | DM | user_ingame_verified | resolved | partial | movement | supported |
| 박스 투 박스 미드필더 (`catalog:ip:dm:box-to-box-midfielder`) | DM | unverified | resolved | identity_only | — | unknown |
| 수비형 미드필더 (`catalog:ip:dm:defensive-midfielder`) | DM | unverified | resolved | identity_only | — | unknown |
| 하프백 (`catalog:ip:dm:half-back`) | DM | unverified | resolved | identity_only | — | unknown |

#### FW

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 센터 포워드 (`catalog:ip:fw:cfd`) | FW | user_ingame_verified | resolved | partial | — | unknown |
| 채널 포워드 (`catalog:ip:fw:chf`) | FW | user_ingame_verified | resolved | identity_only | — | unknown |

#### Full-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 윙백 (`catalog:ip:wing-back:wb`) | Wing-Back, Full-Back | user_ingame_verified | resolved | partial | space | supported |
| 인사이드 윙백 (`catalog:ip:wing-back:iwb`) | Wing-Back, Full-Back | user_ingame_verified | resolved | partial | space, movement | supported |
| 플레이메이킹 윙백 (`catalog:ip:wing-back:playmaking-wing-back`) | Wing-Back, Full-Back | unverified | resolved | identity_only | — | unknown |
| 풀백 (`catalog:ip:full-back:full-back`) | Full-Back | unverified | resolved | identity_only | — | unknown |
| 인사이드 풀백 (`catalog:ip:full-back:inside-full-back`) | Full-Back | unverified | resolved | identity_only | — | unknown |

#### Goalkeeper

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 볼 플레잉 골키퍼 (`catalog:ip:goalkeeper:bgk`) | Goalkeeper | user_ingame_verified | resolved | partial | movement | unknown |
| 골키퍼 (`catalog:ip:goalkeeper:goalkeeper`) | Goalkeeper | unverified | resolved | identity_only | — | unknown |
| 안정형 골키퍼 (`catalog:ip:goalkeeper:stable-goalkeeper`) | Goalkeeper | unverified | resolved | identity_only | — | unknown |

#### Wide Midfield

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 인사이드 윙어 (`catalog:ip:winger:inside-winger`) | Winger, Wide Midfield | unverified | resolved | identity_only | — | unknown |
| 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`) | Winger, Wide Midfield | unverified | unresolved | unresolved | — | unknown |
| 윙어 (`catalog:ip:winger:winger`) | Winger, Wide Midfield | unverified | resolved | identity_only | — | unknown |
| 와이드 미드필더 (`catalog:ip:wide-midfield:wide-midfielder`) | Wide Midfield | unverified | resolved | identity_only | — | unknown |

#### Wing-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 윙백 (`catalog:ip:wing-back:wb`) | Wing-Back, Full-Back | user_ingame_verified | resolved | partial | space | supported |
| 인사이드 윙백 (`catalog:ip:wing-back:iwb`) | Wing-Back, Full-Back | user_ingame_verified | resolved | partial | space, movement | supported |
| 전진형 윙백 (`catalog:ip:wing-back:advanced-wing-back`) | Wing-Back | unverified | resolved | identity_only | — | unknown |
| 플레이메이킹 윙백 (`catalog:ip:wing-back:playmaking-wing-back`) | Wing-Back, Full-Back | unverified | resolved | identity_only | — | unknown |

#### Winger

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 인사이드 포워드 (`catalog:ip:winger:if`) | Winger | user_ingame_verified | resolved | partial | receive, space, movement | supported |
| 와이드 포워드 (`catalog:ip:winger:wfd`) | Winger | user_ingame_verified | resolved | partial | space, movement | supported |
| 플레이메이커 윙어 (`catalog:ip:winger:pw-legacy-name`) | Winger | user_ingame_verified | unresolved | unresolved | — | unknown |
| 인사이드 윙어 (`catalog:ip:winger:inside-winger`) | Winger, Wide Midfield | unverified | resolved | identity_only | — | unknown |
| 플레이메이킹 윙어 (`catalog:ip:winger:playmaking-winger`) | Winger, Wide Midfield | unverified | unresolved | unresolved | — | unknown |
| 윙어 (`catalog:ip:winger:winger`) | Winger, Wide Midfield | unverified | resolved | identity_only | — | unknown |

### OOP

#### AM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 공격형 미드필더 (`catalog:oop:am:attacking-midfielder`) | AM | unverified | resolved | identity_only | — | unknown |
| 중앙 지향 공격형 미드필더 (`catalog:oop:am:central-oriented-attacking-midfielder`) | AM | unverified | resolved | identity_only | — | unknown |
| 추적형 공격형 미드필더 (`catalog:oop:am:tracking-attacking-midfielder`) | AM | unverified | resolved | identity_only | — | unknown |

#### CM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 중앙 미드필더 (`catalog:oop:cm:central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |
| 압박형 중앙 미드필더 (`catalog:oop:cm:pressing-central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |
| 스크리닝 중앙 미드필더 (`catalog:oop:cm:screening-central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |
| 와이드 커버링 중앙 미드필더 (`catalog:oop:cm:wide-covering-central-midfielder`) | CM | unverified | resolved | identity_only | — | unknown |

#### Centre-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 중앙 수비수 (`catalog:oop:centre-back:centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 스토핑 센터백 (`catalog:oop:centre-back:stopping-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 커버링 센터백 (`catalog:oop:centre-back:covering-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 와이드 센터백 (`catalog:oop:centre-back:wide-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 스토핑 와이드 센터백 (`catalog:oop:centre-back:stopping-wide-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |
| 커버링 와이드 센터백 (`catalog:oop:centre-back:covering-wide-centre-back`) | D(C) | unverified | resolved | identity_only | — | unknown |

#### DM

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 드롭핑 수비형 미드필더 (`catalog:oop:dm:dropping-defensive-midfielder`) | DM | unverified | resolved | identity_only | — | unknown |
| 수비형 미드필더 (`catalog:oop:dm:defensive-midfielder`) | DM | unverified | resolved | identity_only | — | unknown |
| 스크리닝 수비형 미드필더 (`catalog:oop:dm:screening-defensive-midfielder`) | DM | unverified | resolved | identity_only | — | unknown |

#### Full-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 풀백 (`catalog:oop:full-back:full-back`) | Full-Back | unverified | resolved | identity_only | — | unknown |
| 홀딩 풀백 (`catalog:oop:full-back:holding-full-back`) | Full-Back | unverified | resolved | identity_only | — | unknown |
| 압박형 풀백 (`catalog:oop:full-back:pressing-full-back`) | Full-Back | unverified | resolved | identity_only | — | unknown |

#### Goalkeeper

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 골키퍼 (`catalog:oop:goalkeeper:goalkeeper`) | Goalkeeper | unverified | resolved | identity_only | — | unknown |
| 라인 홀딩 키퍼 (`catalog:oop:goalkeeper:line-holding-keeper`) | Goalkeeper | unverified | resolved | identity_only | — | unknown |
| 스위퍼 키퍼 (`catalog:oop:goalkeeper:sweeper-keeper`) | Goalkeeper | unverified | resolved | identity_only | — | unknown |

#### Wide Midfield

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 측면 지향 와이드 미드필더 (`catalog:oop:wide-midfield:wide-oriented-wide-midfielder`) | Wide Midfield | unverified | resolved | identity_only | — | unknown |
| 추적형 와이드 미드필더 (`catalog:oop:wide-midfield:tracking-wide-midfielder`) | Wide Midfield | unverified | resolved | identity_only | — | unknown |
| 와이드 미드필더 (`catalog:oop:wide-midfield:wide-midfielder`) | Wide Midfield | unverified | resolved | identity_only | — | unknown |

#### Wing-Back

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 홀딩 윙백 (`catalog:oop:wing-back:holding-wing-back`) | Wing-Back | unverified | resolved | identity_only | — | unknown |
| 압박형 윙백 (`catalog:oop:wing-back:pressing-wing-back`) | Wing-Back | unverified | resolved | identity_only | — | unknown |
| 윙백 (`catalog:oop:wing-back:wing-back`) | Wing-Back | unverified | resolved | identity_only | — | unknown |

#### Winger

| role | available starting positions | abbreviation status | identity status | behaviour | semantic groups | ERS |
|---|---|---|---|---|---|---|
| 인사이드 지향 윙어 (`catalog:oop:winger:inside-oriented-winger`) | Winger | unverified | resolved | identity_only | — | unknown |
| 추적형 윙어 (`catalog:oop:winger:tracking-winger`) | Winger | unverified | resolved | identity_only | — | unknown |
| 윙어 (`catalog:oop:winger:winger`) | Winger | unverified | resolved | identity_only | — | unknown |
| 측면 지향 윙어 (`catalog:oop:winger:wide-oriented-winger`) | Winger | unverified | resolved | identity_only | — | unknown |
