#!/bin/bash
set -e

# 加载 conda 初始化脚本（请确保路径正确，这里假设你在 /home/pc/anaconda3 里）
source /home/pc/anaconda3/etc/profile.d/conda.sh
conda activate cbct

echo "Using Python: $(which python)"
echo "当前工作目录: $(pwd)"

# 设置 GPU 环境变量
export CUDA_VISIBLE_DEVICES=0

# 单个图的推理命令
python ./inference.py --dataset 3D-CBCT-Tooth \
        --model TMamba3D --dimension 3d \
        --scaling_version TINY \
        --pretrain_weight /mnt/d/AIbot/DentalCTSeg-main/T-Mamba/runs/2024-07-28-22-48-49_TMamba3D_3D-CBCT-Tooth/checkpoints/best_TMamba3D.pth \
        --save_dir ./runs \
        --image_path /mnt/d/AIbot/DentalCTSeg-main/T-Mamba/images/1000813648_20180116.nii.gz
