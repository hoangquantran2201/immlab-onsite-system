import  streamlit as st
import  pandas    as pd
from    datetime  import datetime, timedelta
from    streamlit_gsheets import GSheetsConnection
import  random
import  smtplib
from    email.mime.text import MIMEText

st.set_page_config(layout="wide", page_title="IMMLAB ONSITE AGENDA")

# --- CSS ÉP BẢNG CĂN GIỮA ---
st.markdown("""
    <style>
    [data-testid="stTable"] table { width: 100% !important; table-layout: fixed !important; }
    [data-testid="stTable"] th, [data-testid="stTable"] td { text-align: center !important; vertical-align: middle !important; word-wrap: break-word !important; }
    [data-testid="stTable"] th { 
        background-color: #1E2530 !important; 
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# KHỞI TẠO BỘ NHỚ
# ==========================================
DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

if "logged_in_name" not in st.session_state:
    st.session_state.logged_in_name = None
    st.session_state.is_admin = False

# ==========================================
# KẾT NỐI GOOGLE SHEETS
# ==========================================
# Tạo 2 kết nối riêng biệt
conn_agenda = st.connection("gsheets_agenda", type=GSheetsConnection)
conn_accounts = st.connection("gsheets_accounts", type=GSheetsConnection)

# Đọc dữ liệu từ file Lịch trực
df_current = conn_agenda.read(worksheet="IMMLAB ONSITE AGENDA", ttl=0)

# Đọc dữ liệu từ file Tài khoản 
df_accounts = conn_accounts.read(worksheet="ACCOUNTS", ttl=0)
# ==========================================
# HÀM GỬI EMAIL TỰ ĐỘNG
# ==========================================
def send_email(receiver_email, password):
    sender_email = "immlab2026@gmail.com" 
    app_password = "ejprixwusrbinrmf" 
    
    msg = MIMEText(f"Chào bạn,\n\nMật khẩu đăng nhập hệ thống IMMLab Attendance Booking của bạn là: {password}\n\nVui lòng sử dụng mật khẩu này để đăng nhập và không chia sẻ cho người khác.\n\nTrân trọng,\nIMMLAB Admin.")
    msg['Subject'] = 'Mật khẩu truy cập hệ thống IMMLab Attendance Booking'
    msg['From'] = sender_email
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

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
            # Kiểm tra Admin (Ghi cứng để đảm bảo Sếp luôn vào được)
            if email_input == "admin@immlab.com" and pass_input == "immlabstaff":
                st.session_state.logged_in_name = "Staff"
                st.session_state.is_admin = True
                st.success("Đăng nhập Admin thành công!")
                st.rerun()
            else:
                # Kiểm tra thành viên thường dựa trên tab Accounts
                if not df_accounts.empty:
                    # Lọc tìm người dùng
                    user_match = df_accounts[(df_accounts['Email'] == email_input) & (df_accounts['Password'].astype(str) == pass_input)]
                    
                    if not user_match.empty:
                        st.session_state.logged_in_name = user_match.iloc[0]['Name']
                        st.session_state.is_admin = False
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu! Vui lòng kiểm tra lại email chứa 5 số mã PIN.")
                else:
                    st.error("Hệ thống chưa tải được dữ liệu tài khoản.")

else:
    col_info, col_logout = st.columns([4, 1])
    with col_info:
        st.success(f"👤 Đang đăng nhập dưới tên: **{st.session_state.logged_in_name}**")
    with col_logout:
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in_name = None
            st.session_state.is_admin = False
            st.rerun()

    if current_weekday == 0: # 0 là thứ 2. Tùy lab mở ngày nào thì đổi số đó
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
                    
                    new_entry = pd.DataFrame([new_row])
                    updated_df = pd.concat([df_current, new_entry], ignore_index=True)
                    conn_agenda.update(worksheet="IMMLAB ONSITE AGENDA", data=updated_df)
                    
                    st.success("Đã ghi nhận thành công!")
                    st.cache_data.clear() 
                    st.rerun()
    else:
        st.warning("Cổng đăng ký hiện đang ĐÓNG. Bạn chỉ có thể đăng ký vào Chủ Nhật hàng tuần.")

st.markdown("---")

# ==========================================
# KHU VỰC QUẢN TRỊ VIÊN (ADMIN DASHBOARD)
# ==========================================
if st.session_state.is_admin:
    st.subheader("⚙️ Khu vực Quản Trị Viên")
    
    # Chia tab cho gọn gàng
    tab1, tab2 = st.tabs(["Quản lý Lịch Onsite", "Cấp Pass & Gửi Mail"])
    
    # TAB 1: Sửa lịch
    with tab1:
        st.info("💡 Bạn có thể sửa trực tiếp vào bảng dưới đây. Nhấn 'Lưu' để đồng bộ lên Google Sheets.")
        if not df_current.empty:
            edited_df = st.data_editor(df_current, num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("💾 Lưu thay đổi Lịch"):
                conn_agenda.update(worksheet="IMMLAB ONSITE AGENDA", data=edited_df)
                st.success("Đã cập nhật hệ thống!")
                st.cache_data.clear()
                st.rerun()
        else:
            st.write("Chưa có dữ liệu lịch.")
            
    # TAB 2: Cấp tài khoản
    with tab2:
        st.info("💡 Bấm nút dưới đây để tạo mã PIN 5 số và gửi qua Email cho những thành viên CHƯA CÓ mật khẩu trong Google Sheets.")
        # ====== BẮT ĐẦU ĐOẠN CODE TEST THÊM ======
        st.markdown("### 🧪 Khu vực Gửi Thử Nghiệm (Test)")
        test_email = st.text_input("Nhập email để gửi test:", value="hoangquantran2201@gmail.com")
        if st.button("Gửi Test", type="secondary"):
            with st.spinner("Đang gửi mail test..."):
                test_pass = "99999" # Mã PIN giả lập để test
                try:
                    send_email(test_email, test_pass)
                    st.success(f"✅ Đã gửi mail test thành công tới {test_email}! Bạn hãy kiểm tra hộp thư (cả mục Spam) nhé.")
                except Exception as e:
                    st.error(f"❌ Lỗi gửi mail: Kiểm tra lại App Password hoặc kết nối mạng. Chi tiết lỗi: {e}")
        st.markdown("---")
        # ====== KẾT THÚC ĐOẠN CODE TEST ======
        if st.button("Bắt đầu Quét & Gửi Mail", type="primary"):
            with st.spinner("Đang xử lý và gửi mail... (Vui lòng không tắt trang)"):
                updates_made = False
                df_acc_updated = df_accounts.copy()
                
                for index, row in df_acc_updated.iterrows():
                    # Chỉ gửi cho người chưa có Pass
                    if pd.isna(row['Password']) or str(row['Password']).strip() == "":
                        random_pass = str(random.randint(10000, 99999))
                        try:
                            send_email(row['Email'], random_pass)
                            df_acc_updated.at[index, 'Password'] = random_pass
                            df_acc_updated.at[index, 'Status'] = "Đã gửi mail"
                            updates_made = True
                            st.write(f"✅ Đã gửi pass thành công cho: {row['Email']}")
                        except Exception as e:
                            st.error(f"❌ Lỗi khi gửi cho {row['Email']}: Kiểm tra lại App Password hoặc Email nhận.")
                            
                if updates_made:
                    # Ghi đè mật khẩu mới lên tab Accounts
                    conn_accounts.update(worksheet="ACCOUNTS", data=df_acc_updated)
                    st.success("Hoàn tất cấp tài khoản và đồng bộ lên Google Sheets!")
                    st.cache_data.clear()
                else:
                    st.warning("Tất cả thành viên đều đã có mật khẩu. Không có email nào được gửi thêm.")
        
        st.markdown("---")
        st.write("Bảng theo dõi trạng thái tài khoản (Đồng bộ từ Tab Accounts):")
        if not df_accounts.empty:
            st.dataframe(df_accounts, use_container_width=True, hide_index=True)