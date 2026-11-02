import json
import requests

def generate_m3u_and_json():
    target_url = "https://tinyurl.com/xoilacz3" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("Đang kết nối để lấy dữ liệu từ link...")
        response = requests.get(target_url, headers=headers, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Lưu file JSON gốc
            with open('xoilac.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Đã lưu file xoilac.json thành công!")
            
            # 2. In cấu trúc JSON ra log để kiểm tra
            print("=== KIỂM TRA CẤU TRÚC JSON ===")
            if isinstance(data, dict):
                print(f"JSON gốc là dạng Dict, các khóa chính: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"JSON gốc là dạng List gồm {len(data)} phần tử.")
                if len(data) > 0 and isinstance(data[0], dict):
                    print(f"Khóa mẫu của phần tử đầu tiên: {list(data[0].keys())}")
            print("================================")

            # Xác định danh sách items
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for key in ["matches", "data", "list", "result", "channels", "items", "match_list", "schedule"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        print(f"Tìm thấy danh sách dữ liệu tại khóa: '{key}'")
                        break
                if not items:
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 0:
                            items = v
                            print(f"Lấy danh sách từ khóa phụ: '{k}'")
                            break
                    if not items:
                        items = [data]

            m3u_content = "#EXTM3U x-tvg-url=\"\"\n"
            count = 0

            for item in items:
                if not isinstance(item, dict):
                    continue
                
                title = (item.get("title") or item.get("name") or item.get("match_name") or 
                         item.get("channel_name") or item.get("match") or "Trận đấu trực tiếp")
                
                group = (item.get("category") or item.get("group") or item.get("league") or 
                         item.get("sport") or item.get("type") or "Bóng Đá")
                
                logo = item.get("logo") or item.get("icon") or item.get("thumb") or ""

                # Thu thập tất cả các link có thể có trong item này
                urls_to_process = []
                primary_url = (item.get("stream_url") or item.get("url") or item.get("link") or 
                               item.get("m3u8") or item.get("stream") or item.get("source") or "")
                
                if primary_url and isinstance(primary_url, str):
                    urls_to_process.append(primary_url)

                # Kiểm tra các mảng link con bên trong
                for sub_key in ["streams", "links", "servers", "sources", "playlist"]:
                    if sub_key in item and isinstance(item[sub_key], list):
                        for sub in item[sub_key]:
                            if isinstance(sub, str):
                                urls_to_process.append(sub)
                            elif isinstance(sub, dict):
                                s_url = sub.get("url") or sub.get("link") or sub.get("stream_url")
                                if s_url:
                                    urls_to_process.append(s_url)

                for u in urls_to_process:
                    if not u or not isinstance(u, str) or not u.startswith("http"):
                        continue
                    
                    m3u_content += f"#EXTINF:-1 tvg-logo=\"{logo}\" group-title=\"{group}\",{title}\n"
                    m3u_content += f"{u}\n"
                    count += 1

            with open('playlist.m3u', 'w', encoding='utf-8') as f:
                f.write(m3u_content)
                
            print(f"Đã tạo xong file playlist.m3u với {count} mục!")
            
        else:
            print(f"Lỗi phản hồi từ server: {response.status_code}")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    generate_m3u_and_json()
    
