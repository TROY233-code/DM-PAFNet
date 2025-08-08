# step2_skull_stripping.py (高级版)
import subprocess
import os


def bet(src_path, dst_path, frac="0.5"):
    """使用BET进行颅骨剥离，并添加-B选项进行颈部清理"""
    print(f"正在进行颅骨剥离 (阈值: {frac}, 清理颈部: 是)...")

    # 在命令中添加了 "-B" 选项
    command = ["bet", src_path, dst_path, "-R", "-B", "-f", frac, "-g", "0"]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"成功创建剥离颅骨后的大脑图像: {dst_path}")
    except FileNotFoundError:
        print("错误: 'bet' 命令未找到。FSL是否已安装并配置在您的PATH中？")
    except subprocess.CalledProcessError as e:
        print(f"BET 命令执行失败: {e.stderr}")


# --- 配置 ---
# 第1步的输出文件作为本步骤的输入
src_path = "PPMI_3612_oriented.nii.gz"
# 输出的仅含大脑的图像
dst_path = "PPMI_3612_brain.nii.gz"
# 当使用 -B 选项时，建议将阈值重设为 0.5 开始尝试
fractional_threshold = "0.5"
# --- 结束配置 ---

if not os.path.exists(src_path):
    print(f"错误: 输入文件未找到 {src_path}")
else:
    bet(src_path, dst_path, fractional_threshold)