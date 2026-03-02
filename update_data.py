import pandas as pd
import os

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Nơi chứa file gốc khổng lồ
MASTER_TOTAL_PATH = 'data/Master_Total.csv'
MASTER_APPROVER_PATH = 'data/Master_Approver.csv'

# Nơi chứa file bạn tải lên hằng ngày (chứa ticket bị thay đổi trong 24h)
DAILY_TOTAL_PATH = 'daily_uploads/Total-ticket-report.csv'
DAILY_APPROVER_PATH = 'daily_uploads/Reports_By_Request_Approver.csv'

def update_total_tickets():
    if not os.path.exists(DAILY_TOTAL_PATH):
        print("Không có file Total Ticket mới hôm nay.")
        return

    print("Đang xử lý Total Tickets...")
    df_master = pd.read_csv(MASTER_TOTAL_PATH)
    df_daily = pd.read_csv(DAILY_TOTAL_PATH)

    # Nối 2 bảng và xóa trùng lặp dựa trên Request ID (Giữ lại thông tin mới nhất từ file Daily)
    df_combined = pd.concat([df_master, df_daily])
    df_final = df_combined.drop_duplicates(subset=['Request ID'], keep='last')
    
    df_final.to_csv(MASTER_TOTAL_PATH, index=False)
    os.remove(DAILY_TOTAL_PATH) # Xóa file daily sau khi hợp nhất xong
    print(f"✅ Đã cập nhật Master Total. Tổng số vé: {len(df_final)}")

def update_approvers():
    if not os.path.exists(DAILY_APPROVER_PATH):
        print("Không có file Approver mới hôm nay.")
        return

    print("Đang xử lý Approver Report...")
    df_master = pd.read_csv(MASTER_APPROVER_PATH)
    df_daily = pd.read_csv(DAILY_APPROVER_PATH)

    # Tìm danh sách các Ticket ID có sự thay đổi hôm nay
    updated_ticket_ids = df_daily['Request ID'].unique()

    # BƯỚC QUAN TRỌNG: Xóa TOÀN BỘ các dòng cũ của những Ticket này trong file Master
    df_master_cleaned = df_master[~df_master['Request ID'].isin(updated_ticket_ids)]

    # Bơm toàn bộ lịch sử duyệt mới nhất của các Ticket này vào file Master
    df_final = pd.concat([df_master_cleaned, df_daily])
    
    df_final.to_csv(MASTER_APPROVER_PATH, index=False)
    os.remove(DAILY_APPROVER_PATH) # Xóa file daily
    print(f"✅ Đã cập nhật Master Approver. Tổng số dòng: {len(df_final)}")

if __name__ == "__main__":
    update_total_tickets()
    update_approvers()
