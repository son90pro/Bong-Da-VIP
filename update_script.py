import json
import requests

def fetch_and_update():
    # Thay thế URL nguồn dữ liệu của anh vào đây
    target_url = "https://example.com/api/xoilac" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối để lấy dữ liệu mới...")
        response = requests.get(target_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Ghi đè hoặc xử lý dữ liệu vào file xoilac.json
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print("Đã cập nhật file xoilac.json thành công!")
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thực thi: {e}")

if __name__ == "__main__":
    fetch_and_update()

