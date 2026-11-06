# -*- coding: utf-8 -*-
import json
import os
from badong_engine import get_live_channels, resolve_stream_url

# Link logo Bóng Đá VIP của anh Sơn dùng làm ảnh đại diện chính
BONG_DA_VIP_LOGO = "https://raw.githubusercontent.com/son90pro/Bong-Da-VIP/refs/heads/main/10894352.png"

def generate_projectivy_json():
    print("Đang lấy danh sách kênh từ các nguồn...")
    channels = get_live_channels(force_refresh=True, enable_tier3=False)
    
    if not channels:
        print("Cảnh báo: Không lấy được kênh nào!")
        return

    # Gom nhóm các kênh theo group/provider gốc
    grouped_data = {}
    for ch in channels:
        group_name = ch.get("group", "Thể Thao Live").strip()
        if not group_name:
            group_name = "Thể Thao Khác"
            
        if group_name not in grouped_data:
            grouped_data[group_name] = []
        grouped_data[group_name].append(ch)

    # Xây dựng cấu trúc JSON chuẩn Projectivy Launcher
    groups_list = []
    for grp_name, ch_list in grouped_data.items():
        channels_list = []
        for idx, ch in enumerate(ch_list):
            ch_id = f"{grp_name.lower().replace(' ', '-')}-{idx}"
            ch_title = ch.get("title", "Trực tiếp")
            ch_logo = ch.get("logo") or BONG_DA_VIP_LOGO
            raw_url = ch.get("url", "")
            provider = ch.get("provider", "")
            
            # Gắn User-Agent và Referer chuẩn vào stream url
            stream_url = resolve_stream_url(raw_url, provider)
            
            channel_obj = {
                "id": ch_id,
                "name": ch_title,
                "image": {
                    "display": "contain",
                    "shape": "square",
                    "url": ch_logo,
                    "height": 101,
                    "width": 155
                },
                "type": "single",
                "display": "text-below",
                "sources": [
                    {
                        "id": ch_id,
                        "name": "",
                        "contents": [
                            {
                                "id": ch_id,
                                "name": "",
                                "streams": [
                                    {
                                        "id": ch_id,
                                        "name": ch_title,
                                        "image": {
                                            "display": "contain",
                                            "shape": "square",
                                            "url": ch_logo,
                                            "height": 101,
                                            "width": 155
                                        },
                                        "stream_links": [
                                            {
                                                "id": ch_id,
                                                "name": ch_title,
                                                "url": stream_url,
                                                "type": "hls" if ".m3u8" in stream_url else "flv",
                                                "default": True
                                            }
                                        ],
                                        "remote_data": None
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            channels_list.append(channel_obj)
            
        group_obj = {
            "id": grp_name.lower().replace(' ', '-'),
            "name": grp_name,
            "channels": channels_list
        }
        groups_list.append(group_obj)

    # Root cấu trúc JSON tổng "Bóng Đá VIP"
    root_json = {
        "id": "BongDaVIP",
        "name": "Bóng Đá VIP",
        "color": "#FF6B35",
        "org_metadata": {
            "image": BONG_DA_VIP_LOGO,
            "title": "Hệ thống kênh Bóng Đá VIP Tổng Hợp",
            "description": "Danh sách các kênh thể thao trực tuyến được tổng hợp tự động cho anh Sơn."
        },
        "image": {
            "display": "contain",
            "shape": "square",
            "url": BONG_DA_VIP_LOGO,
            "height": 101,
            "width": 155
        },
        "grid_number": 1,
        "groups": groups_list
    }

    output_filename = "playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(root_json, f, ensure_ascii=False, indent=2)
        
    print(f"Đã tạo thành công file {output_filename} cấu trúc Projectivy chuẩn xác!")

if __name__ == "__main__":
    generate_projectivy_json()
    
