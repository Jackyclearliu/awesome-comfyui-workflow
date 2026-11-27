#!/usr/bin/env python3
"""按 v2 方案从官方基线版生成本地化工作流（风格还原优先）。

来源: custom_nodes/Comfyui-Anima-Wardrobe-V6/workflows/Anima-艺术构图_哑光人物_29B_16x9.json
产物: workflow/workflow_json/自建工作流/Anima-艺术构图_提示词模板工作流.json

v2 变更（相对 v1）:
- 恢复官方节点 7 Prompt (LoraManager) / 19 Lora Loader (LoraManager)，配方照抄官方
- 采样器用原生 KSampler + 官方参数 er_sde/beta（本机核心已原生注册 er_sde）
- 种子恢复官方 fixed 值（主采 265521198872240 / 二采 ...241）
- 删除 v1 的 Power Lora Loader / 静态触发词 / 拼接 / 共享种子替代链
"""
import json
import copy
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "custom_nodes",
                    "Comfyui-Anima-Wardrobe-V6", "workflows", "Anima-艺术构图_哑光人物_29B_16x9.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "Anima-艺术构图_提示词模板工作流.json")

with open(BASE, encoding="utf-8") as f:
    wf = json.load(f)

by_id = {n["id"]: n for n in wf["nodes"]}


def keep(nid):
    return copy.deepcopy(by_id[nid])


def set_widget(node, pos, named):
    node["widgets_values"] = pos
    node["widgets_values_named"] = named


# ---- 原样保留的官方节点 ----------------------------------------------------
n_unet = keep(1)      # UNETLoader anima29B
n_clip = keep(2)      # CLIPLoader qwen_3_06b_base
n_vae = keep(3)       # VAELoader —— 本机文件在 models/vae 根目录，去掉 Qwen\ 子目录
set_widget(n_vae, ["qwen_image_vae.safetensors"], {"vae_name": "qwen_image_vae.safetensors"})
n_anima = keep(6)     # AnimaV6RandomPrompt（巨型面板状态原样保留）
n_prompt = keep(7)    # Prompt (LoraManager) —— 触发词动态前置 + 正向编码
n_neg = keep(8)       # 负向 CLIPTextEncode（官方 position 值即 317 字长版）
n_neg["widgets_values_named"] = {"text": n_neg["widgets_values"][0]}  # 官方 named 残留，归一化
n_latent = keep(10)   # EmptyLatentImage —— 改裸控件，面板画幅联动可写
n_latent["inputs"] = []
set_widget(n_latent, [1536, 864, 1], {"width": 1536, "height": 864, "batch_size": 1})
n_save = keep(13)     # SaveImage —— 官方 position 前缀
n_save["widgets_values_named"] = {"filename_prefix": n_save["widgets_values"][0]}
n_scale = keep(14)    # ImageScaleBy lanczos 1.5
n_enc = keep(15)      # VAEEncodeTiled 512/64
n_switch = keep(18)   # LazySwitchKJ 默认 true = 二采输出
n_lora = keep(19)     # Lora Loader (LoraManager) —— 六行配方照抄官方


# ---- XB 三件套的原生替代 ---------------------------------------------------
def node(nid, typ, title, pos, size, inputs, outputs, widgets=None, named=None, props=None):
    n = {
        "id": nid, "type": typ, "pos": pos, "size": size, "flags": {}, "order": 0, "mode": 0,
        "inputs": inputs, "outputs": outputs, "title": title,
        "properties": props or {"cnr_id": "comfy-core", "Node name for S&R": typ},
    }
    if widgets is not None:
        n["widgets_values"] = widgets
    if named is not None:
        n["widgets_values_named"] = named
    return n


def inp(name, typ, link=None, widget=None):
    d = {"name": name, "type": typ}
    if widget:
        d["widget"] = {"name": widget}
    if link is not None:
        d["link"] = link
    return d


def outp(name, typ, links=None):
    return {"name": name, "type": typ, "links": links}


def ks_in():
    return [inp("model", "MODEL"), inp("positive", "CONDITIONING"), inp("negative", "CONDITIONING"),
            inp("latent_image", "LATENT")]


def ks_out():
    return [outp("LATENT", "LATENT")]


