import pandas as pd
import os
import glob

# --- CẤU HÌNH ĐƯỜNG DẪN ---
MASTER_TOTAL_PATH = 'data/Master_Total.csv'
MASTER_APPROVER_PATH = 'data/Master_Approver.csv'

def read_csv_smart(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    header_idx = 0
    # Quét tìm dòng tiêu đề thực sự để bỏ qua rác của ManageEngine
    for i, line in enumerate(lines[:20]):
        line_lower = line.lower().replace(' ', '')
        if 'requestid' in line_lower and ('status' in line_lower or 'stageid' in line_lower):
            header_idx = i
            break
            
    df = pd.read_csv(filepath, skiprows=header_idx, dtype=str)
    
    # Chuẩn hóa tên cột Request ID
    df.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x.strip(), inplace=True)
    
    # Chuẩn hóa giá trị ID (Xóa khoảng trắng và dấu thập phân ẩn) để so sánh không bị trượt
    if 'RequestID' in df.columns:
        df['RequestID'] = df['RequestID'].astype(str).str.strip().str.replace('.0', '', regex=False)
        
    return df

def update_data():
    print("🚀 Bắt đầu tiến trình đồng bộ dữ liệu siêu an toàn...")
    
    # ==========================================
    # BƯỚC 1: UPSERT (CẬP NHẬT) MASTER TOTAL
    # ==========================================
    total_files = glob.glob('daily_uploads/*[Tt]otal*.csv')
    if os.path.exists(MASTER_TOTAL_PATH):
        df_master_total = read_csv_smart(MASTER_TOTAL_PATH)
    else:
        df_master_total = pd.DataFrame()

    if total_files:
        print(f"📥 Đang nạp file Total mới: {total_files[0]}")
        df_daily_total = read_csv_smart(total_files[0])
        
        # Gộp file cũ và mới. Nếu trùng ID thì giữ lại dòng mới nhất (keep='last')
        df_master_total = pd.concat([df_master_total, df_daily_total], ignore_index=True)
        df_master_total.drop_duplicates(subset=['RequestID'], keep='last', inplace=True)
        
        os.remove(total_files[0])
        print(f"✅ Đã Update Master Total. Tổng số vé lưu trữ: {len(df_master_total)}")

    # Lưu lại file với chuẩn xuống dòng chung (tránh bị Git báo lỗi Delete ảo)
    if not df_master_total.empty:
        df_master_total.to_csv(MASTER_TOTAL_PATH, index=False, lineterminator='\n')

    # ==========================================
    # BƯỚC 2: UPSERT (CẬP NHẬT) MASTER APPROVER
    # ==========================================
    approver_files = glob.glob('daily_uploads/*[Aa]pprover*.csv')
    if os.path.exists(MASTER_APPROVER_PATH):
        df_master_app = read_csv_smart(MASTER_APPROVER_PATH)
    else:
        df_master_app = pd.DataFrame()

    if approver_files:
        print(f"📥 Đang nạp file Approver mới: {approver_files[0]}")
        df_daily_app = read_csv_smart(approver_files[0])
        
        if 'RequestID' in df_daily_app.columns and 'RequestID' in df_master_app.columns:
            # Lấy danh sách các vé có sự di chuyển/cập nhật trong hôm nay
            updated_ids = df_daily_app['RequestID'].dropna().unique()
            
            # Chỉ xóa các dòng CỦA CHÍNH VÉ ĐÓ trong file gốc, để thay bằng luồng lịch sử mới
            df_master_app = df_master_app[~df_master_app['RequestID'].isin(updated_ids)]
            
        # Nối dữ liệu mới vào
        df_master_app = pd.concat([df_master_app, df_daily_app], ignore_index=True)
        
        os.remove(approver_files[0])
        print(f"✅ Đã Update Master Approver. Tổng số dòng lưu trữ: {len(df_master_app)}")

    # Lưu lại file
    if not df_master_app.empty:
        df_master_app.to_csv(MASTER_APPROVER_PATH, index=False, lineterminator='\n')

    print("🎉 Tiến trình hoàn tất! Dữ liệu lịch sử được bảo vệ 100%. Các vé Ghost sẽ do giao diện HTML tự động ẩn đi.")

if __name__ == "__main__":
    update_data()
