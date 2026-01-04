# 🤠 ACE's Wanted List - 홀덤 펍 랭킹 관리 시스템

**"ACE 홀덤 펍의 월간 현상수배자(랭커)들을 관리하는 웹 애플리케이션"**

이 프로젝트는 Python **Streamlit**을 기반으로 제작된 홀덤 펍 전용 랭킹 관리 시스템입니다. 
서부 영화의 **'Wanted Poster(현상수배지)'** 콘셉트를 차용하여, 단순한 점수 기록을 넘어 플레이어들에게 재미와 몰입감을 제공합니다.

## ✨ 주요 기능 (Key Features)

* **📊 실시간 랭킹 대시보드**: 
    * Google Sheets와 연동되어 실시간으로 점수가 반영됩니다.
    * 1~40위까지 한눈에 볼 수 있는 2단 레이아웃을 제공합니다.
    * 동점자 발생 시 동일 순위 처리(1, 2, 2, 4...) 로직이 적용되어 있습니다.
* **🎨 커스텀 디자인**:
    * 서부 시대 느낌의 갈색 톤 UI와 빈티지한 폰트를 적용했습니다.
    * HTML/CSS를 활용한 커스텀 게이지 바(Bar)로 점수를 시각화했습니다.
* **🖼️ 수배지 이미지 생성 (Pillow)**:
    * 현재 랭킹을 'WANTED' 포스터 이미지로 자동 생성합니다.
    * 버튼 클릭 한 번으로 PNG 파일을 다운로드하여 SNS 공유 등에 활용할 수 있습니다.
* **☁️ Google Sheets 연동**:
    * 별도의 데이터베이스 서버 없이 구글 시트를 백엔드 DB로 사용합니다.
    * 데이터는 시트의 **6행**부터 저장되어, 상단(1~5행)을 자유롭게 꾸밀 수 있습니다.
    * 1-20위는 왼쪽(A열), 21-40위는 오른쪽(D열)에 저장되는 직관적인 구조입니다.

## 🛠️ 기술 스택 (Tech Stack)

* **Language**: Python 3.9+
* **Framework**: Streamlit
* **Data Processing**: Pandas
* **Image Processing**: Pillow (PIL)
* **Database**: Google Sheets API (gspread, oauth2)

## 📂 프로젝트 구조 (Directory Structure)

```bash
holdem-ranking/
├── app.py               # 메인 애플리케이션 코드
├── requirements.txt     # 의존성 라이브러리 목록
├── packages.txt         # (선택) 시스템 패키지 설정
├── bounty_bg.png        # 배경 이미지 리소스
├── malgunbd.ttf         # 폰트 파일
└── .streamlit/
    └── secrets.toml     # [주의] 구글 API 키 (깃허브 업로드 금지!)
```

## 🚀 설치 및 실행 방법 (Installation)
이 프로젝트를 로컬 컴퓨터에서 실행하려면 다음 단계가 필요합니다.

1. 저장소 복제 (Clone)
Bash
git clone [https://github.com/YOUR_ID/holdem-ranking.git](https://github.com/YOUR_ID/holdem-ranking.git)
cd holdem-ranking

2. 가상환경 설정 및 라이브러리 설치
```Bash
### 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

### 라이브러리 설치
pip install -r requirements.txt
```

3. Google Cloud 인증 설정 (필수)
프로젝트 루트에 .streamlit 폴더를 만들고 secrets.toml 파일을 생성하여 구글 서비스 계정 키를 입력해야 합니다.
```
.streamlit/secrets.toml

Ini, TOML

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----..."
client_email = "your-service-account-email"
...
```
4. 앱 실행
```Bash
streamlit run app.py
```

### 📋 구글 시트 설정 가이드

Google Sheets를 새로 생성하고 이름을 코드의 SHEET_NAME과 동일하게 설정합니다. (기본값: Holdem_Ranking)

secrets.toml에 있는 client_email 주소를 해당 시트의 '편집자(Editor)' 로 초대합니다.

데이터는 6행부터 자동으로 기록됩니다. 1~5행에는 자유롭게 로고나 안내 문구를 넣으세요.


## 📄 라이선스
This project is licensed under the MIT License.
