import streamlit as st
import pandas as pd
import os
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta, timezone
import base64
import gspread
from google.oauth2.service_account import Credentials

# --- [중요] 폰트 및 이미지 설정 ---
FONT_FILE = 'malgunbd.ttf' 
BG_IMAGE_FILE = 'bounty_bg.png' 
SHEET_NAME = 'Holdem_Ranking' 

# --- [설정] 디자인 컬러 팔레트 ---
COLOR_TEXT_MAIN = "#3E2723" 
COLOR_RED = "#B71C1C"       
COLOR_GOLD = "#FFD700"      
COLOR_BROWN_BAR = "#8D6E63" 
COLOR_LIGHT_TEXT = "#EFEBE9" 

# --- [시간] 한국 시간 월 구하기 ---
def get_current_month():
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).month

CURRENT_MONTH = get_current_month()

# --- [함수] 이미지 Base64 인코딩 ---
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

bg_base64 = get_image_base64(BG_IMAGE_FILE)

# --- [디자인] Streamlit 웹 테마 ---
st.set_page_config(page_title="ACE's Wanted List", page_icon="🤠", layout="wide")

st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Rye&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bg_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: {COLOR_TEXT_MAIN};
        font-family: 'Playfair Display', serif;
    }}
    .main-title {{
        color: {COLOR_RED} !important;
        font-family: 'Rye', cursive !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        text-transform: uppercase;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 20px;
    }}
    [data-testid="stSidebar"] {{
        background-color: #161B22; 
        border-right: 1px solid #FFD700; 
        color: #FFFFFF;
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    .stSelectbox label, .stTextInput label, .stTextArea label {{
        color: #FFD700 !important;
        font-family: 'Helvetica', sans-serif !important;
    }}
    /* 4. 버튼 스타일 (검정 배경 + 금색 글씨) */
    .stButton>button {{
        color: #FFD700 !important; 
        background-color: #000000 !important; 
        border: 1px solid #FFD700 !important; 
        font-weight: bold;
        width: 100%;
        font-family: 'Helvetica', sans-serif;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #FFD700 !important; 
        color: #000000 !important; 
        border: 1px solid #000000 !important;
    }}
    table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 10px;
        color: {COLOR_TEXT_MAIN};
        margin-bottom: 20px;
    }}
    th {{
        font-family: 'Rye', cursive;
        font-size: 1.2rem;
        color: {COLOR_TEXT_MAIN};
        padding: 10px;
        text-align: center;
        border-bottom: 3px double {COLOR_TEXT_MAIN};
    }}
    tr.wanted-poster {{
        background-color: rgba(255, 248, 225, 0.8);
        box-shadow: 5px 5px 10px rgba(0,0,0,0.2);
        border: 2px solid {COLOR_TEXT_MAIN};
        border-radius: 5px;
    }}
    td {{
        padding: 5px;
        text-align: center;
        font-size: 1.1rem;
        vertical-align: middle;
        border-top: 2px solid {COLOR_TEXT_MAIN};
        border-bottom: 2px solid {COLOR_TEXT_MAIN};
        font-family: 'Playfair Display', serif;
    }}
    tr.wanted-poster td:first-child {{ border-left: 2px solid {COLOR_TEXT_MAIN}; border-radius: 5px 0 0 5px; }}
    tr.wanted-poster td:last-child {{ border-right: 2px solid {COLOR_TEXT_MAIN}; border-radius: 0 5px 5px 0; }}
    </style>
    """.format(bg_base64=bg_base64, COLOR_TEXT_MAIN=COLOR_TEXT_MAIN, COLOR_RED=COLOR_RED), unsafe_allow_html=True)

# --- [함수] 구글 시트 연결 및 데이터 로드/저장 ---
@st.cache_resource
def init_connection():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"🔌 구글 연결 설정 오류: {e}")
        return None

# --- [함수] 데이터 로드 (6행~26행 사이의 데이터만 읽기) ---
def load_data():
    client = init_connection()
    default_df = pd.DataFrame(columns=['닉네임', '점수'])
    if not client: return default_df

    try:
        sheet = client.open(SHEET_NAME).sheet1
        
        # [수정] 범위를 명확하게 '26행'까지로 제한
        # 27행 아래에 있는 데이터는 랭킹으로 인식하지 않기 위함입니다.
        ranges = sheet.batch_get(['A6:C26', 'D6:F26'])
        
        left_data = ranges[0]  # 1~20등 위치
        right_data = ranges[1] # 21~40등 위치
        
        all_data = left_data + right_data
        
        if not all_data: 
            return default_df
        
        # 컬럼명 수동 지정
        df = pd.DataFrame(all_data, columns=['순위', '닉네임', '점수'])
        
        df = df[['닉네임', '점수']]
        df['닉네임'] = df['닉네임'].astype(str).str.strip()
        df['점수'] = pd.to_numeric(df['점수'], errors='coerce').fillna(0)
        
        # 빈 값 제거
        df = df[df['닉네임'] != ""]
        
        return df
        
    except Exception as e:
        return default_df

# --- [함수] 데이터 저장 (27행 밑으로는 건드리지 않음) ---
def save_data(df):
    client = init_connection()
    if not client: return

    try:
        sheet = client.open(SHEET_NAME).sheet1
        
        # 1. 정렬 및 순위 계산
        df['점수'] = df['점수'].astype(float)
        df_sorted = df.sort_values(by=['점수'], ascending=False).reset_index(drop=True)
        df_sorted['순위'] = df_sorted['점수'].rank(method='min', ascending=False).astype(int)
        
        final_df = df_sorted[['순위', '닉네임', '점수']]
        
        # 2. 데이터 분리
        df_left = final_df.iloc[0:20]   # 1~20등
        df_right = final_df.iloc[20:40] # 21~40등
        
        # 3. [핵심 수정] 청소 범위를 '26행'까지로 고정
        # 기존에는 F1000까지 지웠지만, 이제는 26행까지만 지웁니다.
        sheet.batch_clear(['A6:C26', 'D6:F26'])
        
        # 4. 데이터 업데이트
        if not df_left.empty:
            sheet.update(range_name='A6', values=df_left.values.tolist())
            
        if not df_right.empty:
            sheet.update(range_name='D6', values=df_right.values.tolist())
            
    except Exception as e:
        st.error(f"💾 저장 실패: {e}")

# --- [로직] 점수 규칙 ---
SCORE_RULES = {
    "3 FREE": {"normal": [7, 5, 3], "2chop": 7, "3chop": 6, "4chop": 5, "rebuy": 0.5},
    "5 FREE": {"normal": [10, 7, 5], "2chop": 10, "3chop": 9, "4chop": 8, "rebuy": 1.0}
}

# --- [이미지 생성] 동점자 처리 적용 ---
def create_ranking_image(df):
    W, H = 1000, 1400
    try:
        image = Image.open(BG_IMAGE_FILE).resize((W, H))
    except FileNotFoundError:
        st.error(f"⚠️ 배경 이미지('{BG_IMAGE_FILE}')가 없습니다.")
        return None
    draw = ImageDraw.Draw(image)

    try:
        font_main = ImageFont.truetype(FONT_FILE, 30)
        font_title_big = ImageFont.truetype(FONT_FILE, 100)
        font_title_sub = ImageFont.truetype(FONT_FILE, 45)
        font_nick = ImageFont.truetype(FONT_FILE, 32)
        font_score = ImageFont.truetype(FONT_FILE, 28)
        font_rank = ImageFont.truetype(FONT_FILE, 34) 
    except IOError:
        st.error(f"⚠️ 폰트 파일('{FONT_FILE}')이 없습니다.")
        return None

    draw.text((W/2, 80), "WANTED", font=font_title_big, fill=COLOR_RED, anchor="mm")
    draw.text((W/2, 160), f"ACE's PUB - {CURRENT_MONTH}월 현상 수배자", font=font_title_sub, fill=COLOR_TEXT_MAIN, anchor="mm")
    draw.line((100, 190, W-100, 190), fill=COLOR_TEXT_MAIN, width=5)

    start_y = 230
    col_widths = [60, 240, 100]
    block_margin = 80
    poster_height = 45
    poster_gap = 10

    # 랭킹 계산 (동점자 처리)
    df['점수'] = df['점수'].astype(float)
    ranked_df = df.sort_values(by=['점수'], ascending=False).reset_index(drop=True)
    ranked_df['순위'] = ranked_df['점수'].rank(method='min', ascending=False).astype(int)
    ranked_df = ranked_df.head(40)

    total_table_width = (sum(col_widths) * 2) + block_margin
    start_x = (W - total_table_width) / 2

    current_x = start_x
    for block_idx in range(2):
        current_y = start_y
        
        headers = ["Rank", "Name", "Bounty"]
        for i, h_text in enumerate(headers):
            hx = current_x + sum(col_widths[:i]) + col_widths[i]/2
            draw.text((hx, current_y), h_text, font=font_main, fill=COLOR_TEXT_MAIN, anchor="mm")
        
        current_y += 30
        draw.line((current_x, current_y, current_x + sum(col_widths), current_y), fill=COLOR_TEXT_MAIN, width=3)
        current_y += 20

        start_rank_idx = block_idx * 20
        end_rank_idx = start_rank_idx + 20
        block_data = ranked_df.iloc[start_rank_idx:end_rank_idx]

        for i in range(20):
            if i < len(block_data):
                row = block_data.iloc[i]
                rank = row['순위'] # 실제 계산된 순위 사용
                nick = row['닉네임']
                score = f"${row['점수']:.1f}"
                
                poster_rect = [current_x, current_y, current_x + sum(col_widths), current_y + poster_height]
                draw.rectangle(poster_rect, fill="#FFF8E1", outline=COLOR_TEXT_MAIN, width=2)
                
                draw.text((current_x + col_widths[0]/2, current_y + poster_height/2), str(rank), font=font_rank, fill=COLOR_TEXT_MAIN, anchor="mm")
                draw.text((current_x + col_widths[0] + col_widths[1]/2, current_y + poster_height/2), nick, font=font_nick, fill=COLOR_TEXT_MAIN, anchor="mm")
                draw.text((current_x + col_widths[0] + col_widths[1] + col_widths[2]/2, current_y + poster_height/2), score, font=font_score, fill=COLOR_TEXT_MAIN, anchor="mm")
                
            current_y += poster_height + poster_gap
        current_x += sum(col_widths) + block_margin

    # 규칙표 (기존 유지)
    rule_start_y = current_y + 50
    draw.line((100, rule_start_y-20, W-100, rule_start_y-20), fill=COLOR_TEXT_MAIN, width=5)
    draw.text((W/2, rule_start_y), "BOUNTY RULES", font=font_title_sub, fill=COLOR_TEXT_MAIN, anchor="mm")
    
    rule_start_y += 40
    rule_header_w = 160
    rule_val_w = 110
    rule_row_h = 45
    
    rules_data = [
        ["3 FREE", "1st", "$7", "2nd", "$5", "3rd", "$3", "Rebuy", "$0.5"],
        ["", "1st-2Chop", "$7", "3-Chop", "$6", "4-Chop", "$5", "", ""],
        ["5 FREE ↑", "1st", "$10", "2nd", "$7", "3rd", "$5", "Rebuy", "$1"],
        ["", "1st-2Chop", "$10", "3-Chop", "$9", "4-Chop", "$8", "", ""]
    ]

    curr_ry = rule_start_y
    for r_data in rules_data:
        curr_rx = (W - (rule_header_w + rule_val_w*8)) / 2
        for col_idx, cell_text in enumerate(r_data):
            cell_w = rule_header_w if col_idx == 0 else rule_val_w
            if cell_text:
                draw.rectangle([curr_rx, curr_ry, curr_rx+cell_w, curr_ry+rule_row_h], fill=COLOR_BROWN_BAR, outline=COLOR_TEXT_MAIN, width=2)
                is_header = (col_idx == 0 or (col_idx > 0 and col_idx % 2 != 0))
                fill_c = COLOR_GOLD if is_header else COLOR_LIGHT_TEXT
                f_size = font_main if is_header else font_score
                draw.text((curr_rx + cell_w/2, curr_ry + rule_row_h/2), cell_text, font=f_size, fill=fill_c, anchor="mm")
            curr_rx += cell_w
        curr_ry += rule_row_h

    return image

# ==========================================
# 메인 앱 시작
# ==========================================
st.markdown(f"<div class='main-title'>🤠 WANTED: ACE's {CURRENT_MONTH}월 현상 수배자들</div>", unsafe_allow_html=True)

df = load_data()
existing_players = sorted([str(p) for p in df['닉네임'].unique() if p != "nan" and p != ""])

# --- [사이드바] 블랙 & 골드 스타일 유지 ---
st.sidebar.markdown("### 📝 경기 결과 입력")
col1, col2 = st.sidebar.columns(2)
game_type = col1.selectbox("게임 종류", ["3 FREE", "5 FREE"])
result_type = col2.selectbox("결과 유형", ["일반 (1/2/3등)", "1등 2찹", "3찹", "4찹"])
st.sidebar.markdown("---")

with st.sidebar.form("game_input", clear_on_submit=True):
    st.markdown("#### 1. 입상자 입력")
    winners = [] 
    if result_type == "일반 (1/2/3등)":
        w1, w2, w3 = st.text_input("🥇 1등"), st.text_input("🥈 2등"), st.text_input("🥉 3등")
        winners = [(w1, 0), (w2, 1), (w3, 2)]
    elif result_type == "1등 2찹":
        st.markdown("**🤝 1등 찹 (2명)**")
        c1, c2 = st.text_input("찹 1"), st.text_input("찹 2")
        winners.extend([(c1, '2chop'), (c2, '2chop')])
        st.markdown("**⬇️ 추가 순위**")
        w2, w3 = st.text_input("🥈 2등"), st.text_input("🥉 3등")
        winners.extend([(w2, 1), (w3, 2)])
    elif result_type == "3찹":
        st.markdown("**🤝 3명 찹**")
        c1, c2, c3 = st.text_input("찹 1"), st.text_input("찹 2"), st.text_input("찹 3")
        winners.extend([(c1, '3chop'), (c2, '3chop'), (c3, '3chop')])
        st.markdown("**⬇️ 추가 순위**")
        w2, w3 = st.text_input("🥈 2등"), st.text_input("🥉 3등")
        winners.extend([(w2, 1), (w3, 2)])
    elif result_type == "4찹":
        st.markdown("**🤝 4명 찹**")
        c1, c2, c3, c4 = st.text_input("찹 1"), st.text_input("찹 2"), st.text_input("찹 3"), st.text_input("찹 4")
        winners.extend([(c1, '4chop'), (c2, '4chop'), (c3, '4chop'), (c4, '4chop')])
        st.markdown("**⬇️ 추가 순위**")
        w2, w3 = st.text_input("🥈 2등"), st.text_input("🥉 3등")
        winners.extend([(w2, 1), (w3, 2)])

    st.markdown("---")
    st.markdown("#### 2. 리바인 입력")
    rebuy_text = st.text_area("리바인 명단 (예: 스틴 2)", height=80)
    
    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.form_submit_button("🏆 점수 반영 및 저장")

if submit_btn:
    rule = SCORE_RULES[game_type]
    updates = {} 
    for name, rank in winners:
        if name: name = str(name).strip()
        if name:
            pt = rule['normal'][rank] if isinstance(rank, int) else rule[rank]
            updates[name] = updates.get(name, 0) + pt
    if rebuy_text:
        for line in rebuy_text.replace(',', '\n').split('\n'):
            parts = line.strip().split()
            if not parts: continue
            try: count = int(parts[-1]); name = " ".join(parts[:-1])
            except: count = 1; name = " ".join(parts)
            if name: updates[name] = updates.get(name, 0) + (count * rule['rebuy'])

    if not updates: 
        st.warning("⚠️ 입력된 정보가 없습니다.")
    else:
        # 데이터프레임 업데이트 (참여횟수 로직 제거됨)
        for name, point in updates.items():
            if name in df['닉네임'].values:
                df.loc[df['닉네임'] == name, '점수'] += point
            else:
                new_row = pd.DataFrame({'닉네임': [name], '점수': [point]})
                df = pd.concat([df, new_row], ignore_index=True)
        
        save_data(df)
        st.success(f"✅ 구글 시트 저장 완료! ({len(updates)}명 반영)")
        st.rerun()

# --- [사이드바] 데이터 관리 ---
st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
with st.sidebar.expander("🗑️ 닉네임 삭제 (관리자용)"):
    delete_targets = st.multiselect("삭제할 닉네임", existing_players)
    if st.button("❌ 선택 삭제"):
        if delete_targets:
            new_df = df[~df['닉네임'].isin(delete_targets)]
            save_data(new_df)
            st.success("삭제 완료."); st.rerun()

# =========================================================
# [메인 화면] 랭킹 보드
# =========================================================
if not df.empty:
    df['점수'] = df['점수'].astype(float)
    # 정렬 및 순위 계산 (동점자 처리)
    rank_df = df.sort_values(by=['점수'], ascending=False).reset_index(drop=True)
    rank_df['순위'] = rank_df['점수'].rank(method='min', ascending=False).astype(int)
    
    max_val = rank_df['점수'].max()

    def make_html_table(sub_df):
        if sub_df.empty: return ""
        
        html_parts = []
        html_parts.append('<table><thead><tr><th style="width:20%">Rank</th><th style="width:50%">Outlaw Name</th><th style="width:30%">Bounty</th></tr></thead><tbody>')
        
        for idx, row in sub_df.iterrows():
            percent = (row['점수'] / max_val * 100) if max_val > 0 else 0
            rank = row['순위'] # 계산된 순위 사용
            
            bar_c = COLOR_BROWN_BAR 
            txt_c = COLOR_LIGHT_TEXT
            
            nick_style = f"color: {COLOR_TEXT_MAIN}; font-weight: bold;"
            
            bar_style = f"""
                background: linear-gradient(90deg, {bar_c} {percent:.1f}%, rgba(141,110,99,0.3) {percent:.1f}%);
                color: {txt_c};
                font-weight: bold;
                text-align: left;
                padding-left: 10px;
                border-radius: 4px;
                box-shadow: inset 1px 1px 3px rgba(0,0,0,0.3);
            """
            
            row_html = f'<tr class="wanted-poster"><td style="text-align:center; font-weight:bold;">{rank}</td><td style="text-align:center; {nick_style}">{row["닉네임"]}</td><td style="{bar_style}">${row["점수"]:.1f}</td></tr>'
            html_parts.append(row_html)
            
        html_parts.append('</tbody></table>')
        return "".join(html_parts)

    col1, col2 = st.columns(2)
    df_top20 = rank_df.iloc[0:20]
    df_next20 = rank_df.iloc[20:40]
    
    with col1:
        st.markdown(make_html_table(df_top20), unsafe_allow_html=True)
    with col2:
        if not df_next20.empty:
            st.markdown(make_html_table(df_next20), unsafe_allow_html=True)

    st.markdown("<br><hr style='border:1px solid #3E2723'>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📜 현상 수배지(이미지) 발행"):
            with st.spinner("수배지 인쇄 중..."):
                img = create_ranking_image(df)
                if img:
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.download_button("📥 수배지 다운로드", buf.getvalue(), f"wanted_list_{CURRENT_MONTH}.png", "image/png")
    with col_b:
        st.download_button("📂 장부(엑셀) 다운로드", rank_df.to_csv(index=False).encode('utf-8-sig'), "bounty_ledger.csv", "text/csv")
    
    with st.expander("🛠️ 장부 직접 수정 (보안관용)"):
        # 순위 컬럼은 수정 불가하게 설정할 수도 있지만, 여기선 간단히 전체 표시
        edited_df = st.data_editor(rank_df, use_container_width=True, num_rows="dynamic")
        if st.button("💾 수정 사항 기록"):
            save_data(edited_df[['닉네임', '점수']])
            st.success("장부가 구글 시트에 수정되었습니다."); st.rerun()

else:
    st.info("👈 사이드바에서 첫 번째 현상범을 등록해주세요! (구글 시트 연동 완료)")