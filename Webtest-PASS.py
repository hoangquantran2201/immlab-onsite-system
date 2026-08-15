import  streamlit as st
import  pandas    as pd
from    datetime  import datetime, timedelta
from    streamlit_gsheets import GSheetsConnection
import  random
import  smtplib
from    email.mime.text import MIMEText
import  unicodedata # Thư viện xóa dấu tiếng Việt
import  time # Thư viện điều khiển thời gian chờ

st.set_page_config(layout="wide", page_title="Lab Check-in Schedule")

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
# KHỞI TẠO BỘ NHỚ VÀ HÀM PHỤ TRỢ
# ==========================================
DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

if "logged_in_name" not in st.session_state:
    st.session_state.logged_in_name = None
    st.session_state.is_admin = False

def tao_username(ten):
    """Hàm tự động tạo Username từ Họ Tên (Xóa dấu, viết thường, bỏ khoảng trắng)"""
    if pd.isna(ten) or str(ten).strip() == "":
        return ""
    # Đổi chữ Đ/đ đặc thù của tiếng Việt
    ten = str(ten).replace('Đ', 'd').replace('đ', 'd')
    # Xóa các dấu á, à, ả, ã, ạ...
    ten = unicodedata.normalize('NFKD', ten).encode('ASCII', 'ignore').decode('utf-8')
    return ten.lower().replace(" ", "")

# ==========================================
# KẾT NỐI GOOGLE SHEETS
# ==========================================
conn_agenda = st.connection("gsheets_agenda", type=GSheetsConnection)
conn_accounts = st.connection("gsheets_accounts", type=GSheetsConnection)

df_current = conn_agenda.read(worksheet="Lab Check-in Schedule", ttl="10m")
df_accounts = conn_accounts.read(worksheet="ACCOUNTS", ttl="10m")

# Đảm bảo cột 'User' tồn tại trong DataFrame để tránh lỗi nếu Sheet chưa có
if 'User' not in df_accounts.columns:
    df_accounts['User'] = ""

# ==========================================
# HÀM GỬI EMAIL TỰ ĐỘNG
# ==========================================
def send_email(receiver_email, username, password):
    sender_email = st.secrets["email"]["sender"]
    app_password = st.secrets["email"]["password"]
    
    # Đã cập nhật nội dung thư để gửi kèm cả Username
    msg_body = f"""Chào bạn,

Hệ thống IMMLab Attendance Booking đã cấp tài khoản truy cập cho bạn:
- Tên đăng nhập (Username): {username}
- Mật khẩu (Password): {password}

Bạn có thể sử dụng Username hoặc Email để đăng nhập hệ thống. Vui lòng không chia sẻ thông tin này cho người khác.

Trân trọng,
IMMLAB Admin."""

    msg = MIMEText(msg_body)
    msg['Subject'] = 'Tài khoản truy cập hệ thống IMMLab Attendance Booking'
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

