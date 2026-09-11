# Connectivity v2 User-Facing Analysis UI

## 1. 정보 계층

피치는 계속 첫 번째 설명 도구다. `주요 연결 / 전체 연결`은 유지하며 기본은 주요 연결이다. 분석 영역은 다음 순서로 압축했다.

1. 공 연결성 요약
2. 전진 경로
3. 좌·중앙·우 지역 카드
4. 연결 의존도
5. 지원과 순환
6. 역할에 따른 보정 (접힌 영역)
7. 근거 및 한계 (접힌 영역)

UI는 `connectivity_evaluation`을 `connectivity_evaluation_presenter.js`로 형식화할 뿐이며, app.js에서 topology·dependency·역할 결론을 다시 계산하지 않는다.

## 2. 요약과 line-continuity 문구

`continuous`는 “점유한 각 라인 사이에 전진 연결이 이어집니다.”로, `partial`은 “일부 라인 사이의 전진 연결이 제한적입니다.”로, `interrupted`는 “전방으로 이어지는 과정에서 구조적으로 끊기는 구간이 있습니다.”로 표시한다.

완결 경로가 있는 경우 headline은 현재 가능한 좌·중앙·우 region을 사용한다. 예: “수비선에서 전방까지 이어지는 구조적 연결이 존재하며, 왼쪽과 중앙과 오른쪽을 통해 전진 경로를 사용할 수 있습니다.” raw link/route count는 headline에 쓰지 않는다.

## 3. 지역 카드와 progression

좌·중앙·우 카드는 `전방 연결 있음`, `복수 경로 있음`, `완결 경로 미확인` 및 근거가 있는 `중앙 연결 가능`/`좌·우 연결 가능`만 보여준다. 색이나 등급은 전술적 좋고 나쁨을 뜻하지 않는다.

카드를 누르면 evaluator가 이미 반환한 해당 region의 representative route ID를 읽어 관련 피치 선을 임시 강조한다. 새 route나 edge를 만들지 않고, 다시 누르면 해제한다.

## 4. 의존도·shared connector·bottleneck

node-removal 결과가 `regional_progression_removed` 또는 `all_complete_progression_removed`일 때만 의존도 본문에 표시한다.

* 지역 제거: “`[위치]`가 제외되면 `[지역]`의 전방 연결이 구조적으로 끊깁니다.”
* 전체 제거: “`[위치]`가 제외되면 현재 구조에서 완결된 전진 경로가 남지 않습니다.”

`removes_one_alternative`는 본문에 node별 경고로 나열하지 않는다. 단순 `shared_progression_connector`도 dependency가 없는 경우에만 “여러 전진 경로가 이 연결점을 공유합니다.”라고 별도로 표현한다. 병목·취약점이라는 표현은 사용하지 않는다.

의존도 항목을 누르면 해당 configured-position node와 incident links를 강조한다. node 제거를 피치에서 가상으로 재생하지 않는다.

## 5. 지원·순환, dead end, isolation

fallback 구조가 확인되면 “같은 라인이나 후방으로 공을 다시 연결할 구조적 선택지”로, 확인되지 않으면 “되돌려 순환할 선택지가 제한적”으로 표시한다. 이는 패스 성공, 점유율, 압박 회피를 주장하지 않는다.

dead-end와 isolation은 evaluator가 확인한 경우만 출력한다. configured forward endpoint나 일반 wide outlet은 표시하지 않는다.

## 6. 역할 보정과 근거

역할 보정은 검증된 `role_adjustments`만 사용한다. 중앙 이동, 라인 사이 수신, 폭 유지, 전방 전달 같은 문구는 구조 링크를 변경하지 않는 설명 근거로 표시한다. evidence ID는 화면의 상위 정보가 아니라 최하단의 접힌 한계/근거 영역에 남는다.

항상 다음 limitation을 유지한다.

> 이 평가는 포메이션과 역할의 구조적 연결 가능성을 분석합니다. 실제 패스 성공률, 선수 능력치, 상대 압박, 경기 상황은 반영하지 않습니다.

## 7. 반응형 동작

desktop에서는 피치와 Team Instructions가 기존처럼 나란히 있고 분석은 아래에 나온다. 지역 카드는 3열이다. narrow view에서는 기존 evaluation grid와 지역 카드가 한 열로 바뀌며 수평 스크롤을 만들지 않는다.

## 8. 7개 preset 관찰

| Formation | headline의 region | 카드 문구 |
| --- | --- | --- |
| 4-2-3-1 | 왼쪽·중앙·오른쪽 | 세 지역 모두 복수 경로 있음 |
| 4-3-3 | 왼쪽·중앙·오른쪽 | 세 지역 모두 복수 경로 있음 |
| 4-4-2 | 왼쪽·오른쪽 | 좌·우 복수 경로 있음, 중앙 완결 경로 미확인 |
| 4-2-4 | 왼쪽·오른쪽 | 좌·우 복수 경로 있음, 중앙 완결 경로 미확인 |
| 3-4-2-1 | 왼쪽·중앙·오른쪽 | 세 지역 모두 복수 경로 있음 |
| 3-4-3 | 왼쪽·중앙·오른쪽 | 세 지역 모두 복수 경로 있음 |
| 3-5-2 | 왼쪽·중앙·오른쪽 | 세 지역 모두 복수 경로 있음 |

이는 formation 순위가 아니며, “중앙 완결 경로 미확인”도 evaluator의 current family 분류 결과일 뿐 전술적 단점 결론이 아니다.

## 9. Synthetic presentation 결과

* 단일 중앙 bridge: 전체 progression 생존 상실 문구만 표시
* 좌 연결·우 고립: 우 isolation 문구만 표시
* 한 미드필더 의존: node-removal 근거가 있을 때만 지역 연결 제거 문구 표시
* 독립 두 path: 각 지역의 전방 연결을 독립적으로 표시
* 완결 route 없음: 완결 경로 미확인 headline
* 전진·순환 없음: 지원과 순환의 제한 문구
* wide-only / central-only: 존재하지 않는 region을 “완결 경로 미확인”으로 표시

## 10. 검증과 파일

추가 테스트는 summary, line-continuity, 지역 문구, dependency/shared/bottleneck 구분, support/recycle, dead-end 안전성, role adjustment, limitation, 7 preset 및 synthetic fixture를 검증한다.

변경 파일:

* `web/static/js/connectivity_evaluation_presenter.js`
* `web/static/js/connectivity_evaluation_presentation_runner.mjs`
* `web/static/app.js`
* `web/static/index.html`
* `web/static/style.css`
* `test_connectivity_evaluation_presenter.py`

## 11. 알려진 한계와 Git 상태

이 UI는 evaluator의 configured-position topology를 설명할 뿐 실제 경기 전개·선수 능력·상대 압박·팀 지침 효과를 분석하지 않는다. public UI에는 점수, 등급, progress bar, formation ranking을 추가하지 않았다.

이번 phase에서 commit과 push는 수행하지 않았다.
