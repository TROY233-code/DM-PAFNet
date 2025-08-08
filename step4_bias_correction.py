# step4_bias_correction.py
import os
from nipype.interfaces.ants.segmentation import N4BiasFieldCorrection

def bias_field_correction(src_path, dst_path):
    print("正在进行N4偏置场校正: ", src_path)
    try:
        n4 = N4BiasFieldCorrection()
        n4.inputs.input_image = src_path
        n4.inputs.output_image = dst_path
        n4.inputs.dimension = 3
        n4.inputs.n_iterations = [100, 100, 60, 40]
        n4.inputs.shrink_factor = 3
        n4.inputs.convergence_threshold = 1e-4
        n4.inputs.bspline_fitting_distance = 300
        print("正在运行N4... 这可能需要几分钟时间。")
        n4.run()
        print("成功创建经偏置场校正的图像: ", dst_path)
    except Exception as e:
        print("\t处理失败: ", src_path)
        print("\t错误信息: ", e)
        print("\t请确保ANTs已正确安装，并且Nipype可以找到它。")

# --- 配置 ---
src_path = "PPMI_3612_brain_registered.nii.gz"
dst_path = "PPMI_3612_brain_registered_n4.nii.gz"
# --- 结束配置 ---

if not os.path.exists(src_path):
    print(f"错误: 输入文件未找到 {src_path}")
else:
    bias_field_correction(src_path, dst_path)