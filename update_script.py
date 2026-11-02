import json
import requests

def generate_m3u_and_json():
    # Sử dụng link JSON chính xác của anh Sơn
    target_url = "https://tinyurl.com/xoilacz3" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối để lấy dữ liệu từ link...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Lưu file JSON gốc vào repo
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã cập nhật file xoilac.json thành công!")
            
            # 2. Tự động sinh file playlist.m3u cho IPTV
            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            
            # Tự động nhận diện cấu trúc dữ liệu (dạng list trực tiếp hoặc nằm trong key con)
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ["data", "matches", "result", "list", "items"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break
                if not items:
                    # Nếu là dict đơn thuần nhưng có các giá trị là list
                    for val in data.values():
                        if isinstance(val, list):
                            items = val
                            break

            count = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                # Quét các tên trường phổ biến chứa tiêu đề, link, danh mục
                title = item.get("title") or item.get("name") or item.get("match_name") or "Trận đấu trực tiếp"
                group = item.get("category") or item.get("group") or item.get("league") or "Bóng Đá"
                stream_url = item.get("stream_url") or item.get("url") or item.get("link") or item.get("m3u8") or ""
                logo = item.get("logo") or item.get("icon") or ""
                
                if stream_url:
                    ua = item.get("user_agent", "Mozilla/5.0")
                    referer = item.get("referer", "")
                    
                    final_link = stream_url
                    if referer:
                        final_link = f"{stream_url}|User-Agent={ua}&Referer={referer}"
                    elif ua != "Mozilla/5.0":
                        final_link = f"{stream_url}|User-Agent={ua}"

                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group}\",{title}\n"
                    m3u_content += f"{final_link}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} kênh/trận đấu!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình thực thi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
