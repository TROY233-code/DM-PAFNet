# step1_reorient.py
import subprocess
import os

def orient2std(src_path, dst_path):
    """使用fslreorient2std将图像重定位到标准方向"""
    print(f"正在将 {src_path} 重定位到标准方向...")
    command = ["fslreorient2std", src_path, dst_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"成功创建重定位后的图像: {dst_path}")
    except FileNotFoundError:
        print("错误: 'fslreorient2std' 命令未找到。FSL是否已安装并配置在您的PATH中？")
    except subprocess.CalledProcessError as e:
        print(f"fslreorient2std 命令执行失败: {e.stderr}")

# --- 配置 ---
# 输入的原始图像
src_path = "PPMI_3612.nii.gz"
# 输出的重定位后的图像
dst_path = "PPMI_3612_oriented.nii.gz"
# --- 结束配置 ---

if not os.path.exists(src_path):
    print(f"错误: 输入文件未找到 {src_path}")
else:
    orient2std(src_path, dst_path)