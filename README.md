# 공지봇 — AI 대학교 공지사항 챗봇

## 📁 프로젝트 개요

- n8n 워크플로우가 학교·학과 공지사항을 자동 크롤링하고, BGE-M3 임베딩 + pgvector 유사도 검색으로 관련 공지를 찾아 LLM이 자연어로 답변하는 RAG 기반 AI 챗봇 서비스입니다.
- 가입 시 선택한 학교·학과 범위 내 공지만 검색 대상으로 삼아 개인화된 답변을 제공하며, 타학과 공지는 DB 레벨에서 차단합니다.
- 질문 의도를 자동 분류(개수 집계 / 최신 조회 / 목록 / 유사도 검색)하여 단순 RAG 한계를 보완한 팀 프로젝트입니다.
- 프로젝트 기간 : 2025.04.28 ~ 2025.06.24

## 🤝 팀 소개

<table border="1px solid">
  <thead>
    <tr><td colspan="3" align="center">LLM 챗봇 Project</td></tr>
  </thead>
  <tr align="center">
    <td>이이언 (최수호)</td>
    <td>박영수</td>
    <td>유경민</td>
  </tr>
  <tr>
    <td>
      <a href="https://github.com/Hasegos">
        <img src="https://avatars.githubusercontent.com/u/93961708?v=4" width="200" height="200" alt="깃허브 페이지 바로가기">
      </a>
    </td>
    <td>
      <a href="https://github.com/xuxtaku7610-del">
        <img src="https://avatars.githubusercontent.com/u/245087152?v=4" width="200" height="200" alt="깃허브 페이지 바로가기">
      </a>
    </td>
    <td>
      <a href="https://github.com/ykm-63">
        <img src="https://avatars.githubusercontent.com/u/264807334?v=4" width="200" height="200" alt="깃허브 페이지 바로가기">
      </a>
    </td>
  </tr>
</table>

## 🛠️ 기술 스택

+ **Backend** :<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">

+ **Frontend** : <img src="https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white"> <img src="https://img.shields.io/badge/css-1572B6?style=for-the-badge&logo=css3&logoColor=white"> <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=JavaScript&logoColor=white">

+ **Database** : <img src="https://img.shields.io/badge/postgresql-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">

+ **AI / LLM** : <img src="https://img.shields.io/badge/vLLM-412991?style=for-the-badge&logo=ai&logoColor=white"> <img src="https://img.shields.io/badge/Llama 3.1 70B-FF6600?style=for-the-badge&logo=meta&logoColor=white"> <img src="https://img.shields.io/badge/BGE--M3-FF6F00?style=for-the-badge&logo=huggingface&logoColor=white"> <img src="https://img.shields.io/badge/NVIDIA RTX 5090-76B900?style=for-the-badge&logo=nvidia&logoColor=white">

+ **자동화 / 크롤링** : <img src="https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white">

+ **Infra** : <img src="https://img.shields.io/badge/OpenStack-ED1944?style=for-the-badge&logo=openstack&logoColor=white"> <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">

+ **Tooling** : <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white"> <img src="https://img.shields.io/badge/notion-000?style=for-the-badge&logo=Notion&logoColor=white"> <img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white">

## 🗏 페이지 구성

### 홈 페이지

<img width="800" alt="홈페이지" src="assets/screenshots/01_home.png" />
<img width="800" alt="홈페이지" src="assets/screenshots/02_home.png" />

<br>

+ 학교·학과 셀렉트박스로 가입 진입
+ RAG 파이프라인 터미널 데모 시각화
+ AI 자동 요약 / 의미 기반 검색 / 학교·학과 맞춤 / 대화형 채팅 기능 소개

### 로그인 / 회원가입 페이지

<img width="800" alt="로그인" src="assets/screenshots/login.png" />
<img width="800" alt="회원가입" src="assets/screenshots/register.png" />

<br>

+ 이메일·비밀번호 기반 회원가입 / 로그인
+ 가입 시 학교·학과 선택 → 개인화된 공지 범위 설정
+ 비밀번호: 영문 + 숫자 + 특수문자 8자 이상 검증
+ 로그인 시 JWT HttpOnly 쿠키 발급 (XSS 방어)

### 공지사항 페이지

<img width="800" alt="공지사항" src="assets/screenshots/01_notices.png" />
<img width="800" alt="공지사항" src="assets/screenshots/02_notices.png" />
<img width="600" alt="공지사항" src="assets/screenshots/03_notices.png" />

