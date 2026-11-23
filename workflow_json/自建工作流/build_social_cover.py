#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「社媒封面/配图生成器」工作流 JSON。

节点 widget 顺序/选项均取自本机 custom_nodes 源码与官方 turbo t2i 模板
（qwen_image_2_1_turbo_default_t2i.json），不要凭记忆改 widget 顺序。

用法: python build_social_cover.py
产出: 社媒封面配图生成器.json（与脚本同目录）
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(
    HERE, "..", "外部工作流", "qwen_image_2_1", "qwen_image_2_1_turbo_default_t2i.json")

# 从官方 turbo t2i 模板提取 PE 系统提示词（PrimitiveStringMultiline 的 value）
tpl = json.load(open(TEMPLATE, encoding="utf-8"))
PE_SYSTEM_PROMPT = ""
for sg in tpl["definitions"]["subgraphs"]:
    for n in sg["nodes"]:
        if n["type"] == "PrimitiveStringMultiline":
            PE_SYSTEM_PROMPT = n["widgets_values_named"]["value"]
assert PE_SYSTEM_PROMPT, "模板中未找到 PE 系统提示词"

NINE_STEP_SIGMAS = "1.0, 0.978453, 0.954180, 0.926626, 0.895080, 0.845148, 0.704534, 0.414568, 0.150000, 0"

nodes = []
links = []
_link_id = [0]


def L(src, src_slot, dst, dst_slot, typ):
    """创建连线并登记到两端节点的 link 列表。返回 link id。"""
    _link_id[0] += 1
    lid = _link_id[0]
    links.append([lid, src["id"], src_slot, dst["id"], dst_slot, typ])
    src["outputs"][src_slot]["links"].append(lid)
    dst["inputs"][dst_slot]["link"] = lid
    return lid


def node(type_, pos, size, widgets_named=None, inputs=None, outputs=None,
         title=None, properties=None, widgets_order=None):
    n = {
        "id": len(nodes) + 1,
        "type": type_,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": type_},
    }
    if title:
        n["title"] = title
    if properties:
        n["properties"].update(properties)
    if widgets_named is not None:
        n["widgets_values_named"] = widgets_named
        order = widgets_order or list(widgets_named.keys())
        n["widgets_values"] = [widgets_named[k] for k in order]
    nodes.append(n)
    return n


def sock(name, typ):
    return {"name": name, "type": typ, "link": None}


def out(name, typ):
    return {"name": name, "type": typ, "links": []}


def w_in(name, typ):
    """可连线的 widget 输入"""
    return {"name": name, "type": typ, "widget": {"name": name}, "link": None}


UE = {"widget_ue_connectable": {}, "version": "7.8", "input_ue_unconnectable": {}}

# ============ ① 尺寸比例组 ============
ratio = node(
    "GoohaiRatioAndResolution", [0, 400], [320, 300],
    {"比例": "16:9", "模式": "固定长边", "固定边像素": 1920, "百万像素": 2.0,
     "长边最小": 512, "长边最大": 2048, "自定宽度": 2350, "自定高度": 1000,
     "倍数取整": 32},
    outputs=[out("比例", "STRING"), out("宽度", "INT"), out("高度", "INT")])

# ============ ② 底图：AI 生成支线（官方 turbo t2i 配方展开） ============
gen_prompt = node(
    "PrimitiveStringMultiline", [520, -780], [560, 240],
    {"value": "适合科技公众号封面的抽象背景：深蓝紫渐变，几何光带，画面下方留白放标题"},
    outputs=[out("STRING", "STRING")], title="生成提示词（底图为AI生成时必填）")

