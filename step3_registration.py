# step3_registration.py (最终版)
import subprocess
import os

def registration(src_path, dst_path, ref_path):
    """使用FLIRT将图像配准到标准空间"""
    print(f"正在将 {src_path} 配准到模板 {ref_path}...")
    command = ["flirt", "-in", src_path, "-ref", ref_path, "-out", dst_path,
               "-bins", "256", "-cost", "corratio", "-searchrx", "0", "0",
               "-searchry", "0", "0", "-searchrz", "0", "0", "-dof", "12",
               "-interp", "spline"]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"成功创建配准后的图像: {dst_path}")
    except FileNotFoundError:
        print("错误: 'flirt' 命令未找到。FSL是否已安装并配置在您的PATH中？")
    except subprocess.CalledProcessError as e:
        print(f"FLIRT 命令执行失败: {e.stderr}")

# --- 配置 ---
# 第2步的输出文件作为本步骤的输入
src_path = "PPMI_3612_brain.nii.gz"
# 输出的配准后图像
dst_path = "PPMI_3612_brain_registered.nii.gz"
# 标准大脑模板的路径 (已更新为您的系统上的正确路径)
ref_path = "/home/troy/fsl/data/standard/MNI152_T1_1mm_brain.nii.gz"
# --- 结束配置 ---

if not os.path.exists(src_path):
    print(f"错误: 输入文件未找到 {src_path}")
elif not os.path.exists(ref_path):
    print(f"错误: 模板文件未找到 {ref_path}")
else:
    registration(src_path, dst_path, ref_path)