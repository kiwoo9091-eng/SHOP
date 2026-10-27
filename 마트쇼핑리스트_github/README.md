# 🛒 오늘의 장보기 리스트

마트에서 살 것을 적어 두고, 장바구니에 담으면 체크하는 만화 스타일 장보기 앱입니다.
Python + Streamlit으로 만들었고, Streamlit Community Cloud에 무료로 배포할 수 있습니다.

## 기능
- 살 것 추가 · 수정 · 삭제 · 체크 (담은 것은 취소선 + "담았다!" 도장)
- 분류 7개: 🥬 채소·과일 · 🥩 정육·수산 · 🥛 유제품·계란 · 🍜 가공식품 · 🍪 과자·음료 · 🧻 생활용품 · 📦 기타
- 코너 · 상태(살 것/산 것) 필터, 정렬(기본 · 코너별 · 이름순 · 금액 높은순)
- 요약: 살 것 개수, 담은 것, 남은 예상 금액, 진행률
- 같은 이름을 또 적으면 "수량을 늘릴까요?" 확인
- CSV 백업 · 복원 (엑셀에서 열어도 한글이 깨지지 않음)
- 선택: 비밀번호 보호 (배포할 때 Secrets에 `APP_PASSWORD`를 넣으면 켜짐)

## 로컬에서 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```
브라우저에서 http://localhost:8501 이 열립니다. 데이터는 같은 폴더의 `shoplist.db`에 저장됩니다.

## 테스트
```bash
pip install -r requirements-dev.txt
python -m pytest            # 데이터·검증·CSV 단위 테스트
```
화면 테스트(Playwright)는 `tests/e2e.playwright.js` 맨 위 설명을 참고하세요.

---

## 🚀 배포하기 (Streamlit Community Cloud)

### 1. GitHub에 올릴 파일

| 올리기 ✅ | 설명 |
|-----------|------|
| `app.py` | 화면 (진입점) |
| `shoplist/` 폴더 전체 | `__init__.py`, `db.py`, `models.py`, `csv_io.py` |
| `requirements.txt` | 배포 서버가 설치할 패키지 (**꼭 필요**) |
| `.streamlit/config.toml` | 테마 색상 |
| `.gitignore` | 올리면 안 되는 파일 목록 |
| `README.md` | 이 설명서 |
| `tests/`, `pytest.ini`, `requirements-dev.txt` | 테스트용 (올려도 되고 안 올려도 됨) |
| `PRD.md`, `PROMPT.md`, `CLAUDE.md` | 문서 (올려도 되고 안 올려도 됨) |

| 올리지 않기 ❌ | 이유 |
|----------------|------|
| `shoplist.db`, `test_e2e.db` | 내 장보기 데이터 · 테스트 데이터 |
| `.streamlit/secrets.toml` | 비밀번호 |
| `__pycache__/`, `.pytest_cache/`, `screenshots/` | 실행하면 자동으로 생기는 파일 |

`.gitignore`에 위 파일들이 이미 들어 있어서, 아래처럼 `git add .`을 해도 자동으로 빠집니다.

### 2. 올리는 방법
GitHub에서 새 저장소(예: `mart-shoplist`)를 만든 뒤, 이 폴더에서:
```bash
git init
git add .
git status          # shoplist.db, secrets.toml이 목록에 없는지 확인!
git commit -m "장보기 리스트 앱"
git branch -M main
git remote add origin https://github.com/<내 아이디>/mart-shoplist.git
git push -u origin main
```
> 명령어가 어려우면 GitHub 저장소 화면의 **Add file → Upload files**로 위 ✅ 파일들을 끌어다 놓아도 됩니다.
> 이때 `.streamlit` 폴더는 이름이 점(.)으로 시작해서 탐색기에서 안 보일 수 있으니 꼭 함께 올리세요.

### 3. Streamlit Cloud에서 배포
1. https://share.streamlit.io 에 GitHub 계정으로 로그인
2. **Create app** → **Deploy a public app from GitHub**
3. Repository: `mart-shoplist`, Branch: `main`, Main file path: `app.py`
4. **Advanced settings** → Python 버전 3.12 선택
5. (비밀번호를 쓰려면) **Secrets** 칸에 입력:
   ```toml
   APP_PASSWORD = "원하는 비밀번호"
   ```
6. **Deploy!** → 몇 분 뒤 `https://<앱이름>.streamlit.app` 주소가 생깁니다
7. 휴대폰에서 주소를 열고 "홈 화면에 추가"하면 앱처럼 쓸 수 있어요

### ⚠️ 꼭 알아 두세요
- **데이터가 지워질 수 있어요.** Streamlit Cloud는 앱이 재시작되거나(오래 안 쓰면 잠들었다 깨어날 때 포함) 코드를 다시 올리면 서버의 `shoplist.db`가 초기화될 수 있습니다. 앱의 **💾 백업 · 복원**에서 가끔 CSV로 내보내 두세요.
- **주소를 아는 사람은 누구나 볼 수 있어요.** 혼자 쓰려면 위 5번의 비밀번호를 설정하세요.
- 로컬에서 비밀번호를 시험하려면 `.streamlit/secrets.toml` 파일에 `APP_PASSWORD = "1234"`를 적으면 됩니다 (이 파일은 git에 올라가지 않음).
