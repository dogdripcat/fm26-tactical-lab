# FM26 Tactical Lab v1.2.0

FM26 Tactical Lab은 Football Manager 26 전술의 구조를 브라우저에서 구성하고 분석하는 정적 웹 도구입니다.

공개 사이트에서는 전술을 직접 편집한 뒤 다음 세 축을 중심으로 확인합니다.

- **Connectivity** — 공이 구조적으로 이어질 수 있는가
- **Progression** — 연결을 통해 더 전진된 전술 공간으로 이동할 수 있는가
- **Support** — 공을 받은 뒤 전진·횡·재순환 지원을 받을 수 있는가

숫자 전술 점수, 승률, xG 또는 xThreat를 임의로 생성하지 않습니다.

## 공개 사이트

https://dogdripcat.github.io/fm26-tactical-lab/

## v1.2.0 주요 기능

- 공 소유 시(IP) / 공 미소유 시(OOP) 전술 입력 분리
- 선수 직접 드래그 및 canonical configured-position 기반 배치
- IP/OOP 역할 셀 직접 편집
- 스타일 / 플레이 성향 입력
- Team Instructions: IP 18개 카테고리, OOP 9개 카테고리
- structural formation recognition 및 20개 formation family
- 불명확한 구조의 `사용자 구성` fallback
- Connectivity / Progression / Support 분석
- 상대 전술 직접 편집 및 구조적 matchup 분석
- desktop/mobile 반응형 정적 UI
- GitHub Pages 배포

## 웹 아키텍처

공개 웹사이트는 HTML, CSS, JavaScript modules, JSON으로 구성되며 분석은 브라우저에서 실행됩니다.

주요 경로:

```text
web/static/index.html
web/static/style.css
web/static/app.js
web/static/js/
web/static/data/
```

공개 사이트 사용에는 Python, 데이터베이스, API key 또는 별도 백엔드가 필요하지 않습니다.

Python 코드는 분석 로직의 reference/regression 검증과 기존 연구 도구를 위해 저장소에 함께 유지합니다.

## 개발 검증

전체 Python 회귀 테스트:

```bash
python -m unittest discover -v
```

코어 self-test:

```bash
python fm26lab.py self-test
```

JavaScript 문법 검사는 Node.js가 설치된 환경에서 다음처럼 실행할 수 있습니다.

```bash
node --check web/static/app.js
```

`web/static/js/` 아래 모듈도 동일하게 `node --check`로 검증할 수 있습니다.

## 데이터 및 근거 경계

FM26 역할 identity, 역할 행동, Team Instruction, 플레이 성향 등은 근거 수준을 구분해 관리합니다. 확인되지 않은 FM26 동작을 역할 이름만으로 추론하거나 공식 게임 데이터처럼 표시하지 않습니다.

`미설정`은 필요한 입력에서 Tactical Lab의 UI sentinel로 사용할 수 있으며, 그 자체를 검증된 FM26 선택지라고 간주하지 않습니다.

## Legacy Python core

저장소에는 초기 `v0.2.1` Python 연구/CLI 코어도 남아 있습니다. `fm26lab.py`의 버전은 이 legacy core 계열을 나타내며, 현재 공개 웹 릴리스 버전 `v1.2.0`과는 별도입니다.

예:

```bash
python fm26lab.py self-test
python fm26lab.py inspect-fmf --file "전술파일.fmf"
```

실제 FM26 `.fmf` 내부 포맷을 검증 없이 추측하지 않습니다.

## Release

Public web release: **v1.2.0**

분석 엔진의 검증된 Connectivity / Progression / Support 의미를 presentation 변경 때문에 바꾸지 않는 것을 원칙으로 합니다.