KS_NAMED = ["seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "denoise"]

n_ks1 = node(
    11, "KSampler", "主采样 · 16 步 / CFG 2.0 / er_sde / beta（官方参数照搬）",
    [1480, 140], [340, 590], ks_in(), ks_out(),
    widgets=[265521198872240, "fixed", 16, 2.0, "er_sde", "beta", 1],
    named=dict(zip(KS_NAMED, [265521198872240, "fixed", 16, 2.0, "er_sde", "beta", 1])),
)
n_ks1["color"], n_ks1["bgcolor"] = "#323", "#535"

n_dec1 = node(
    12, "VAEDecodeTiled", "主图分块解码 · 320/32",
    [1900, 160], [340, 220],
    [inp("samples", "LATENT"), inp("vae", "VAE")],
    [outp("IMAGE", "IMAGE")],
    widgets=[320, 32, 64, 8],
    named={"tile_size": 320, "overlap": 32, "temporal_size": 64, "temporal_overlap": 8},
)

n_ks2 = node(
    16, "KSampler", "二采 · 6 步 / denoise 0.20（像素域，官方种子+1）",
    [2640, 940], [340, 590], ks_in(), ks_out(),
    widgets=[265521198872241, "fixed", 6, 2.0, "er_sde", "beta", 0.2],
    named=dict(zip(KS_NAMED, [265521198872241, "fixed", 6, 2.0, "er_sde", "beta", 0.2])),
)
n_ks2["color"], n_ks2["bgcolor"] = "#323", "#535"

n_dec2 = node(
    17, "VAEDecodeTiled", "二采分块解码 · 320/32",
    [3060, 960], [340, 220],
    [inp("samples", "LATENT"), inp("vae", "VAE")],
    [outp("IMAGE", "IMAGE")],
    widgets=[320, 32, 64, 8],
    named={"tile_size": 320, "overlap": 32, "temporal_size": 64, "temporal_overlap": 8},
)

n_label = node(
    29, "Label (rgthree)", "▶Anima29B-16步-艺术构图哑光 · 提示词模板工作流 v2",
    [0, -160], [1300, 64], [], [],
    widgets=["▶Anima29B-16步-艺术构图哑光 · 提示词模板工作流 v2"],
    props={"fontSize": 64, "fontFamily": "Arial", "fontColor": "#3CB371", "textAlign": "left",
           "backgroundColor": "transparent", "padding": 0, "borderRadius": 0, "angle": 0,
           "Node name for S&R": "Label (rgthree)"},
)
n_label["flags"] = {"allow_interaction": True}
n_label["color"], n_label["bgcolor"] = "#fff0", "#fff0"

nodes = [n_label, n_anima, n_prompt, n_neg, n_unet, n_clip, n_vae, n_lora,
         n_latent, n_ks1, n_dec1, n_scale, n_enc, n_ks2, n_dec2, n_switch, n_save]

# ---- 连线 ----------------------------------------------------------------
# 官方保留节点深拷贝时带旧连线登记，必须全部清空后再接线
for n in nodes:
    for i in n["inputs"]:
        i.pop("link", None)
    for o in n["outputs"]:
        o["links"] = None

LINKS = [  # (src_id, src_slot, dst_id, dst_slot, type)
    (6, 0, 7, 3, "STRING"),           # Anima.text -> Prompt.text（widget 转输入）
    (19, 1, 7, 0, "CLIP"),            # lora CLIP -> Prompt.clip
    (19, 1, 8, 0, "CLIP"),            # lora CLIP -> 负向编码
    (19, 2, 7, 2, "STRING"),          # lora trigger_words -> Prompt.trigger_words1
    (1, 0, 19, 0, "MODEL"),           # unet -> lora
    (2, 0, 19, 3, "CLIP"),            # cliploader -> lora
    (19, 0, 11, 0, "MODEL"),          # lora MODEL -> 主采（官方经 SageAttention，直连）
    (19, 0, 16, 0, "MODEL"),          # lora MODEL -> 二采
    (7, 0, 11, 1, "CONDITIONING"),    # 正向 -> 主采
    (8, 0, 11, 2, "CONDITIONING"),    # 负向 -> 主采
    (10, 0, 11, 3, "LATENT"),         # 空 latent -> 主采
    (11, 0, 12, 0, "LATENT"),         # 主采 -> 解码1
    (3, 0, 12, 1, "VAE"),             # vae -> 解码1
    (12, 0, 14, 0, "IMAGE"),          # 解码1 -> 放大（二采支路）
    (12, 0, 18, 1, "IMAGE"),          # 解码1 -> switch.on_false（首采原图）
    (14, 0, 15, 0, "IMAGE"),          # 放大 -> 编码
    (3, 0, 15, 1, "VAE"),             # vae -> 编码
    (15, 0, 16, 3, "LATENT"),         # 编码 -> 二采
    (7, 0, 16, 1, "CONDITIONING"),    # 正向 -> 二采
    (8, 0, 16, 2, "CONDITIONING"),    # 负向 -> 二采
    (16, 0, 17, 0, "LATENT"),         # 二采 -> 解码2
    (3, 0, 17, 1, "VAE"),             # vae -> 解码2
    (17, 0, 18, 2, "IMAGE"),          # 解码2 -> switch.on_true
    (18, 0, 13, 0, "*"),              # switch -> save
]

links, id2node = [], {n["id"]: n for n in nodes}
for i, (s, ss, d, ds, t) in enumerate(LINKS, start=1):
    links.append([i, s, ss, d, ds, t])
    so = id2node[s]["outputs"][ss]
    so["links"] = (so["links"] or []) + [i]
    id2node[d]["inputs"][ds]["link"] = i

# ---- 分组与元数据 --------------------------------------------------------
GROUPS = [
    ("① Anima 出题与 LoraManager 正向", -128, 1100, 1560, 1120, "#3f789e"),
    ("② 模型与 LoRA 配方（LoraManager）", -128, -60, 1020, 1160, "#8A8A8A"),
    ("③ 画幅", 900, 1100, 1040, 500, "#3f789e"),
    ("④ 主采样与解码", 1440, -60, 840, 500, "#3f789e"),
    ("⑤ 二采 · LazySwitch（默认开）", 1860, 860, 1580, 760, "#A1309C"),
    ("⑥ 保存", 3480, 1180, 560, 300, "#3f789e"),
]

for i, n in enumerate(nodes):
    n["order"] = i

out = {
    "id": "e28c56f1-0000-4000-8000-anima29btplv2",
    "revision": 0,
    "last_node_id": max(id2node),
    "last_link_id": len(links),
    "nodes": nodes,
    "links": links,
    "groups": [{"id": i + 1, "title": t, "bounding": [x, y, w, h], "color": c, "flags": {}}
               for i, (t, x, y, w, h, c) in enumerate(GROUPS)],
    "config": {},
    "extra": {"frontendVersion": "1.57.1"},
    "version": 0.4,
    "seed_widgets": {"6": 1, "11": 0, "16": 0},
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"written: {os.path.normpath(OUT)}  nodes={len(nodes)}  links={len(links)}")
