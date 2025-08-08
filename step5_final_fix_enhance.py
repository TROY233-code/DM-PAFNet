# improved_enhance.py (改进版 - 保护脑沟信息)
from __future__ import print_function
import os
import numpy as np
import nibabel as nib
from scipy.signal import medfilt
from scipy import ndimage


def load_nii(path):
    nii = nib.load(path)
    return nii.get_fdata(), nii.affine


def save_nii(data, path, affine):
    nib.save(nib.Nifti1Image(data, affine), path)


def create_brain_mask(volume, method='otsu'):
    """
    创建更智能的脑部掩码，保护脑沟等低信号区域
    """
    if method == 'otsu':
        # 使用Otsu阈值法自动确定背景阈值
        hist, bins = np.histogram(volume.flatten(), bins=256, range=(0, volume.max()))
        hist = hist.astype(float)

        # Otsu算法
        bin_centers = (bins[:-1] + bins[1:]) / 2
        weight1 = np.cumsum(hist)
        weight2 = np.cumsum(hist[::-1])[::-1]

        mean1 = np.cumsum(hist * bin_centers) / (weight1 + 1e-10)
        mean2 = (np.cumsum((hist * bin_centers)[::-1]) / (weight2 + 1e-10))[::-1]

        variance = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
        idx = np.argmax(variance)
        threshold = bin_centers[idx]

        print(f"Otsu阈值: {threshold:.2f}")

    elif method == 'percentile':
        # 使用百分位数法
        threshold = np.percentile(volume[volume > 0], 5)  # 使用5%分位数
        print(f"百分位阈值: {threshold:.2f}")

    else:  # adaptive
        # 自适应阈值：基于非零像素的统计特性
        nonzero_voxels = volume[volume > 0]
        if len(nonzero_voxels) == 0:
            threshold = 0
        else:
            mean_val = np.mean(nonzero_voxels)
            std_val = np.std(nonzero_voxels)
            threshold = max(mean_val - 2 * std_val, np.percentile(nonzero_voxels, 1))
        print(f"自适应阈值: {threshold:.2f}")

    # 创建初始掩码
    brain_mask = volume > threshold

    # 形态学操作去除小的噪声区域
    # 先闭运算填充小洞，再开运算去除小噪点
    from scipy import ndimage
    brain_mask = ndimage.binary_closing(brain_mask, structure=np.ones((3, 3, 3)))
    brain_mask = ndimage.binary_opening(brain_mask, structure=np.ones((2, 2, 2)))

    # 保留最大连通区域（大脑主体）
    labeled_mask, num_labels = ndimage.label(brain_mask)
    if num_labels > 0:
        # 找到最大的连通区域
        region_sizes = ndimage.sum(brain_mask, labeled_mask, range(1, num_labels + 1))
        largest_region = np.argmax(region_sizes) + 1
        brain_mask = labeled_mask == largest_region

        # 适度膨胀以包含更多边缘信息
        brain_mask = ndimage.binary_dilation(brain_mask, structure=np.ones((3, 3, 3)), iterations=2)

    return brain_mask


