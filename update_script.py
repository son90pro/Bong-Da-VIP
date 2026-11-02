import json
import requests

def generate_m3u_and_json():
    # URL nguồn dữ liệu của anh (thay thế bằng API hoặc nguồn thực tế của anh)
    target_url = "https://example.com/api/xoilac" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối để lấy dữ liệu mới...")
        response = requests.get(target_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Lưu file JSON gốc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã cập nhật file xoilac.json thành công!")
            
            # 2. Tự động sinh file playlist.m3u cho IPTV
            # (Giả cấu trúc dữ liệu trả về là một danh sách các trận đấu/kênh)
            # Anh có thể điều chỉnh lại các trường key (ví dụ: title, stream_url, group) cho khớp với dữ liệu thực tế của anh
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            
            # Ví dụ duyệt qua danh sách (điều chỉnh vòng lặp theo JSON thực tế của anh)
            items = data if isinstance(data, list) else data.get("matches", [])
            
            for item in items:
                title = item.get("title", "Trận đấu trực tiếp")
                group = item.get("category", "Bóng Đá")
                stream_url = item.get("stream_url", "")
                logo = item.get("logo", "")
                
                if stream_url:
                    # Nếu link stream cần kèm Header (ví dụ như User-Agent hoặc Referer cho .m3u8)
                    # Một số app IPTV hỗ trợ cú pháp: url |User-Agent=...&Referer=...
                    ua = item.get("user_agent", "Mozilla/5.0")
                    referer = item.get("referer", "")
                    
                    final_link = stream_url
                    if referer:
                        final_link = f"{stream_url}|User-Agent={ua}&Referer={referer}"
                    elif ua != "Mozilla/5.0":
                        final_link = f"{stream_url}|User-Agent={ua}"

                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group}\",{title}\n"
                    m3u_content += f"{final_link}\n"

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print("Đã tạo xong file playlist.m3u chuẩn IPTV!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