<br>

+ 학교 공지 + 내 학과 공지 통합 조회 (타학과 공지 차단)
+ 사이드바 필터: 전체 / 학교 공지 / 학과 공지 분류
+ 공지 카드 클릭 시 본문 상세 모달 표시
+ 키워드 검색 (300ms 디바운스)
+ 페이지네이션 윈도잉 처리 (`‹ 1 … 20 21 [22] 23 24 … 43 ›`)

### AI 챗봇 페이지

<img width="800" alt="채팅" src="assets/screenshots/chat.png" />

<br>

+ 자연어 질문 → RAG 기반 공지 검색 → LLM 답변 생성
+ 질문 의도 자동 분류:
  + 개수 질문 → DB 직접 집계 후 응답
  + 최신/목록 질문 → 최신순 DB 조회 후 응답
  + 일반 질문 → pgvector 코사인 유사도 검색 (Top-5)
+ RAG 검색 범위: 내 학교 공지 + 내 학과 공지만
+ 공지 현황(학교/학과/전체 개수)을 매 요청마다 컨텍스트 주입
+ 채팅 세션 관리 (생성·조회·삭제)
+ 무관한 질문 자동 회피 처리

## 📊 ERD (Entity Relationship Diagram)

### 🗺️ ERD 개요

<img width="800" alt="공지사항" src="assets/screenshots/ERD.png" />

| 테이블 | 설명 |
|---|---|
| `schools` | 학교 정보 + n8n 크롤링 URL |
| `departments` | 학과 정보 + 학과 공지 URL |
| `users` | 사용자 계정 (school_id · dept_id FK) |
| `notices` | 크롤링된 공지 + LLM 요약 + 임베딩 벡터 (vector 1024) |
| `chat_sessions` | 채팅 세션 |
| `chat_messages` | 채팅 메시지 (role: user/assistant) |

### 📚 프로젝트 문서 / 회고

