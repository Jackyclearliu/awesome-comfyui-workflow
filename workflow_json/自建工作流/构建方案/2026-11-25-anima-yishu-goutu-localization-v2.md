# Anima 艺术构图工作流本地化改造 · v2 方案（风格还原优先）

日期：2026-11-25
产物：`workflow/workflow_json/自建工作流/Anima-艺术构图_提示词模板工作流.json`（覆盖同名旧 v1 文件）
基线：`custom_nodes/Comfyui-Anima-Wardrobe-V6/workflows/Anima-艺术构图_哑光人物_29B_16x9.json`（18 节点，官方文件不改动）

## 一、v1 验收问题诊断

主人实测：v1 出图风格与质量相比官方差距明显。逐项排查后定位四个真实偏差（按嫌疑排序）：

### 1. LoRA 配方错误（主因）
- v1 把 `anima-base-1-masterpiece-v51` 设为**开启 0.60**，并静态前置触发词 `masterpiece, very aesthetic`。
- 官方基线的配方状态（节点 19 widgets 权威）：**只有 turbo 0.85 与 light-concepts 0.30 开启**，masterpiece 关闭。
- masterpiece 是画质增强 LoRA，叠加其触发词会明显改变画风——这是风格差距的最大来源。

### 2. 采样器误判
- v1 结论「er_sde 本机无注册」**错误**。实际本机 ComfyUI 核心已原生注册：
  `comfy/samplers.py` `KSAMPLER_NAMES` 含 `"er_sde"`，`comfy/k_diffusion/sampling.py:1593` 有 `sample_er_sde`。
- 原生 KSampler 可直接用 `sampler_name="er_sde"`，无需任何替代，官方采样轨迹可完全复现。

### 3. 触发词机制被静态猜测替代
- 官方链路：`Lora Loader (LoraManager)` 的 `trigger_words` 输出 → `Prompt (LoraManager)` 的 `trigger_words1` 输入，运行时动态前置（`, ` 拼接）。
- v1 用 PrimitiveStringMultiline 静态写死 `masterpiece, very aesthetic`，属于双重错误（既错词又错机制）。
- 现在本机已安装 ComfyUI-Lora-Manager，两个官方节点原样可用（已核对节点类 `LoraLoaderLM`/`PromptLM` 与安装版本契约一致）。

### 4. 种子语义不同
- 官方：主采种子 `265521198872240` **fixed**，二采 `265521198872241`（=主采+1）**fixed**。
- v1：randomize + 主二采共享同一 PrimitiveInt 种子。验收对比时两边构图不同，放大了「差距感」。
- v2 直接采用官方 fixed 种子，保证同场景严格对拍；想随机出图把 control_after_generate 改回 randomize 即可。

### 非因素（保留剔除）
- XB_SageAttentionAccelerator：attention 数值优化，对画风影响可忽略，继续剔除。

## 二、v2 构建决策

原则：**官方部件原样恢复，仅替换本机确实没有的 XB 三件套**。

| 部件 | 官方 | v2 处置 |
|---|---|---|
| UNETLoader / CLIPLoader | 节点 1 / 2 | 原样 |
| VAELoader | 节点 3（`Qwen\qwen_image_vae.safetensors`） | 路径改 `qwen_image_vae.safetensors`（本机在 models/vae 根目录） |
| AnimaV6RandomPrompt | 节点 6 巨型面板 | 原样 |
| Prompt (LoraManager) | 节点 7 | **原样恢复**（widgets 官方序列化原封拷贝） |
| 负向 CLIPTextEncode | 节点 8 | 官方 position 值即 317 字长版，原样 |
| XB_ImageParamsMaster | 节点 9 | 剔除；EmptyLatentImage 改裸控件 1536×864（Anima 面板画幅联动可回退写它） |
| XB_ROCmKSampler ×2 | 节点 11 / 16 | 原生 KSampler，官方参数逐项照搬（fixed 种子 / er_sde / beta / 16·2.0·1 与 6·2.0·0.2） |
| XB_ROCmVAEDecode ×2 | 节点 12 / 17 | VAEDecodeTiled 320/32/64/8 |
| SaveImage | 节点 13（position 前缀 `图片/艺术构图_哑光/构图_`） | 原样 |
| ImageScaleBy / VAEEncodeTiled | 节点 14 / 15 | 原样 |
| LazySwitchKJ | 节点 18（默认 True=二采输出） | 原样 |
| Lora Loader (LoraManager) | 节点 19 | **原样恢复**，六行配方 active 状态照抄官方 |

触发词链路恢复：`19.trigger_words → 7.trigger_words1`、`19.CLIP → 7.clip`、`6.text → 7.text`。

### 关于本地触发词的预期
本机 Anima LoRA 文件仅含 `format` 元数据、无 CivitAI trainedWords，LoraManager 扫描缓存里 trigger_words 预计为空串 → Prompt 节点实际不前置任何词。这与官方基线意图不冲突（指南：turbo 无触发词；light-concepts 触发词实测作用很弱）。若日后在 LoraManager 中同步 CivitAI 元数据，触发词会自动恢复前置，无需改工作流。

## 三、结构清单（19 节点 / 25 连线 / 6 分组）

节点：1 UNETLoader、2 CLIPLoader、3 VAELoader(改路径)、6 AnimaV6RandomPrompt、7 Prompt(LM)、8 负向编码、10 EmptyLatentImage(裸 1536×864)、11 KSampler(主采)、12 VAEDecodeTiled、13 SaveImage、14 ImageScaleBy、15 VAEEncodeTiled、16 KSampler(二采)、17 VAEDecodeTiled、18 LazySwitchKJ、19 Lora Loader(LM)、29 Label(rgthree)。

与 v1 的差异：删除 v1 新增的 Power Lora Loader(20)、静态触发词(21)、拼接(22)、CLIPTextEncode(23)、共享种子(24)；KSampler 编号 25/27 → 11/16；解码 26/28 → 12/17。

## 四、验收标准

1. 静态校验（同 v1 校验器升级）：连线完整性、无 XB_/Power Lora Loader 残留、widgets 一致性、er_sde ∈ KSAMPLER_NAMES、六行配方逐行核对（turbo on 0.85 / light-concepts on 0.3 / 其余 off，注意 gouache 官方 strength=0.9）、模型文件存在性、KSampler 参数 = (fixed, 16/2.0/er_sde/beta/1) 与 (fixed, 6/2.0/er_sde/beta/0.2)。
2. 真实执行：与官方工作流同场景（同 seed 已天然保证：两边都是 fixed 种子 + Anima 面板随机出题种子各自 randomize……注意：Anima 面板种子是 randomize，严格对拍需把两边面板 seed 都手动固定为同一值）。
3. 对拍通过后即可把 v1 经验 + 本次诊断回写 comfyui-workflow-craft skill。
