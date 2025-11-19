## 简介
  这是一个EVE帮助程序，使用纯视觉分析完成对游戏内容或是关键节点的理解
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
PS： 如果仍有缺失，请自行补充 (实则是没招了
```
```
# 选装
scoop install ccache
```
## 使用
### 信息栏
- 在信息栏你可以快速启动控制脚本，但是请不要忘记初始化哦
![信息栏](assets/image/信息栏.png "信息栏")
### 主控制台
- 使用前请进行区域初始化
![区域初始化](assets/image/初始化位置.png "初始化")
### 矿石选择
- 在矿石选择页面对你想要挖掘的矿石进行精细挑选
![矿石选择](assets/image/矿石选择.png "矿石选择")
### 窗口控制
- 窗口控制页面内置了账号窗口快速切换功能
![窗口控制](assets/image/窗口控制_大.png "窗口控制")
![窗口控制](assets/image/窗口控制_小.png "窗口控制")



## 关于
- 本软件以及功能仅作学习用途，请不要将其用于正式用于公开运行的公共服务器上