- 기획, 요구사항 정의, ERD 상세, 화면 설계, 회고(트러블슈팅 포함)는 아래 노션에 정리했습니다.
    - Notion: [학교 공지사항 LLM 챗봇 프로젝트 문서](https://www.notion.so/LLM-360be056f649807ea2b9e99b21dc8b75)

## 📌 API 명세표

### 페이지 라우터
 
| 기능 구분 | HTTP 메서드 | URL | 설명 | 접근 권한 |
|---|---|---|---|---|
| 🏠 홈 페이지 | GET | / | 홈 화면 (학교·학과 셀렉트) | 🔓 모두 가능 |
| 🔑 로그인 페이지 | GET | /login | 로그인 폼 페이지 | 🔓 모두 가능 |
| 📝 회원가입 페이지 | GET | /register | 회원가입 폼 페이지 | 🔓 모두 가능 |
| 💬 채팅 페이지 | GET | /chat | AI 챗봇 채팅 화면 | 🔐 로그인 필요 |
| 📢 공지사항 페이지 | GET | /notices | 공지사항 목록 화면 | 🔐 로그인 필요 |
 
### API 엔드포인트
 
| 기능 구분 | HTTP 메서드 | URL | 설명 | 접근 권한 |
|---|---|---|---|---|
| 📝 회원가입 처리 | POST | /api/auth/register | 신규 사용자 등록 | 🔓 모두 가능 |
| 🔑 로그인 처리 | POST | /api/auth/login | 로그인 → JWT 쿠키 발급 | 🔓 모두 가능 |
| 🚪 로그아웃 처리 | POST | /api/auth/logout | 쿠키 삭제 → 홈 리다이렉트 | 🔐 로그인 필요 |
| 👤 내 정보 조회 | GET | /api/auth/me | 로그인된 사용자 정보 반환 | 🔐 로그인 필요 |
| 🏫 학교 목록 조회 | GET | /api/schools | 활성화된 학교 목록 반환 | 🔓 모두 가능 |
| 🏢 학과 목록 조회 | GET | /api/schools/{school_id}/departments | 학교별 학과 목록 반환 | 🔓 모두 가능 |
| 📋 공지 목록 조회 | GET | /api/notices | 학교 공지 + 내 학과 공지 목록 | 🔐 로그인 필요 |
| 📄 공지 상세 조회 | GET | /api/notices/{notice_id} | 공지 상세 본문 (타학교 403 차단) | 🔐 로그인 필요 |
| 💬 채팅 메시지 전송 | POST | /api/chat | 질문 전송 → RAG → LLM 응답 | 🔐 로그인 필요 |
| 📂 세션 목록 조회 | GET | /api/chat/sessions | 내 채팅 세션 목록 | 🔐 로그인 필요 |
| 📂 세션 상세 조회 | GET | /api/chat/sessions/{session_id} | 세션 메시지 목록 포함 상세 | 🔐 로그인 필요 |
| 🗑️ 세션 삭제 | DELETE | /api/chat/sessions/{session_id} | 세션 + 메시지 삭제 (소유권 검증) | 🔐 로그인 필요 |

## 🔐 보안 설계

| 항목 | 구현 |
|---|---|
| 비밀번호 | bcrypt 해싱 |
| 인증 | JWT HttpOnly 쿠키 (XSS 방어) |
| CSRF | SameSite=Lax |
| SQL 인젝션 | SQLAlchemy ORM + 바인딩 파라미터 + 이름 필드 패턴 차단 |
| XSS | innerHTML 전면 제거 → DOM API만 사용 |
| 공지 접근 제어 | school_id 비교 (타학교 공지 403 차단) |
| 세션 소유권 | user_id 비교 검증 (403 반환) |
| RAG 범위 제한 | 내 학교 + 내 학과 공지만 벡터 검색 대상 |
| 500 에러 | 스택트레이스 숨김, 일반 메시지만 반환 |

## 📁 디렉토리 구조

```
openstack-ai-notice-chatbot/
├── 🚀 main.py                        # FastAPI 앱 진입점
│
├── ⚙️ core/
│   ├── config.py                     # Settings (DB · JWT · vLLM · SYSTEM_PROMPT)
│   ├── security.py                   # bcrypt + JWT 생성/검증
│   ├── auth.py                       # 쿠키 기반 optional/required 인증
│   ├── exception.py                  # 전역 예외 처리 (401→/login, 404→/, 500→error.html)
│   └── templates.py                  # Jinja2 설정
│
├── 🗄️ db/
│   ├── base_class.py
│   ├── base.py                       # 모든 모델 import 집결
│   └── session.py
│
├── 🧩 models/
│   ├── school_model.py
│   ├── department_model.py
│   ├── user_model.py
│   ├── notice_model.py               # embedding 컬럼 (vector 1024) 포함
│   ├── chat_session_model.py
│   └── chat_message_model.py
│
├── 📨 schemas/
│   ├── user_schema.py
│   ├── school_schema.py
│   ├── notice_schema.py              # NoticeOut · NoticeDetail (content 포함)
│   └── chat_schema.py
│
├── 🗂️ crud/
│   ├── user_crud.py
│   ├── school_crud.py
│   ├── notice_crud.py                # RAG 검색 · 집계 · 최신 조회 포함
│   └── chat_crud.py
│
├── 🧭 api/
│   ├── routers.py                    # /api/auth · /api/schools · /api/notices · /api/chat
│   ├── pages.py                      # 페이지 라우터 5개
│   └── endpoints/
│       ├── user_endpoint.py          # 회원가입 · 로그인 · 로그아웃 · 내 정보
│       ├── school_endpoint.py        # 학교 목록 · 학과 목록
│       ├── notice_endpoint.py        # 공지 목록 · 공지 상세
│       └── chat_endpoint.py          # 채팅 · 세션 CRUD · RAG 파이프라인
│
├── 📄 templates/
│   ├── partials/                     # 공통 레이아웃
│   │   ├── head_meta.html
│   │   ├── header.html
│   │   └── footer.html
│   ├── 🏠 home.html
│   ├── 🔐 login.html
│   ├── 📝 register.html
│   ├── 💬 chat.html
│   ├── 📢 notices.html
│   └── ⚠️ error.html
│
└── 🌐 static/
    ├── 🎨 css/
    │   ├── common.css
    │   ├── home.css
    │   ├── login.css
    │   ├── register.css
    │   ├── chat.css
    │   ├── notices.css
    │   └── error.css
    └── ⚙️ js/
        ├── apiClient.js              # 공통 API 요청 · 401/422 처리
        ├── home.js
        ├── login.js
        ├── register.js
        ├── chat.js                   # 세션 CRUD · 로딩버블 · 예시버튼
        └── notices.js                # 필터 · 검색 · 모달 · 페이지네이션
```