def enhance_masked_improved(volume, mask_method='adaptive', kernel_size=3, percentiles=[1, 99], bins_num=256, eh=True,
                            black_background=True, refine_mask=True):
    """
    改进的掩码增强算法，更好地保护脑沟等结构

    Parameters:
    - black_background: True保持纯黑背景，False允许边界平滑
    - refine_mask: True进行掩码精细化，去除边缘"膜状"区域
    """
    print(f"使用掩码方法: {mask_method}")

    # 1. 创建智能脑部掩码
    brain_mask = create_brain_mask(volume, method=mask_method)

    # 2. 掩码精细化处理（针对percentile等保守方法）
    if refine_mask and mask_method in ['percentile', 'otsu']:
        print("执行掩码精细化...")
        # 更激进的形态学操作，去除边缘"膜状"区域
        brain_mask = ndimage.binary_erosion(brain_mask, structure=np.ones((2, 2, 2)), iterations=1)
        brain_mask = ndimage.binary_dilation(brain_mask, structure=np.ones((3, 3, 3)), iterations=1)

        # 基于强度进一步筛选，去除低信号边缘区域
        intensity_threshold = np.percentile(volume[volume > 0], 10)  # 使用10%分位数
        high_intensity_mask = volume > intensity_threshold
        brain_mask = brain_mask & high_intensity_mask

        # 再次保留最大连通区域
        labeled_mask, num_labels = ndimage.label(brain_mask)
        if num_labels > 0:
            region_sizes = ndimage.sum(brain_mask, labeled_mask, range(1, num_labels + 1))
            largest_region = np.argmax(region_sizes) + 1
            brain_mask = labeled_mask == largest_region

    print(f"掩码覆盖的体素数量: {np.sum(brain_mask)} / {volume.size}")

    # 3. 对整个容积进行轻度去噪
    denoised_volume = medfilt(volume, kernel_size)

    # 4. 提取脑部区域像素值
    if not np.any(brain_mask):
        print("警告: 没有找到脑组织！")
        return np.zeros_like(volume)

    brain_voxels = denoised_volume[brain_mask]

    # 5. 更温和的强度重缩放（保护低信号区域）
    min_value = np.percentile(brain_voxels, percentiles[0])
    max_value = np.percentile(brain_voxels, percentiles[1])

    print(f"强度范围: [{min_value:.2f}, {max_value:.2f}]")

    if max_value > min_value:
        # 使用更温和的缩放，避免过度拉伸
        brain_voxels_scaled = (brain_voxels - min_value) / (max_value - min_value) * (bins_num - 1)
        brain_voxels_scaled = np.clip(brain_voxels_scaled, 0, bins_num - 1)
    else:
        brain_voxels_scaled = brain_voxels

    # 6. 可选的直方图均衡化（更温和）
    if eh:
        # 使用CLAHE（对比度限制的自适应直方图均衡化）的简化版本
        hist, bins = np.histogram(brain_voxels_scaled.flatten(), bins_num, density=True)
        cdf = hist.cumsum()
        cdf = (bins_num - 1) * cdf / cdf[-1]

        # 限制对比度增强的程度
        brain_voxels_eq = np.interp(brain_voxels_scaled, bins[:-1], cdf)

        # 混合原始和均衡化结果（保护低信号区域）
        alpha = 0.7  # 均衡化权重
        brain_voxels_final = alpha * brain_voxels_eq + (1 - alpha) * brain_voxels_scaled
    else:
        brain_voxels_final = brain_voxels_scaled

    # 7. 创建输出容积 - 严格的黑色背景
    enhanced_volume = np.zeros_like(volume, dtype=np.float64)
    enhanced_volume[brain_mask] = brain_voxels_final

    # 8. 可选的边界处理（仅在不要求纯黑背景时）
    if not black_background:
        # 创建一个稍微扩大的掩码用于边界平滑
        expanded_mask = ndimage.binary_dilation(brain_mask, structure=np.ones((2, 2, 2)))
        boundary_mask = expanded_mask & (~brain_mask)

        if np.any(boundary_mask):
            # 对边界区域应用轻微的原始信号
            enhanced_volume[boundary_mask] = denoised_volume[boundary_mask] * 0.2

    return enhanced_volume


def process_with_multiple_methods(volume, affine, base_name):
    """
    使用多种方法处理并保存结果，便于比较
    """
    # 定义不同的处理配置
    configs = {
        'adaptive_black': {
            'method': 'adaptive',
            'black_background': True,
            'refine_mask': False,
            'description': 'adaptive方法，纯黑背景'
        },
        'percentile_refined': {
            'method': 'percentile',
            'black_background': True,
            'refine_mask': True,
            'description': 'percentile方法，去除边缘膜，纯黑背景'
        },
        'otsu_refined': {
            'method': 'otsu',
            'black_background': True,
            'refine_mask': True,
            'description': 'otsu方法，去除边缘膜，纯黑背景'
        }
    }

    results = {}

    for config_name, config in configs.items():
        print(f"\n=== {config['description']} ===")
        try:
            enhanced = enhance_masked_improved(
                volume,
                mask_method=config['method'],
                black_background=config['black_background'],
                refine_mask=config['refine_mask']
            )
            output_path = f"{base_name}_{config_name}.nii.gz"
            save_nii(enhanced, output_path, affine)
            results[config_name] = output_path
            print(f"保存完成: {output_path}")
        except Exception as e:
            print(f"配置 {config_name} 失败: {e}")

    return results


# --- 主程序 ---
if __name__ == "__main__":
    # 配置
    src_path = "PPMI_3612_brain_registered_n4.nii.gz"  # 修正了文件名
    base_name = "PPMI_3612_enhanced"

    print("开始改进版MRI T1图像增强...")

    try:
        # 加载数据
        volume, affine = load_nii(src_path)
        print(f"加载图像: {volume.shape}, 数据范围: [{volume.min():.2f}, {volume.max():.2f}]")

        # 使用多种方法处理
        results = process_with_multiple_methods(volume, affine, base_name)

        print(f"\n=== 处理完成 ===")
        print("生成的文件:")
        for config_name, path in results.items():
            print(f"  {config_name}: {path}")

        print("\n建议:")
        print("1. adaptive_black: 自适应方法，纯黑背景，保护脑沟")
        print("2. percentile_refined: 保守方法，去除边缘膜，适合特征提取")
        print("3. otsu_refined: 经典方法，平衡效果")
        print("\n推荐用于特征提取: percentile_refined")

    except FileNotFoundError:
        print(f"错误: 找不到文件 {src_path}")
        print("请确认文件路径是否正确")
    except Exception as e:
        print(f"处理失败: {e}")
        import traceback

        traceback.print_exc()