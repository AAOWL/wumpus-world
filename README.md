# Wumpus World Project

25학년도 가톨릭대학교 인공지능 팀 프로젝트.

## 폴더 구조
- `wumpus/agent/`: Agent 관련 코드
- `wumpus/environment/`: Wumpus World 환경 코드
- `wumpus/controller/` : Agent, Environment간 흐름 제어
- `wumpus/models/`: 값 객체들 정의
- `main.py`: 실행 진입점

## 개발 환경
- Python 3.10
- Formatter: black
- Linter: pylint

## 가상환경 설정
```bash
python -m venv venv
source venv/Scripts/activate  # 윈도우는 .\venv\Scripts\activate
pip install -r requirements.txt