pe_clip = node(
    "CLIPLoader", [520, -460], [560, 120],
    {"clip_name": "qwen3.5_9b_qwen_image_2.1_pe_t2i_w4a8.safetensors",
     "type": "stable_diffusion", "device": "default"},
    inputs=[w_in("clip_name", "COMBO")], outputs=[out("CLIP", "CLIP")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

pe_sys = node(
    "PrimitiveStringMultiline", [520, -1360], [560, 840],
    {"value": PE_SYSTEM_PROMPT}, outputs=[out("STRING", "STRING")],
    title="Text (System Prompt)")

pe_gen = node(
    "TextGenerate", [1160, -760], [420, 460],
    {"prompt": "", "max_length": 4096, "sampling_mode": "on",
     "sampling_mode.temperature": 1, "sampling_mode.top_k": 20,
     "sampling_mode.top_p": 0.95, "sampling_mode.min_p": 0,
     "sampling_mode.repetition_penalty": 1, "sampling_mode.seed": 0,
     "sampling_mode.presence_penalty": 1.5, "thinking": True,
     "use_default_template": True, "mtp": "auto"},
    inputs=[sock("clip", "CLIP"), w_in("prompt", "STRING"),
            w_in("max_length", "INT"), w_in("sampling_mode.seed", "INT"),
            w_in("thinking", "BOOLEAN"), sock("system_prompt", "STRING")],
    outputs=[out("generated_text", "STRING"), out("thinking", "STRING")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

pe_switch = node(
    "ComfySwitchNode", [1660, -700], [280, 80],
    {"switch": False},
    inputs=[sock("on_false", "STRING"), sock("on_true", "STRING"),
            w_in("switch", "BOOLEAN")],
    outputs=[out("output", "STRING")],
    title="提示词增强（False=直出）")

pe_preview = node(
    "PreviewAny", [1160, -220], [480, 200],
    inputs=[sock("source", "*")], outputs=[out("STRING", "STRING")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

unet = node(
    "UNETLoader", [520, 260], [560, 90],
    {"unet_name": "qwen_image2.1\\qwen_image_2.1_turbo_bf16.safetensors",
     "weight_dtype": "default"},
    inputs=[w_in("unet_name", "COMBO")], outputs=[out("MODEL", "MODEL")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

clip = node(
    "CLIPLoader", [520, 400], [560, 120],
    {"clip_name": "qwen3.5_9b_int8_convrot.safetensors",
     "type": "qwen_image", "device": "default"},
    inputs=[w_in("clip_name", "COMBO")], outputs=[out("CLIP", "CLIP")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

vae = node(
    "VAELoader", [520, 560], [560, 70],
    {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"},
    inputs=[w_in("vae_name", "COMBO")], outputs=[out("VAE", "VAE")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

cache = node(
    "QwenImage21Cache", [1160, 260], [280, 90],
    {"device": "auto", "dtype": "default"},
    inputs=[sock("model", "MODEL"), w_in("device", "COMBO"), w_in("dtype", "COMBO")],
    outputs=[out("MODEL", "MODEL")], properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

tenc = node(
    "TextEncodeQwenImage21", [1160, 420], [380, 190],
    {"prompt": "", "negative_prompt": "", "resolution": 1024},
    inputs=[sock("clip", "CLIP"), sock("images.image_1", "IMAGE"),
            sock("vae", "VAE"), w_in("prompt", "STRING"),
            w_in("negative_prompt", "STRING")],
    outputs=[out("positive", "CONDITIONING"), out("negative", "CONDITIONING"),
             out("latent", "LATENT")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

empty_latent = node(
    "EmptyLatentImage", [1160, 660], [320, 120],
    {"width": 1920, "height": 1080, "batch_size": 1},
    inputs=[w_in("width", "INT"), w_in("height", "INT")],
    outputs=[out("LATENT", "LATENT")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

cfg_guider = node(
    "CFGGuider", [1660, 420], [280, 100],
    {"cfg": 1},
    inputs=[sock("model", "MODEL"), sock("positive", "CONDITIONING"),
            sock("negative", "CONDITIONING")],
    outputs=[out("GUIDER", "GUIDER")], properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

sampler_select = node(
    "KSamplerSelect", [1660, 660], [280, 60],
    {"sampler_name": "euler"}, inputs=[w_in("sampler_name", "COMBO")],
    outputs=[out("SAMPLER", "SAMPLER")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

sigmas = node(
    "ManualSigmas", [1660, 760], [420, 60],
    {"sigmas": NINE_STEP_SIGMAS}, outputs=[out("SIGMAS", "SIGMAS")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

seed = node(
    "Seed (rgthree)", [1660, 880], [320, 170],
    {"seed": -1, "🎲 Randomize Each Time": "", "🎲 New Fixed Random": "",
     "USE_LAST_SEED": ""},
    outputs=[{"name": "SEED", "type": "INT", "links": [], "shape": 3}],
    properties={"randomMax": 1125899906842624, "randomMin": 0, "cnr_id": "rgthree-comfy",
                "ver": "8ff50e4521881eca1fe26aec9615fc9362474931"})

noise = node(
    "RandomNoise", [2100, 880], [280, 80],
    {"noise_seed": 0, "control_after_generate": "randomize"},
    inputs=[sock("noise_seed", "INT")], outputs=[out("NOISE", "NOISE")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

sampler = node(
    "SamplerCustomAdvanced", [2100, 420], [240, 110],
    inputs=[sock("noise", "NOISE"), sock("guider", "GUIDER"),
            sock("sampler", "SAMPLER"), sock("sigmas", "SIGMAS"),
            sock("latent_image", "LATENT")],
    outputs=[out("output", "LATENT"), out("denoised_output", "LATENT")],
    properties={"cnr_id": "comfy-core", "ver": "0.16.3"})

vae_decode = node(
    "VAEDecode", [2500, 420], [240, 60],
    inputs=[sock("samples", "LATENT"), sock("vae", "VAE")],
    outputs=[out("IMAGE", "IMAGE")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

# ============ ③ 底图：上传支线 + 高清修复组（默认禁用） ============
load_img = node(
    "LoadImage", [520, 1200], [340, 560],
    {"image": "", "upload": "image"},
    outputs=[out("IMAGE", "IMAGE"), out("MASK", "MASK")],
    properties={"cnr_id": "comfy-core", "ver": "0.36.0"})

upscale = node(
    "CR Upscale Image", [940, 1320], [360, 200],
    {"upscale_model": "4x-UltraSharp.pth", "mode": "rescale", "rescale_factor": 2.0,
     "resize_width": 1920, "resampling_method": "lanczos", "supersample": "false",
     "rounding_modulus": 8},
    inputs=[sock("image", "IMAGE"), w_in("upscale_model", "COMBO")],
    outputs=[out("IMAGE", "IMAGE"), out("show_help", "STRING")])

resize_crop = node(
    "图像缩放V2_孤海", [1400, 1240], [340, 320],
    {"宽度": 1920, "高度": 1080, "缩放方法": "自定义宽高", "将边缩放到": 1024,
     "缩放插值": "Lanczos", "缩放模式": "裁剪", "固定方向": "居中",
     "执行条件": "总是", "填充颜色": "#364254", "整除数": 32},
    inputs=[sock("图像", "IMAGE"), w_in("宽度", "INT"), w_in("高度", "INT")],
    outputs=[out("图像", "IMAGE"), out("宽度", "INT"), out("高度", "INT"),
             out("遮罩", "MASK")])

src_switch = node(
    "easy imageSwitch", [2920, 700], [300, 80],
    {"boolean": False},
    inputs=[sock("image_a", "IMAGE"), sock("image_b", "IMAGE")],
    outputs=[out("IMAGE", "IMAGE")],
    title="底图来源（勾选=AI生成，不勾=上传图）")

# ============ ④ 文字组 ============
text_img = node(
    "LayerUtility: TextImage", [3360, 260], [340, 460],
    {"text": "主标题文字", "font_file": "Alibaba-PuHuiTi-Heavy.ttf",
     "spacing": 0, "leading": 8, "horizontal_border": 5, "vertical_border": 5,
     "scale": 35, "variation_range": 0, "variation_seed": 123,
     "layout": "horizontal", "width": 1920, "height": 1080,
     "text_color": "#FFFFFF", "background_color": "#000000"},
    inputs=[sock("size_as", "*")],
    outputs=[out("image", "IMAGE"), out("mask", "MASK")])

text_shadow = node(
    "LayerStyle: DropShadow V3", [3360, 800], [340, 220],
    {"invert_mask": True, "blend_mode": "normal", "opacity": 60,
     "distance_x": 6, "distance_y": 6, "grow": 4, "blur": 12,
     "shadow_color": "#000000"},
    inputs=[sock("layer_image", "IMAGE"), sock("background_image", "IMAGE")],
    outputs=[out("image", "IMAGE"), out("mask", "MASK")])

text_blend = node(
    "LayerUtility: ImageBlendAdvance", [3820, 420], [340, 340],
    {"invert_mask": False, "blend_mode": "normal", "opacity": 100,
     "x_percent": 50, "y_percent": 75, "mirror": "None", "scale": 1,
     "aspect_ratio": 1, "rotate": 0, "transform_method": "lanczos",
     "anti_aliasing": 0},
    inputs=[sock("background_image", "IMAGE"), sock("layer_image", "IMAGE"),
            sock("layer_mask", "MASK")],
    outputs=[out("image", "IMAGE"), out("mask", "MASK")])

# ============ ⑤ 水印组 ============
watermark = node(
    "孤海-图像添加水印", [4280, 420], [340, 420],
    {"水印文本": "@jacky", "字体": "font.ttf", "水印大小百分比": 5,
     "水印不透明度": 50, "水平位置": "靠左", "垂直位置": "靠上",
     "X偏移百分比": 2, "Y偏移百分比": 2, "文字颜色": "#FFFFFF",
     "水印平铺": False, "水印角度": 0, "水印间距": 10, "输出透明通道": False},
    inputs=[sock("图像", "IMAGE")], outputs=[out("IMAGE", "IMAGE")])

# ============ ⑥ 输出组 ============
comparer = node(
    "Image Comparer (rgthree)", [4740, 260], [420, 720],
    {"rgthree_comparer": {"images": []}},
    inputs=[{"dir": 3, "label": "图像_A(成品)", "name": "image_a", "type": "IMAGE", "link": None},
            {"dir": 3, "label": "图像_B(底图)", "name": "image_b", "type": "IMAGE", "link": None}],
    outputs=[{"dir": 4, "name": "images", "shape": 3, "type": "IMAGE", "links": []},
             {"dir": 4, "name": "images", "shape": 3, "type": "IMAGE", "links": []}],
    widgets_order=["rgthree_comparer"],
    properties={"cnr_id": "rgthree-comfy",
                "ver": "8ff50e4521881eca1fe26aec9615fc9362474931",
                "comparer_mode": "Slide"})

save = node(
    "SaveImage", [4740, 1080], [420, 720],
    {"filename_prefix": "cover_"},
    inputs=[{"label": "图像", "name": "images", "type": "IMAGE", "link": None}],
    outputs=[out("images", "IMAGE"), out("images", "IMAGE")],
    properties={"cnr_id": "comfy-core", "ver": "0.37.0"})

# ============ 使用说明 & 标题 & 组开关 ============
note = node(
    "MarkdownNote", [0, 40], [420, 320],
    {"text": (
        "## 使用说明\n"
        "1. **尺寸比例**：`GoohaiRatioAndResolution` 是全局唯一尺寸源。\n"
        "   - 公众号头条封面 2.35:1 → 比例选「自定义宽高」，自定宽 2350 × 高 1000\n"
        "   - 视频封面/帖子 16:9 → 比例「16:9」+ 固定长边 1920\n"
        "   - 部分平台 2:1 → 比例「2:1」\n"
        "2. **底图来源**：`easy imageSwitch` 勾选=AI生成（填生成提示词），"
        "不勾=上传网络图。\n"
        "3. **高清修复**：本组默认禁用，经 `Fast Groups Bypasser` 一键启用。"
        "首次使用需先把放大模型（如 4x-UltraSharp）放入 "
        "`models/upscale_models/`。\n"
        "4. **文字**：`TextImage` 填标题，位置在 `ImageBlendAdvance` 的 "
        "x/y_percent 调（50/75=中下）。遮罩已配好，只合成文字像素。\n"
        "5. **水印**：默认左上角；右下角 = 水平靠右 + 垂直靠下。"
        "Logo 图片水印接 `水印图像` 可选输入。\n"
        "6. **提示词增强**：PE 组默认关闭（False=直出），开启前确认已下载 "
        "pe_t2i 模型。")},
    widgets_order=["text"])

bypasser = node(
    "Fast Groups Bypasser (rgthree)", [940, 1080], [360, 60],
    inputs=[], outputs=[{"label": "可选连接", "name": "OPT_CONNECTION", "type": "*", "links": []}],
    properties={"matchTitle": "高清修复", "showNav": True, "showAllGraphs": True,
                "sort": "position", "toggleRestriction": "default"})

title_label = node(
    "Label (rgthree)", [0, -80], [1600, 100],
    title="▶社媒封面/配图生成器 (Qwen2.1-turbo-9步)",
    properties={"fontSize": 80, "fontFamily": "Arial", "fontColor": "#3CB371",
                "textAlign": "left", "backgroundColor": "transparent", "padding": 0,
                "borderRadius": 0, "angle": 0})
title_label["flags"] = {"allow_interaction": True}

# ============ 连线 ============
# PE 支线
L(gen_prompt, 0, pe_gen, 1, "STRING")          # 生成提示词 -> TextGenerate.prompt
L(pe_sys, 0, pe_gen, 5, "STRING")              # 系统提示词 -> TextGenerate.system_prompt
L(pe_clip, 0, pe_gen, 0, "CLIP")               # PE CLIP
L(gen_prompt, 0, pe_switch, 0, "STRING")       # 直出支路
L(pe_gen, 0, pe_switch, 1, "STRING")           # 增强支路
L(pe_switch, 0, pe_preview, 0, "*")            # 最终提示词预览
L(pe_preview, 0, tenc, 3, "STRING")            # -> TextEncode.prompt

# 生成支线
L(unet, 0, cache, 0, "MODEL")
L(cache, 0, cfg_guider, 0, "MODEL")
L(clip, 0, tenc, 0, "CLIP")
L(tenc, 0, cfg_guider, 1, "CONDITIONING")
L(tenc, 1, cfg_guider, 2, "CONDITIONING")
L(ratio, 1, empty_latent, 0, "INT")            # 宽度 -> EmptyLatent
L(ratio, 2, empty_latent, 1, "INT")            # 高度 -> EmptyLatent
L(empty_latent, 0, sampler, 4, "LATENT")
L(seed, 0, noise, 0, "INT")
L(noise, 0, sampler, 0, "NOISE")
L(cfg_guider, 0, sampler, 1, "GUIDER")
L(sampler_select, 0, sampler, 2, "SAMPLER")
L(sigmas, 0, sampler, 3, "SIGMAS")
L(sampler, 0, vae_decode, 0, "LATENT")
L(vae, 0, vae_decode, 1, "VAE")

# 上传支线：LoadImage -> [高清修复组: CR Upscale] -> 缩放裁剪
L(load_img, 0, upscale, 0, "IMAGE")
L(upscale, 0, resize_crop, 0, "IMAGE")
L(ratio, 1, resize_crop, 1, "INT")             # 宽度
L(ratio, 2, resize_crop, 2, "INT")             # 高度

# 底图来源开关
L(vae_decode, 0, src_switch, 0, "IMAGE")       # image_a = AI生成
L(resize_crop, 0, src_switch, 1, "IMAGE")      # image_b = 上传图

# 文字：文字层(size_as=底图) -> 投影 -> 合成(遮罩只保留文字像素)
L(src_switch, 0, text_img, 0, "*")             # size_as
L(text_img, 0, text_shadow, 0, "IMAGE")
L(src_switch, 0, text_shadow, 1, "IMAGE")
L(src_switch, 0, text_blend, 0, "IMAGE")
L(text_shadow, 0, text_blend, 1, "IMAGE")
L(text_img, 1, text_blend, 2, "MASK")

# 水印 -> 输出
L(text_blend, 0, watermark, 0, "IMAGE")
L(watermark, 0, comparer, 0, "IMAGE")
L(src_switch, 0, comparer, 1, "IMAGE")
L(watermark, 0, save, 0, "IMAGE")

# ============ 分组 ============
def bbox(ids, pad=40):
    xs, ys = [], []
    for i in ids:
        n = nodes[i - 1]
        xs += [n["pos"][0], n["pos"][0] + n["size"][0]]
        ys += [n["pos"][1], n["pos"][1] + n["size"][1]]
    return [min(xs) - pad, min(ys) - pad,
            max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad]

COLOR = "#3f789e"
groups = [
    {"title": "① 尺寸比例（唯一尺寸源）", "bounding": bbox([ratio["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "②-A 底图：AI生成（提示词增强可选）",
     "bounding": bbox([gen_prompt["id"], pe_clip["id"], pe_sys["id"], pe_gen["id"], pe_switch["id"], pe_preview["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "②-B 底图：模型与采样（9步固定配方）",
     "bounding": bbox([unet["id"], clip["id"], vae["id"], cache["id"], tenc["id"], empty_latent["id"], cfg_guider["id"], sampler_select["id"], sigmas["id"], seed["id"], noise["id"], sampler["id"], vae_decode["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "③ 底图：上传网络图",
     "bounding": bbox([load_img["id"], resize_crop["id"], bypasser["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "高清修复",  # Fast Groups Bypasser 按此标题匹配，勿改名
     "bounding": bbox([upscale["id"]]), "color": "#a13034", "font_size": 24, "locked": False},
    {"title": "④ 文字（x/y_percent 控位置）", "bounding": bbox([text_img["id"], text_shadow["id"], text_blend["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "⑤ 水印（左上/右下）", "bounding": bbox([watermark["id"]]), "color": COLOR, "font_size": 24, "locked": False},
    {"title": "⑥ 输出", "bounding": bbox([comparer["id"], save["id"]]), "color": COLOR, "font_size": 24, "locked": False},
]

# 执行顺序（拓扑近似，前端会重算）
for i, n in enumerate(nodes):
    n["order"] = i

workflow = {
    "id": str(uuid.uuid4()),
    "revision": 0,
    "last_node_id": len(nodes),
    "last_link_id": len(links),
    "nodes": nodes,
    "links": links,
    "groups": groups,
    "config": {},
    "extra": {"ds": {"scale": 0.45, "offset": [80, 900]}, "frontendVersion": "1.57.1"},
    "version": 0.4,
}

out_path = os.path.join(HERE, "社媒封面配图生成器.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(workflow, f, ensure_ascii=False, indent=1)
print(f"OK -> {out_path}")
print(f"nodes={len(nodes)} links={len(links)} groups={len(groups)}")