# --- PHẦN 1: KHU VỰC ĐĂNG KÝ ---
st.markdown("<h2 style='font-size: 26px; padding-bottom: 10px;'>1. Cập nhật lịch có mặt</h2>", unsafe_allow_html=True)
if st.session_state.logged_in_name is None:
    st.warning("🔒 Vui lòng đăng nhập để có thể đăng ký lịch.")
    with st.expander("Bấm vào đây để ĐĂNG NHẬP", expanded=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            email_input = st.text_input("Tài khoản (Email hoặc Username):")
        with col2:
            pass_input = st.text_input("Mật khẩu:", type="password")
        
        if st.button("Đăng nhập"):
            # 1. Gọt giũa dữ liệu ngay từ đầu cho CẢ ADMIN VÀ USER
            input_user_clean = email_input.strip().lower()
            input_pass_clean = pass_input.strip()

            # 2. Xử lý Admin
            if input_user_clean == "immlabstaff" and input_pass_clean == "immlabstaff":
                st.session_state.logged_in_name = "Staff"
                st.session_state.is_admin = True
                st.success("Đăng nhập Admin thành công!")
                st.rerun()
            else:
                # 3. Xử lý User thường
                if not df_accounts.empty:
                    sheet_passwords = df_accounts['Password'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace(',', '', regex=False).str.strip()
                    sheet_users = df_accounts['User'].astype(str).str.strip().str.lower()
                    sheet_emails = df_accounts['Email'].astype(str).str.strip().str.lower()

                    # So khớp
                    user_match = df_accounts[
                        ((sheet_emails == input_user_clean) | (sheet_users == input_user_clean)) & 
                        (sheet_passwords == input_pass_clean)
                    ]
                    
                    if not user_match.empty:
                        st.session_state.logged_in_name = user_match.iloc[0]['Name']
                        st.session_state.is_admin = False
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu! Vui lòng kiểm tra lại.")
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

    if current_weekday in [0, 6]: #0 là Thứ 2, 6 là Chủ Nhật, tùy chỉnh các ngày trong tuần
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
                    if current_weekday == 6: 
                        target_monday = now + timedelta(days=1)
                    else: 
                        target_monday = now - timedelta(days=current_weekday)
                    target_sunday = target_monday + timedelta(days=6)
                    week_str = f"{target_monday.strftime('%d/%m')} - {target_sunday.strftime('%d/%m')}"
                    
                    new_row = {"Dấu thời gian": timestamp, "Tuần đăng ký": week_str}
                    for day in DAYS:
                        new_row[day] = current_user if selected_days[day] else ""
                    
                    new_entry = pd.DataFrame([new_row])
                    updated_df = pd.concat([df_current, new_entry], ignore_index=True)
                    conn_agenda.update(worksheet="Lab Check-in Schedule", data=updated_df)
                    
                    st.success("Đã ghi nhận thành công!")
                    st.cache_data.clear() 
                    time.sleep(2)
                    st.rerun()
    else:
        st.warning("Cổng đăng ký hiện đang ĐÓNG. Bạn chỉ có thể đăng ký vào Chủ Nhật và Thứ 2 hàng tuần.")

st.markdown("---")

# ==========================================
# KHU VỰC QUẢN TRỊ VIÊN
# ==========================================
if st.session_state.is_admin:
    st.subheader("⚙️ Khu vực Quản Trị Viên")
    
    tab1, tab2, tab3 = st.tabs(["Quản lý Lịch Onsite", "Cấp Pass & Gửi Mail", "Thống kê Lab"])
    with tab1:
        st.info("💡 Chế độ xem theo tuần: Chọn tuần cần xem và sửa. Nhấn 'Lưu' để đồng bộ lên Google Sheets.")
        
        # Kiểm tra xem bảng có dữ liệu và có cột "Tuần đăng ký" chưa
        if not df_current.empty and 'Tuần đăng ký' in df_current.columns:
            
            # Lấy danh sách các tuần (loại bỏ ô trống và các tuần trùng lặp)
            danh_sach_tuan = df_current['Tuần đăng ký'].dropna().unique().tolist()
            
            if danh_sach_tuan:
                # Tạo thanh menu chọn tuần (mặc định chọn tuần mới nhất - nằm cuối danh sách)
                selected_week = st.selectbox("📅 Chọn tuần để xem:", danh_sach_tuan, index=len(danh_sach_tuan)-1)
                
                # Lọc bảng chỉ hiển thị dữ liệu của tuần vừa chọn
                df_filtered = df_current[df_current['Tuần đăng ký'] == selected_week]
                
                # Hiển thị bảng cho phép chỉnh sửa
                edited_df = st.data_editor(df_filtered, num_rows="dynamic", use_container_width=True, hide_index=True)
                
                if st.button("💾 Lưu thay đổi Lịch"):
                    with st.spinner("Đang lưu dữ liệu..."):
                        # 1. Tách riêng dữ liệu của tất cả các tuần KHÁC cất đi
                        df_other_weeks = df_current[df_current['Tuần đăng ký'] != selected_week]
                        
                        # 2. Đảm bảo nếu Admin bấm (+) thêm dòng mới, nó vẫn tự nhảy đúng vào tuần này
                        edited_df['Tuần đăng ký'] = selected_week
                        
                        # 3. Ráp nối lại: Dữ liệu các tuần cũ + Dữ liệu tuần này vừa sửa
                        df_final = pd.concat([df_other_weeks, edited_df], ignore_index=True)
                        
                        # 4. Đẩy toàn bộ bảng mới lên Google Sheets
                        conn_agenda.update(worksheet="Lab Check-in Schedule", data=df_final)
                        
                        st.success(f"✅ Đã cập nhật thành công lịch cho {selected_week}! Hệ thống đang làm mới...")
                        st.cache_data.clear()
                        time.sleep(1.5)
                        st.rerun()
            else:
                st.write("Chưa có thông tin tuần nào được đăng ký.")
        else:
            st.write("Chưa có dữ liệu lịch.")
            
    with tab2:
        st.info("💡 Bấm nút dưới đây để tạo mã PIN và gửi qua Email cho những thành viên CHƯA CÓ mật khẩu.")
        
        st.markdown("### 🧪 Khu vực Gửi Thử Nghiệm (Test)")
        test_email = st.text_input("Nhập email để gửi test:", value="hoangquantran2201@gmail.com")
        if st.button("Gửi Test", type="secondary"):
            with st.spinner("Đang gửi mail test..."):
                try:
                    send_email(test_email, "hoangquantest", "99999")
                    st.success(f"✅ Đã gửi mail test thành công tới {test_email}!")
                except Exception as e:
                    st.error(f"❌ Lỗi gửi mail: {e}")
        st.markdown("---")
        
        if st.button("Bắt đầu Quét & Gửi Mail", type="primary"):
            with st.spinner("Đang xử lý và gửi mail... (Vui lòng không tắt trang)"):
                updates_made = False
                df_acc_updated = df_accounts.copy()
                
                df_acc_updated['User'] = df_acc_updated['User'].astype(object)
                df_acc_updated['Password'] = df_acc_updated['Password'].astype(object)
                df_acc_updated['Status'] = df_acc_updated['Status'].astype(object)

                # Lấy danh sách pass cũ để chống trùng
                existing_passwords = df_acc_updated['Password'].dropna().astype(str).tolist()
                
                for index, row in df_acc_updated.iterrows():
                    current_user = str(row.get('User', ''))
                    current_pass = str(row.get('Password', ''))
                    
                    # 1. Tự động tạo Username nếu ô đang trống
                    if pd.isna(row.get('User')) or current_user.strip() == "" or current_user == "nan":
                        current_user = tao_username(row['Name'])
                        df_acc_updated.at[index, 'User'] = current_user
                        updates_made = True
                        
                    # 2. Tự động tạo Password và gửi Mail nếu ô đang trống
                    if pd.isna(row.get('Password')) or current_pass.strip() == "" or current_pass == "nan":
                        # Bốc pass ngẫu nhiên và chống trùng
                        random_pass = str(random.randint(10000, 99999))
                        while random_pass in existing_passwords:
                            random_pass = str(random.randint(10000, 99999))
                        existing_passwords.append(random_pass)
                        
                        try:
                            # Truyền cả User và Pass vào hàm gửi mail
                            send_email(row['Email'], current_user, random_pass)
                            df_acc_updated.at[index, 'Password'] = random_pass
                            df_acc_updated.at[index, 'Status'] = "Đã gửi mail"
                            updates_made = True
                            st.write(f"✅ Đã tạo tài khoản và gửi mail cho: {row['Name']} ({row['Email']})")
                        except Exception as e:
                            st.error(f"❌ Lỗi khi gửi cho {row['Email']}: {e}")
                            
                if updates_made:
                    conn_accounts.update(worksheet="ACCOUNTS", data=df_acc_updated)
                    st.success("Hoàn tất cấp tài khoản và đồng bộ lên Google Sheets!")
                    st.cache_data.clear()
                else:
                    st.warning("Tất cả thành viên đều đã có Username và Password. Không có email nào được gửi thêm.")
        
        st.markdown("---")
        st.write("Bảng theo dõi trạng thái tài khoản (Đồng bộ từ Tab Accounts):")
        if not df_accounts.empty:
            st.dataframe(df_accounts, use_container_width=True, hide_index=True)

    with tab3:
        st.info("📊 Bảng thống kê: Theo dõi số ngày CÓ MẶT THỰC TẾ và số lần VẮNG MẶT.")
        
        if not df_current.empty:
            try:
                # 1. Gom cột Thứ 2 -> Chủ Nhật thành 1 cột dọc
                df_melted = df_current.melt(
                    id_vars=['Dấu thời gian', 'Tuần đăng ký'], 
                    value_vars=DAYS, 
                    var_name='Thứ', 
                    value_name='Thành viên'
                )
                
                # 2. Lọc bỏ ô trống
                df_valid = df_melted[(df_melted['Thành viên'].notna()) & (df_melted['Thành viên'].str.strip() != "")].copy()
                
                if not df_valid.empty:
                    # Trích xuất Tháng
                    df_valid['Tháng'] = df_valid['Tuần đăng ký'].astype(str).str.extract(r'/(\d{2})\s*-')
                    df_valid['Tháng'] = "Tháng " + df_valid['Tháng'].fillna("Khác")
                    
                    # ==========================================
                    # THUẬT TOÁN XỬ LÝ VẮNG MẶT
                    # ==========================================
                    # Nhận diện ai có chữ "vắng" trong tên (bất kể viết hoa/thường hay có dấu ngoặc)
                    is_absent = df_valid['Thành viên'].str.lower().str.contains('vắng')
                    
                    # Dọn dẹp tên (Cắt bỏ đoạn "(vắng)" để gộp chung vào tên gốc)
                    # Biểu thức (?i) giúp không phân biệt hoa thường
                    df_valid['Tên chuẩn'] = df_valid['Thành viên'].str.replace(r'(?i)[-_\(\)\[\]\s]*vắng.*', '', regex=True).str.strip()
                    
                    # Chia làm 2 nhóm dữ liệu: Đi thực tế và Vắng mặt
                    df_present = df_valid[~is_absent]
                    df_absent = df_valid[is_absent]
                    
                    # Tính toán: SỐ NGÀY ĐI THỰC TẾ
                    if not df_present.empty:
                        df_stats = df_present.groupby(['Tên', 'Tháng']).size().reset_index(name='Số ngày')
                        df_pivot = df_stats.pivot(index='Tên', columns='Tháng', values='Số ngày').fillna(0).astype(int)
                        df_pivot['Tổng có mặt'] = df_pivot.sum(axis=1)
                    else:
                        df_pivot = pd.DataFrame(columns=['Tổng có mặt'])
                        
                    # Tính toán: SỐ LẦN VẮNG MẶT (Để cảnh cáo)
                    if not df_absent.empty:
                        absent_counts = df_absent.groupby('Tên').size()
                        # Ghép cột Vắng mặt vào bảng chính
                        df_pivot = df_pivot.join(absent_counts.rename('Tổng số lần Vắng')).fillna(0)
                        df_pivot['Tổng số lần Vắng'] = df_pivot['Tổng số lần Vắng'].astype(int)
                    else:
                        df_pivot['Tổng số lần Vắng'] = 0
                        
                    # Sắp xếp theo chuyên cần 
                    df_pivot = df_pivot.sort_values(by='Tổng có mặt', ascending=False)
                    
                    # Xuất bảng báo cáo ra màn hình
                    st.dataframe(df_pivot, use_container_width=True)
                else:
                    st.write("Hiện chưa có dữ liệu thành viên đăng ký lịch.")
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra khi tính toán thống kê: {e}")
        else:
            st.write("Chưa có dữ liệu lịch trên Google Sheets để thống kê.")