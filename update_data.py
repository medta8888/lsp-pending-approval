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
            
    # Đọc file và tự động bỏ qua các dòng rác phía trên
    return pd.read_csv(filepath, skiprows=header_idx, dtype=str)

def update_total_tickets():
    # Tự động tìm bất kỳ file nào có chữ "total" trong thư mục daily_uploads
    files = glob.glob('daily_uploads/*[Tt]otal*.csv')
    if not files:
        print("Không có file Total Ticket mới hôm nay.")
        return

    print(f"Đang xử lý Total Tickets từ file: {files[0]}")
    
    df_master = read_csv_smart(MASTER_TOTAL_PATH)
    df_daily = read_csv_smart(files[0])

    # Chuẩn hóa tên cột để ghép nối không bị lỗi (Request ID hay RequestID đều quy về 1 chuẩn)
    df_master.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x, inplace=True)
    df_daily.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x, inplace=True)

    # Ghép nối và loại bỏ trùng lặp
    df_combined = pd.concat([df_master, df_daily])
    df_final = df_combined.drop_duplicates(subset=['RequestID'], keep='last')
    
    df_final.to_csv(MASTER_TOTAL_PATH, index=False)
    os.remove(files[0]) # Xóa file rác sau khi xử lý xong
    print(f"✅ Đã cập nhật Master Total. Tổng số vé: {len(df_final)}")

def update_approvers():
    # Tự động tìm file có chữ "approver"
    files = glob.glob('daily_uploads/*[Aa]pprover*.csv')
    if not files:
        print("Không có file Approver mới hôm nay.")
        return

    print(f"Đang xử lý Approver Report từ file: {files[0]}")
    df_master = read_csv_smart(MASTER_APPROVER_PATH)
    df_daily = read_csv_smart(files[0])

    df_master.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x, inplace=True)
    df_daily.rename(columns=lambda x: 'RequestID' if str(x).replace(' ','').lower() == 'requestid' else x, inplace=True)

    # Tìm các Ticket ID bị thay đổi và xóa dòng cũ của chúng đi
    updated_ids = df_daily['RequestID'].unique()
    df_master_cleaned = df_master[~df_master['RequestID'].isin(updated_ids)]

    # Nối dữ liệu mới vào
    df_final = pd.concat([df_master_cleaned, df_daily])
    df_final.to_csv(MASTER_APPROVER_PATH, index=False)
    os.remove(files[0])
    print(f"✅ Đã cập nhật Master Approver. Tổng số dòng: {len(df_final)}")

if __name__ == "__main__":
    update_total_tickets()
    update_approvers()
