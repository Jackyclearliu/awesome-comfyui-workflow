---
description: 本工作流仓库涉及的 ComfyUI 自定义节点仓库清单、GitHub 地址、功能说明与典型使用场景。
---

# ComfyUI 自定义节点仓库说明

> 汇总本机 `ComfyUI/custom_nodes` 目录中的 16 个仓库，帮助使用者在导入工作流前补齐所需插件。

## 目录

- [使用说明](#使用说明)
- [仓库清单](#仓库清单)
- [术语说明](#术语说明)
- [安装与维护建议](#安装与维护建议)

## 使用说明

- 工作流 JSON 只保存节点及其连接关系，不包含节点代码、Python 依赖或模型权重。导入后出现红色缺失节点时，应先安装对应仓库，再安装依赖并重启 ComfyUI。
- 并非每个工作流都需要下表全部仓库；请根据界面提示的缺失节点选择安装。`comfyui-manager` 可辅助查找和安装缺失节点。
- 链接统一使用 GitHub 原始地址，不包含下载加速代理。`ComfyUI-llama-cpp_vlm` 使用本机实际安装的 fork；其余地址对应当前安装仓库或其 README 声明的上游仓库。
- 安装节点库不代表模型已经就绪。Krea 2、Bernini-R、IndexTTS、GGUF 多模态模型及 ControlNet 预处理器等仍需按各仓库说明准备权重。

## 仓库清单

| 仓库名 | 仓库 GitHub 地址 | 节点库简要说明 | 典型使用场景 |
| --- | --- | --- | --- |
| `ComfyUI-BerniniR` | [neuregex/ComfyUI-BerniniR](https://github.com/neuregex/ComfyUI-BerniniR) | Bernini-R 模型加载、文本编码、采样、解码与视频保存节点，支持参考图像或视频参与生成。 | 文生视频、参考图生图、图像编辑、视频编辑与参考视频生视频。 |
| `ComfyUI-Easy-Use` | [yolain/ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | 以 PIPE 管线为核心的大型整合包，提供一键加载器、采样器、XY 参数对比，以及 IP-Adapter、InstantID、PuLID、IC-Light 等封装。 | 简化模型加载与采样连线、批量调参、风格迁移、人脸修复、身份保持与打光。 |
| `ComfyUI-KJNodes` | [kijai/ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | Kijai 维护的多功能工具集，涵盖遮罩与图像批处理、批量裁剪恢复、曲线关键帧、编译加速和视频模型辅助。 | 局部重绘、批量裁脸后贴回、动画遮罩、视频工作流调优与采样提速。 |
| `ComfyUI-Krea2-Ostris-Edit` | [ostris/ComfyUI-Krea2-Ostris-Edit](https://github.com/ostris/ComfyUI-Krea2-Ostris-Edit) | 为使用 ai-toolkit 训练的 Krea 2 编辑 LoRA 提供多图条件编码和模型补丁，支持参考 latent 及可选 KV 缓存。 | 运行 Ostris 训练方式的 Krea 2 编辑 LoRA、单图或多参考图编辑。 |
| `ComfyUI-llama-cpp_vlm` | [Jackyclearliu/ComfyUI-llama-cpp_vlm](https://github.com/Jackyclearliu/ComfyUI-llama-cpp_vlm) | 本机使用的 fork，通过 llama.cpp 在本地运行 GGUF 多模态模型，并扩展 QwenTE 推理、多轮对话、提示词增强与结构化结果解析节点。 | 本地图像反推、提示词扩写、视觉问答、多轮创意讨论，以及生成 BBOX 供检测或分割流程使用。 |
| `ComfyUI_Comfyroll_CustomNodes` | [Suzie1/ComfyUI_Comfyroll_CustomNodes](https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes) | CR 系列综合工具箱，提供文本与列表处理、图形和排版模板、宽高比预设、输入切换、动画调度及模型/LoRA/ControlNet 堆栈。 | 社媒物料与简单排版、水印、提示词拼装、多模型轮换、按帧调度和分支调试。 |
| `ComfyUI_LayerStyle` | [chflame163/ComfyUI_LayerStyle](https://github.com/chflame163/ComfyUI_LayerStyle) | Photoshop 式图像工具箱，覆盖图层样式、混合合成、调色、遮罩、滤镜、文字、裁剪恢复和批量处理。 | 海报与封面合成、文字和水印叠加、图像调色、局部处理后原位贴回。 |
| `ComfyUI_essentials` | [cubiq/ComfyUI_essentials](https://github.com/cubiq/ComfyUI_essentials) | 轻量基础增强集，提供图像与遮罩编辑、尺寸和数学运算、简单逻辑、LUT 调色、CLIPSeg 分割及采样辅助。 | 获取图像尺寸、裁剪翻转、基础调色、遮罩处理和通用工作流工具补充。 |
| `Comfyui-Anima-Wardrobe-V6` | [lingdongbudong/Comfyui-Anima-Wardrobe-V6](https://github.com/lingdongbudong/Comfyui-Anima-Wardrobe-V6) | ANIMA3 本地提示词工具，可按角色、服装、场景、姿势和内容档位随机组合文本，并进行检查、清理与修复；不直接生成图片。 | 角色与服装创意探索、可复现随机提示词、为 Anima 或其他出图模型准备文本。 |
| `Comfyui-K2-Editorial` | [lingdongbudong/Comfyui-K2-Editorial](https://github.com/lingdongbudong/Comfyui-K2-Editorial) | Krea 2 白垩光编辑主视觉提示词装配器，内置 3D 场景、平面海报和短提示词母题，输出提示词、自检报告与元数据。 | 时尚大片、奢华主视觉、平面海报及角色服装替换的提示词设计。 |
| `Goohaitools-comfyui` | [goohai/Goohaitools-comfyui](https://github.com/goohai/Goohaitools-comfyui) | 孤海工具箱，面向证件照、写真和批量生产，提供文件批处理、DPI 保存、裁剪恢复、排版、人脸对齐、取色及 Qwen 提示词优化等功能。 | 证件照与写真批处理、自动排版、图像缩放裁剪、封面设计和图像视频对比。 |
| `comfyui-index-tts25` | [maikarlone/comfyui-index-tts25](https://github.com/maikarlone/comfyui-index-tts25) | IndexTTS 2.5 零样本语音合成节点，支持参考音色、情感音频、情感文本、情感向量及小说文本结构化。 | 视频旁白、有声内容、声音克隆、情感配音和多人小说配音。 |
| `comfyui-krea2edit` | [lbouaraba/comfyui-krea2edit](https://github.com/lbouaraba/comfyui-krea2edit) | Krea 2 编辑模型的条件编码与模型补丁节点，将编辑指令和参考图区域对齐，并适配编辑模型的采样过程。 | Krea 2 单图或双图编辑、局部修改、图像扩展及人物身份保持。 |
| `comfyui-manager` | [Comfy-Org/ComfyUI-Manager](https://github.com/Comfy-Org/ComfyUI-Manager) | ComfyUI 管理工具，用于安装、删除、启用和禁用插件，并提供模型下载及缺失节点辅助安装；不提供生成类工作流节点。 | 初始化节点环境、补装工作流缺失节点、管理插件和下载模型。 |
| `comfyui_controlnet_aux` | [Fannovel16/comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux) | ControlNet 预处理器合集，覆盖姿态、深度、法线、线稿、语义分割、光流和瓦片等提示图生成方式。 | 姿态控制、深度控制、线稿出图、参考图结构提取及高清修复预处理。 |
| `rgthree-comfy` | [rgthree/rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | 工作流效率与整理工具，提供 Context 管线、Power Prompt、LoRA 管理、种子、开关、重路由、数据显示和图像对比节点。 | 减少复杂连线、模块化管理模型与条件、调试输出、固定种子和图像 AB 对比。 |

## 术语说明

| 术语 | 含义 | 本文中的使用场景 |
| --- | --- | --- |
| 自定义节点 | 为 ComfyUI 增加模型、图像处理、文本或管理能力的插件。 | 导入工作流前需安装其引用的节点库。 |
| ControlNet | 利用姿态、深度、线稿等参考信息约束图像生成的技术。 | `comfyui_controlnet_aux` 负责生成控制参考图。 |
| GGUF | 常用于 llama.cpp 的量化模型文件格式。 | 本地运行多模态语言模型，减少显存占用。 |
| VLM | 视觉语言模型，可同时理解图像和文本。 | 图像反推、视觉问答和提示词增强。 |
| LoRA | 对基础生成模型进行轻量微调的权重文件。 | 风格、身份或特定编辑能力扩展。 |
| PIPE / Context | 将模型、文本编码器、VAE、条件等多个值打包成一条连接的方式。 | Easy-Use 与 rgthree 用于减少重复连线。 |
| VAE | 在图像与 latent 表示之间编码、解码的模型组件。 | 图像生成、参考图编码和最终解码。 |
| BBOX | 目标区域的边界框坐标。 | 将视觉模型检测结果转换为遮罩或裁剪区域。 |
| KV 缓存 | 复用注意力计算中的键和值，避免重复计算的缓存。 | 加速多参考图编辑或多轮语言模型推理。 |
| IndexTTS | 支持参考音色和情感控制的文本转语音模型。 | 视频旁白与多人配音。 |

## 安装与维护建议

1. 优先使用 ComfyUI Manager 安装；手动安装时，将仓库放入 `ComfyUI/custom_nodes/<仓库目录>`。
2. 阅读目标仓库的 `README.md`，并按其 `requirements.txt` 或 `pyproject.toml` 安装依赖，避免只复制代码而遗漏运行环境。
3. 重启 ComfyUI，检查启动日志是否出现导入错误，并确认原工作流中的缺失节点已经消失。
4. 按工作流和节点说明准备模型权重、文本编码器、VAE、LoRA 或预处理器模型；这些文件通常不随节点仓库分发。
5. 更新插件前记录当前版本并保留工作流备份。更新后同时核对节点新增、删除、改名及输入输出变化。

---

> **Document Version**: v1.0
> **Last Updated**: 2026-11-23
> **Applicable Version**: 本机 `custom_nodes` 目录快照（16 个仓库）
>
> **Reference Documents**:
> - [ComfyUI 官方仓库](https://github.com/Comfy-Org/ComfyUI)
> - [ComfyUI Manager](https://github.com/Comfy-Org/ComfyUI-Manager)
> - 各节点仓库的 README，链接见[仓库清单](#仓库清单)。
