import pandas as pd
import os
import glob

# --- CẤU HÌNH ĐƯỜNG DẪN ---
MASTER_TOTAL_PATH = 'data/Master_Total.csv'
MASTER_APPROVER_PATH = 'data/Master_Approver.csv'

# Hàm đọc CSV thông minh (Tự động bỏ qua các dòng rác của ManageEngine)
def read_csv_smart(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    header_idx = 0
    # Quét 20 dòng đầu tiên để tìm xem dòng nào chứa chữ RequestID
    for i, line in enumerate(lines[:20]):
        line_lower = line.lower().replace(' ', '')
        if 'requestid' in line_lower and ('status' in line_lower or 'stageid' in line_lower):
            header_idx = i
            break
            
    return pd.read_csv(filepath, skiprows=header_idx, dtype=str)

def update_data():
    # ==========================================
    # BƯỚC 1: CẬP NHẬT MASTER TOTAL
    # ==========================================
    total_files = glob.glob('daily_uploads/*[Tt]otal*.csv')
    df_master_total = read_csv_smart(MASTER_TOTAL_PATH)
    
    # Chuẩn hóa tên cột
    df_master_total.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x.strip(), inplace=True)
    
    if total_files:
        print(f"Đang xử lý Total Tickets từ file: {total_files[0]}")
        df_daily_total = read_csv_smart(total_files[0])
        df_daily_total.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x.strip(), inplace=True)
        
        # Ghép nối và loại bỏ trùng lặp (lấy dữ liệu mới nhất)
        df_master_total = pd.concat([df_master_total, df_daily_total]).drop_duplicates(subset=['RequestID'], keep='last')
        os.remove(total_files[0]) # Xóa file rác
        print(f"✅ Đã cập nhật Master Total. Tổng số vé: {len(df_master_total)}")

    # Ghi đè file Total lại để dùng làm gốc đối chiếu
    df_master_total.to_csv(MASTER_TOTAL_PATH, index=False)

    # ==========================================
    # BƯỚC 2: CẬP NHẬT MASTER APPROVER
    # ==========================================
    approver_files = glob.glob('daily_uploads/*[Aa]pprover*.csv')
    df_master_app = read_csv_smart(MASTER_APPROVER_PATH)
    
    df_master_app.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x.strip(), inplace=True)
    
    if approver_files:
        print(f"Đang xử lý Approver Report từ file: {approver_files[0]}")
        df_daily_app = read_csv_smart(approver_files[0])
        df_daily_app.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x.strip(), inplace=True)
        
        # Xóa các ID cũ đi và nạp ID mới vào
        updated_ids = df_daily_app['RequestID'].dropna().unique()
        df_master_app = df_master_app[~df_master_app['RequestID'].isin(updated_ids)]
        df_master_app = pd.concat([df_master_app, df_daily_app])
        os.remove(approver_files[0])

    # ==========================================
    # BƯỚC 3: DỌN DẸP "GHOST RECORDS" (CROSS-CLEANUP)
    # ==========================================
    print("🔍 Đang dọn dẹp các vé không còn cần duyệt (Ghost Records)...")
    
    if 'Approval Status' in df_master_total.columns:
        # Danh sách các trạng thái có nghĩa là VÉ ĐÃ XONG HOẶC KHÔNG CẦN DUYỆT NỮA
        statuses_to_remove = ['denied', 'not assigned', 'pending clarification', 'approved']
        
        # Chuẩn hóa cột chữ để so sánh chính xác
        total_approval_status = df_master_total['Approval Status'].astype(str).str.strip().str.lower()
        
        # Lấy danh sách ID cần bị "trảm"
        ids_to_remove = df_master_total[total_approval_status.isin(statuses_to_remove)]['RequestID'].dropna().unique()
        
        initial_count = len(df_master_app)
        
        # Lọc bỏ các ID này ra khỏi Master Approver
        df_master_app = df_master_app[~df_master_app['RequestID'].isin(ids_to_remove)]
        
        removed_count = initial_count - len(df_master_app)
        print(f"🧹 Đã dọn dẹp {removed_count} dòng lịch sử phê duyệt rác/hết hạn khỏi Master Approver.")

    # Lưu lại file Approver sạch sẽ
    df_master_app.to_csv(MASTER_APPROVER_PATH, index=False)
    print(f"✅ Hoàn tất! Dữ liệu đã đồng bộ và sạch sẽ hoàn toàn. Tổng dòng Approver hiện tại: {len(df_master_app)}")

if __name__ == "__main__":
    update_data()
