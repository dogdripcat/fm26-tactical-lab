# 전술 UI Compact Repair 보고

## 변경 내용

전술판의 최대 폭을 390px로 제한하고 노드·글자·SVG 선을 함께 축소했다. 데스크톱에서는 전술판과 팀 지침을 한 행에서 보도록 최대 콘텐츠 폭과 grid 비율을 줄였다. 모바일에서는 한 열로 전환한다. 기존 position display coordinates, 좌우 대칭, 7 preset, 축구장 markings는 유지한다.

Connectivity 범례는 legacy evidence 상태 대신 `기본 연결 경로`, `전진 연결 경로`, `보조/순환 경로`, `역할 근거로 강화된 경로`로 바꿨다. 링크 클릭 tooltip은 구조적 연결, 역할 보정, 근거, 한계를 분리한다.

팀 지침은 IP/OOP 탭으로 바꿨다. 한 시점에는 한 panel만 표시되고 전환해도 선택값은 tactic object에 그대로 보존된다. IP 18개와 OOP 9개 카테고리 및 `선택값 검증 필요` 상태는 유지한다. 팀 지침 효과는 여전히 분석하지 않는다.

## 제한과 검증

브라우저 런타임은 정적 파일만 사용하며 API/서버를 다시 도입하지 않았다. Forward catalogue는 이번 단계의 범위 밖이므로 수정하지 않았고 별도 데이터 블로커로 남겼다. UI와 v2 엔진의 회귀는 unittest 및 browser parity로 검증한다.
