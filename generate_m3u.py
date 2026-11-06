# -*- coding: utf-8 -*-
import os
from badong_engine import get_live_channels, resolve_stream_url

def generate_playlist():
    print("Đang lấy danh sách kênh từ các nguồn (Tier 1, Tier 2)...")
    # Lấy danh sách kênh trực tiếp (force_refresh=True để không dùng cache cũ)
    channels = get_live_channels(force_refresh=True, enable_tier3=False)
    
    if not channels:
        print("Cảnh báo: Không lấy được kênh nào!")
        return

    # Khởi tạo nội dung file M3U
    m3u_lines = ["#EXTM3U x-tvg-url=\"\""]
    
    for ch in channels:
        title = ch.get("title", "Trực tiếp Thể Thao")
        group = ch.get("group", "Thể Thao Live")
        logo = ch.get("logo", "")
        raw_url = ch.get("url", "")
        provider = ch.get("provider", "")
        
        # Tự động gắn pipe parameters (User-Agent & Referer) cho Kodi / VLC
        stream_url = resolve_stream_url(raw_url, provider)
        
        # Định dạng dòng #EXTINF chuẩn
        extinf = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{title}'
        m3u_lines.append(extinf)
        m3u_lines.append(stream_url)
        
    output_filename = "playlist.m3u"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
        
    print(f"Đã tạo thành công {output_filename} với {len(channels)} kênh!")

if __name__ == "__main__":
    generate_playlist()
    
