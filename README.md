# Backend

해커톤용 FastAPI + MySQL 백엔드 스캐폴딩입니다. LangGraph/OpenAI 확장을 염두에 둔 구조로 설계했습니다.

## 아키텍쳐 구조
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── health.py
│   │       │   ├── db_info.py
│   │       │   └── auth.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── deps.py
│   │   └── security.py
│   ├── db/
│   │   └── session.py
│   ├── domains/
│   │   ├── auth/
│   │   │   └── models.py           # 도메인 I/O 모델(Token 등, Pydantic)
│   │   ├── system/
│   │   │   └── models.py           # DBInfo 등 시스템 I/O 모델(Pydantic)
│   │   └── users/
│   │       ├── models.py           # UserCreate/UserRead 등(Pydantic)
│   │       └── service.py          # 유즈케이스/비즈니스 로직
│   ├── repositories/
│   │   ├── db_info.py
│   │   └── user.py                 # 영속성 접근. 엔티티(SQLAlchemy) 의존
│   ├── schemas/
│   │   └── users.py                # 엔티티(SQLAlchemy) — 테이블 매핑
│   └── main.py
├── alembic/
├── requirements.txt
├── Dockerfile
└── ENV.EXAMPLE
```

## 아키텍처 / 레이어
- 엔티티(SQLAlchemy) = `app/schemas/*`
  - DB 테이블 스키마 매핑. 내부 전용
- 도메인 I/O 모델(Pydantic) = `app/domains/<domain>/models.py`
  - API/서비스 경계의 DTO. 외부 계약을 표현
- 서비스(Application) = `app/domains/<domain>/service.py`
  - 유즈케이스/권한/검증/트랜잭션/외부 연동 오케스트레이션
- 리포지토리 = `app/repositories/*`
  - DB 접근. 엔티티(SQLAlchemy)만 의존
- API = `app/api/v1/endpoints/*`
  - 라우팅/입출력 바인딩. 도메인 I/O 모델만 의존(엔티티 직접 의존 금지)
- 코어/인프라 = `app/core/*`, `app/db/session.py`

의존성 방향(단방향)
- api → domains(models, services) → repositories → schemas(entities) → db
- api는 절대 schemas(엔티티)를 직접 참조하지 않음

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
- 필수: `DATABASE_URL` (예: RDS dev/prod 또는 로컬 MySQL)
- CORS: `CORS_ORIGINS`는 JSON 배열 또는 CSV/단일 문자열 모두 지원
- JWT: `SECRET_KEY`는 운영에서 반드시 변경

3) 서버 실행
```bash
uvicorn app.main:app --reload
```
- 기본 엔드포인트: `GET /`

## 코드 포맷(Black)
```bash
pip install black
# 전체 포맷
black .
# 체크만(변경 없음)
black --check .
```
- 에디터 저장 시 포맷을 켜두는 것을 권장합니다(VS Code: Python › Formatting: Provider = black).

## Docker (로컬 통합)
루트 `infra/local/docker-compose.yml` 사용
```bash
# 루트에서 실행
cd ../infra/local
docker compose up -d --build
```
- 서비스: `mysql`, `adminer(8080)`, `api(8000)`
- API 컨테이너는 `DATABASE_URL`을 env로 주입해 사용

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
- 보안 강화를 위해 `%` 대신 팀 고정 IP로 제한 권장

### 3) RDS 네트워크/보안 체크
- 퍼블릭 접근 허용 설정(또는 VPC 내부 통신 구성)
- 보안 그룹 인바운드: 3306 포트에 팀원/서버 IP 화이트리스트 추가

### 4) 애플리케이션 환경변수(.env)
- 개발(RDS dev):
```env
DATABASE_URL=mysql+pymysql://dev_eatingrabbit:<PASSWORD>@<RDS_ENDPOINT>:3306/nafal_mvp_dev
```
- 운영(RDS prod):
```env
DATABASE_URL=mysql+pymysql://prod_eatingrabbit:<PASSWORD>@<RDS_ENDPOINT>:3306/nafal_mvp_prod
```
- 비밀번호 특수문자는 URL 인코딩 권장(@ → %40, ! → %21 등)
- SSL 사용 시(권장):
```env
DATABASE_URL=mysql+pymysql://.../nafal_mvp_dev?ssl_ca=/path/to/rds-combined-ca-bundle.pem
```

### 5) 연결 확인
- API: `GET /api/v1/db/info`
- 파이썬 원라이너:
```bash
python -c "import os; from sqlalchemy import create_engine, text; e=create_engine(os.environ['DATABASE_URL']); print(e.connect().execute(text('select 1')).scalar())"
```

### 6) 운영 베스트 프랙티스(간단 요약)
- 운영 RDS 계정 최소 권한 원칙
- Adminer/DB GUI 외부 공개 금지(SSH 터널 사용)
- 비밀값은 .env로만 관리(.gitignore). 예시는 `ENV.EXAMPLE` 참조
- SQLAlchemy 엔진 옵션 권장: `pool_pre_ping=True`, `pool_recycle=3600`

### 공유용 접속 정보 예시(실제 값은 담당자에게 요청)
```
Host: nafal-mvp-db.cn60qq0gyhgp.ap-northeast-2.rds.amazonaws.com
Port: 3306
Database: nafal_mvp_dev / nafal_mvp_prod
User: dev_eatingrabbit / prod_eatingrabbit
Password: <요청>
Allowed IP: <팀원 공인 IP>
```
