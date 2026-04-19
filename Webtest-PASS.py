import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(layout="wide", page_title="IMMLAB ONSITE AGENDA")

# --- CSS ÉP BẢNG CĂN GIỮA ---
st.markdown("""
    <style>
    [data-testid="stTable"] table { width: 100% !important; table-layout: fixed !important; }
    [data-testid="stTable"] th, [data-testid="stTable"] td { text-align: center !important; vertical-align: middle !important; word-wrap: break-word !important; }
    [data-testid="stTable"] th { 
        background-color: #1E2530 !important; 
        color: #FFFFFF !important; /* Dòng này ép chữ tiêu đề luôn có màu trắng */
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CƠ SỞ DỮ LIỆU & KHỞI TẠO BỘ NHỚ
# ==========================================
USER_DB = {
    "hoangquantran2201@gmail.com":      {"name": "Hoàng Quân",  "password": "immlab"},
    "ngvkhang123@gmail.com":            {"name": "Vĩnh Khang",  "password": "immlab"},
    "nttdmy1206@gmail.com":             {"name": "Diễm My",     "password": "immlab"},
    "baotranhuynh0523@gmail.com":       {"name": "Bảo Trân",    "password": "immlab"},
    "thanhhoangtt7@gmail.com":          {"name": "Thanh hoàng", "password": "immlab"},
    "phamaivy092@gmail.com":            {"name": "Ái Vy",       "password": "immlab"},
    "lthabh923@gmail.com":              {"name": "Hữu Phát",    "password": "immlab"},
    "nhimaidung987@gmail.com":          {"name": "Dung Nhi",    "password": "immlab"},
    "myanhphan.22092004@gmail.com":     {"name": "Mỹ Anh",      "password": "immlab"},
    "anhtai0125@gmail.com":             {"name": "Anh Tài",     "password": "immlab"},
    "phanngoc.huong0101@gmail.com":     {"name": "Ngọc Hương",  "password": "immlab"},
    "datnguyenn113@gmail.com":          {"name": "Thành Đạt",   "password": "immlab"},
    "tacocubing2231@gmail.com":         {"name": "Nguyên Khôi", "password": "immlab"},
    "byhoangtho@gmail.com":             {"name": "Hoàng Thơ",   "password": "immlab"},
    "boytruong70@gmail.com":            {"name": "Hoài Nguyên", "password": "immlab"},
    "phn759931@gmail.com":              {"name": "Thanh Phong", "password": "immlab"},
    "hangoct19@gmail.com":              {"name": "Gia Hưng",    "password": "immlab"},
    "nguyenhuudang2510@gmail.com":      {"name": "Hữu Đăng",    "password": "immlab"},
    "nguyenquocbinh290506@gmail.com":   {"name": "Quốc Bình",   "password": "immlab"},
    "thuyvy.y30i@gmail.com":            {"name": "Thúy Vy",     "password": "immlab"},
    "minhkhang180707@gmail.com":        {"name": "Minh Khang",  "password": "immlab"},
    "anhhthao273@gmail.com":            {"name": "Ánh Thảo",    "password": "immlab"},
    "tuongvinguyen.nttv2007@gmail.com": {"name": "Tường Vi",    "password": "immlab"},
    "nc.uyenvy@gmail.com":              {"name": "Uyên Vy",     "password": "immlab"},
    "nguyenhoangminhcan@gmail.com":     {"name": "Minh Can",    "password": "immlab"},
    "truongquocquan9a5@gmail.com":      {"name": "Quốc Quân",   "password": "immlab"},
    "phuockhangchu2345@gmail.com":      {"name": "Phước Khang", "password": "immlab"},
    "tamynhi2007@gmail.com":            {"name": "Mỹ Nhi",      "password": "immlab"},
    "tranhoanganhthu.anhthu@gmail.com": {"name": "Anh Thư",     "password": "immlab"},

    "admin@immlab.com": {"name": "Staff", "password": "immlabstaff"} 
}

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

if "logged_in_name" not in st.session_state:
    st.session_state.logged_in_name = None
    st.session_state.is_admin = False

# ==========================================
# KẾT NỐI GOOGLE SHEETS
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_from_sheets():
    try:
        # Lấy dữ liệu mới nhất từ tab "IMMLAB ONSITE AGENDA"
        return conn.read(worksheet="IMMLAB ONSITE AGENDA", ttl=0)
    except Exception as e:
        # Nếu chưa có dữ liệu hoặc lỗi, trả về bảng trống
        return pd.DataFrame(columns=["Dấu thời gian", "Tuần đăng ký"] + DAYS)

# Lấy dữ liệu thực tế từ Cloud
df_current = get_data_from_sheets()

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
now = datetime.now()
current_weekday = now.weekday() 

st.markdown("<h2 style='font-size: 26px; padding-bottom: 10px;'>TRANG THÔNG TIN ĐĂNG KÝ LỊCH CÓ MẶT TẠI LAB</h2>", unsafe_allow_html=True)

# --- PHẦN 1: KHU VỰC ĐĂNG KÝ (CẦN ĐĂNG NHẬP) ---
st.markdown("<h2 style='font-size: 26px; padding-bottom: 10px;'>1. Cập nhật lịch có mặt</h2>", unsafe_allow_html=True)
if st.session_state.logged_in_name is None:
    st.warning("🔒 Vui lòng đăng nhập bằng Gmail để có thể đăng ký lịch.")
    with st.expander("Bấm vào đây để ĐĂNG NHẬP", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            email_input = st.text_input("Tài khoản Gmail:")
        with col2:
            pass_input = st.text_input("Mật khẩu:", type="password")
        
        if st.button("Đăng nhập"):
            if email_input in USER_DB and USER_DB[email_input]["password"] == pass_input:
                st.session_state.logged_in_name = USER_DB[email_input]["name"]
                if email_input == "admin@immlab.com":
                    st.session_state.is_admin = True
                st.success("Đăng nhập thành công!")
                st.rerun()
            else:
                st.error("Sai tài khoản hoặc mật khẩu!")

else:
    col_info, col_logout = st.columns([4, 1])
    with col_info:
        st.success(f"👤 Đang đăng nhập dưới tên: **{st.session_state.logged_in_name}**")
    with col_logout:
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in_name = None
            st.session_state.is_admin = False
            st.rerun()

    if current_weekday == 6:
        st.info("Cổng đăng ký hiện đang MỞ: Mời bạn đăng ký")
        with st.form("registration_form"):
            current_user = st.session_state.logged_in_name
            st.write("Đánh dấu vào các ngày bạn sẽ có mặt tại Lab:")
            
            cols = st.columns(7)
            selected_days = {}
            for i, day in enumerate(DAYS):
                with cols[i]:
                    selected_days[day] = st.checkbox(day)
                    
            if st.form_submit_button("Gửi đăng ký"):
                if not any(selected_days.values()):
                    st.error("Vui lòng chọn ít nhất một ngày!")
                else:
                    timestamp = now.strftime("%d/%m %H:%M")
                    next_monday = now + timedelta(days=1)
                    next_sunday = now + timedelta(days=7)
                    week_str = f"{next_monday.strftime('%d/%m')} - {next_sunday.strftime('%d/%m')}"
                    
                    new_row = {"Dấu thời gian": timestamp, "Tuần đăng ký": week_str}
                    for day in DAYS:
                        new_row[day] = current_user if selected_days[day] else ""
                    
                    # Cập nhật thẳng lên Google Sheets
                    new_entry = pd.DataFrame([new_row])
                    updated_df = pd.concat([df_current, new_entry], ignore_index=True)
                    conn.update(worksheet="IMMLAB ONSITE AGENDA", data=updated_df)
                    
                    st.success("Đã ghi nhận thành công!")
                    st.cache_data.clear() # Xóa cache để bảng tải lại
                    st.rerun()
    else:
        st.warning("Cổng đăng ký hiện đang ĐÓNG. Bạn chỉ có thể đăng ký vào Chủ Nhật hàng tuần.")

st.markdown("---")

# --- PHẦN 2: DANH SÁCH ONSITE (CÔNG KHAI) ---
st.markdown("<h2 style='font-size: 26px; padding-bottom: 10px;'>2. Danh sách Onsite Agenda</h2>", unsafe_allow_html=True)
if not df_current.empty:
    display_df = df_current.copy()

    # Logic ẩn dữ liệu cũ sau 22h Chủ Nhật
    if current_weekday == 6 and now.hour >= 22:
        next_monday = now + timedelta(days=1)
        next_sunday = now + timedelta(days=7)
        week_next_str = f"{next_monday.strftime('%d/%m')} - {next_sunday.strftime('%d/%m')}"
        display_df = display_df[display_df["Tuần đăng ký"] == week_next_str]
        st.info(f"💡 Đã sau 22h Chủ Nhật: Chỉ hiển thị lịch tuần sau ({week_next_str}).")

    search_term = st.text_input("🔍 Tìm kiếm nhanh theo tên thành viên:")
    if search_term:
        mask = display_df[DAYS].apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]

    st.table(display_df.set_index("Dấu thời gian"))
    
    st.subheader("Thống kê số lượng người có mặt")
    counts = {day: sum((display_df[day] != "") & (display_df[day].notna())) for day in DAYS}
    st.table(pd.DataFrame([counts], index=["Số người"]))

    # --- KHU VỰC ADMIN ---
    if st.session_state.is_admin:
        st.markdown("---")
        st.subheader("⚙️ Khu vực Quản Trị Viên")
        st.info("💡 Bạn có thể sửa trực tiếp vào bảng dưới đây. Nhấn 'Lưu' để đồng bộ lên Google Sheets.")
        
        edited_df = st.data_editor(df_current, num_rows="dynamic", use_container_width=True, hide_index=True)
        
        if st.button("💾 Lưu thay đổi lên Google Sheets"):
            conn.update(worksheet="IMMLAB ONSITE AGENDA", data=edited_df)
            st.success("Đã cập nhật hệ thống!")
            st.cache_data.clear()
            st.rerun()

else:
    st.info("Chưa có dữ liệu đăng ký")