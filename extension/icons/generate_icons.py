#!/usr/bin/env python3
# ============================================================
# 文件：extension/icons/generate_icons.py
# 作用：生成小鲸 OrcaAI 的 Chrome 插件图标（三个尺寸）
# 用法：python3 generate_icons.py
# 依赖：pip3 install Pillow（如果没有会自动安装）
# ============================================================
"""生成小鲸 OrcaAI 插件图标"""

import math
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("正在安装 Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image, ImageDraw


HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = [("icon16.png", 16), ("icon48.png", 48), ("icon128.png", 128)]


def draw_orca(draw, cx, cy, scale):
    """在给定的 Draw 对象上绘制虎鲸图案
    cx, cy = 画布中心, scale = 相对于 128px 的缩放比例
    """
    s = scale
    # 虎鲸身体（黑色椭圆）
    body_x1, body_y1 = cx - 30 * s, cy - 10 * s
    body_x2, body_y2 = cx + 30 * s, cy + 12 * s
    draw.ellipse([body_x1, body_y1, body_x2, body_y2], fill="#1c1c1c")

    # 白色腹部
    belly_x1, belly_y1 = cx - 18 * s, cy + 2 * s
    belly_x2, belly_y2 = cx + 18 * s, cy + 14 * s
    draw.ellipse([belly_x1, belly_y1, belly_x2, belly_y2], fill="white")

    # 白色眼斑
    eye_patch_x1, eye_patch_y1 = cx - 25 * s, cy - 12 * s
    eye_patch_x2, eye_patch_y2 = cx - 11 * s, cy - 4 * s
    draw.ellipse([eye_patch_x1, eye_patch_y1, eye_patch_x2, eye_patch_y2], fill="white")

    # 眼睛
    eye_r = 2.5 * s
    draw.ellipse(
        [cx - 18 * s - eye_r, cy - 8 * s - eye_r,
         cx - 18 * s + eye_r, cy - 8 * s + eye_r],
        fill="#1c1c1c",
    )

    # 背鳍（三角形）
    fin_top = (cx, cy - 34 * s)
    fin_left = (cx - 6 * s, cy - 22 * s)
    fin_right = (cx + 6 * s, cy - 22 * s)
    draw.polygon([fin_left, fin_top, fin_right], fill="#1c1c1c")

    # 尾鳍（两个三角形）
    tail_left = [(cx + 28 * s, cy - 2 * s), (cx + 38 * s, cy - 12 * s),
                 (cx + 38 * s, cy + 2 * s)]
    tail_right = [(cx + 28 * s, cy + 2 * s), (cx + 38 * s, cy - 2 * s),
                  (cx + 38 * s, cy + 12 * s)]
    draw.polygon(tail_left, fill="#1c1c1c")
    draw.polygon(tail_right, fill="#1c1c1c")

    # 胸鳍
    fin_pts = [(cx - 12 * s, cy + 2 * s), (cx - 22 * s, cy + 14 * s),
               (cx - 12 * s, cy + 8 * s)]
    draw.polygon(fin_pts, fill="#1c1c1c")

    # 水花
    for dx, dy, r in [(cx - 34 * s, cy - 24 * s, 3 * s),
                       (cx - 42 * s, cy - 14 * s, 2 * s),
                       (cx - 30 * s, cy - 30 * s, 1.5 * s)]:
        draw.ellipse([dx - r, dy - r, dx + r, dy + r],
                     fill="#87ceeb", outline=None)


for filename, size in SIZES:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 圆形蓝色背景
    margin = 2
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill="#1a73e8", outline="#1557b0", width=max(1, size // 40))

    # 画虎鲸
    draw_orca(draw, size / 2, size / 2, size / 128)

    out_path = os.path.join(HERE, filename)
    img.save(out_path, "PNG")
    print(f"  ✅ {filename} ({size}x{size})")

print("\n所有图标生成完毕！")
