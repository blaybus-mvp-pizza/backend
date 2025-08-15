# Backend

해커톤용 FastAPI + MySQL 백엔드 스캐폴딩입니다. LangGraph/OpenAI 확장을 염두에 둔 구조로 설계했습니다.

## 아키텍쳐 구조
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── health.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── deps.py
│   ├── db/
│   │   └── session.py
│   ├── integrations/
│   │   └── llm/
│   │       ├── clients.py
│   │       └── prompts/
│   └── main.py
├── alembic/
├── requirements.txt
├── Dockerfile
└── ENV.EXAMPLE
```

- `api/`:
  - `endpoints/`: 라우트 단위 파일(예: `users.py`)
  - `router.py`: v1 라우터 집결지
- `core/`:
  - `config.py`: pydantic-settings 기반 환경설정
  - `deps.py`: 공용 의존성(예: DB 세션)
- `db/`:
  - `session.py`: SQLAlchemy 엔진/세션, `Base`
- `integrations/llm/`:
  - `clients.py`: LLM 클라이언트 추상화(나중에 OpenAI/LangGraph 연계)
- `main.py`: FastAPI 엔트리. CORS 설정 및 v1 라우터 연결

## 로컬 환경 설정
1) 의존성 설치
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) 환경변수 파일 생성
- `ENV.EXAMPLE`를 복사해 `.env`로 저장 후 값 수정
```bash
cp ENV.EXAMPLE .env
```

3) 서버 실행
```bash
uvicorn app.main:app --reload
```

- 기본 엔드포인트: `GET /` → 웰컴 메시지
- 헬스체크: `GET /api/v1/health/` → `{ "status": "ok" }`

## Docker (로컬 통합)
루트 `infra/local/docker-compose.yml` 사용
```bash
# 루트에서 실행
cd ../infra/local
docker compose up -d --build
```
- 서비스: `mysql`, `adminer(8080)`, `api(8000)`
- API 컨테이너는 `DATABASE_URL=mysql+pymysql://mvp_user:mvp_password@mysql:3306/mvp_db`를 사용


## RDS / MySQL 설정 가이드
- 유저 정보는 보안상 저장하지 않으며, 필요 시 담당자에게 요청하세요.

### 1) 데이터베이스 분리(개발/운영)
```sql
CREATE DATABASE nafal_mvp_dev;
CREATE DATABASE nafal_mvp_prod;
```

### 2) 사용자 생성 및 권한 부여
```sql
-- 개발 계정
CREATE USER 'dev_eatingrabbit'@'%' IDENTIFIED WITH mysql_native_password BY 'mvp2025!';
GRANT ALL PRIVILEGES ON nafal_mvp_dev.* TO 'dev_eatingrabbit'@'%';

-- 운영 계정
CREATE USER 'prod_eatingrabbit'@'%' IDENTIFIED WITH mysql_native_password BY 'mvp2025!';
GRANT ALL PRIVILEGES ON nafal_mvp_prod.* TO 'prod_eatingrabbit'@'%';

FLUSH PRIVILEGES;
```

- 보안 강화를 위해 `%` 대신 팀 고정 IP로 제한하는 것을 권장합니다.

### 3) RDS 네트워크/보안 체크
- 퍼블릭 접근 허용 설정(또는 VPC 내부 통신 구성)
- 보안 그룹 인바운드: 3306 포트에 팀원/서버 IP 화이트리스트 추가

### 4) 애플리케이션 환경변수 설정(.env)
- 개발(RDS dev):
```env
DATABASE_URL=mysql+pymysql://dev_eatingrabbit:<PASSWORD>@<RDS_ENDPOINT>:3306/nafal_mvp_dev
```
- 운영(RDS prod):
```env
DATABASE_URL=mysql+pymysql://prod_eatingrabbit:<PASSWORD>@<RDS_ENDPOINT>:3306/nafal_mvp_prod
```

### ** 공유용 접속 정보 예시(실제 값은 담당자에게 요청)
```
Host: nafal-mvp-db.cn60qq0gyhgp.ap-northeast-2.rds.amazonaws.com
Port: 3306
Database: nafal_mvp_dev / nafal_mvp_prod
User: dev_eatingrabbit / prod_eatingrabbit
Password: <요청>
Allowed IP: <팀원 공인 IP>
```
