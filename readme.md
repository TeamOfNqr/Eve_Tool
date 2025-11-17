## 简介
  这是一个EVE帮助程序，使用纯视觉分析完成对游戏内容或是关键节点的理解
## 使用
  1. 区域初始化
  2. 
## 部署环境
- 部分环境链接
  - [paddlepaddle-gpu 快速部署](https://www.paddlepaddle.org.cn/install/quick?docurl=/documentation/docs/zh/develop/install/pip/windows-pip.html)
  - [CUDA12.9 Windows](https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda_12.9.0_576.02_windows.exe)
  - [Scoop 安装](https://csdiy.wiki/%E5%BF%85%E5%AD%A6%E5%B7%A5%E5%85%B7/Scoop/)
  - [PaddleOCR 文档](https://www.paddleocr.ai/main/index.html)


```
# 快速环境部署
conda create --name EveTool_Env python=3.12
conda activate EveTool_Env
pip install PyQt6 pyautogui paddleocr dotenv easyocr src pywin32
```
```
# 选装
scoop install ccache
```