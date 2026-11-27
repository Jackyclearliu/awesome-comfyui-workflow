#!/usr/bin/env python3
"""静态校验 Anima-艺术构图_提示词模板工作流.json（v2 风格还原版）。

检查项：
1. 连线完整性：端点存在、插槽不越界、输出/输入双向登记、类型匹配（* 通配）
2. 每个 input.link 能在 links 表反查；无悬空 link id
3. 禁用类型扫描（XB_* / Power Lora Loader 残留）
4. widgets_values 与 widgets_values_named 一致性（跳过 LoraManager DOM 节点 7/19）
5. 模型文件存在性
6. LoRA 六行配方 = 官方基线（turbo on 0.85 / light-concepts on 0.3 / 其余 off，gouache 0.9）
7. KSampler 参数 = 官方值（fixed 种子 / er_sde / beta / 16·2.0·1 与 6·2.0·0.2），er_sde 须在核心 KSAMPLER_NAMES 中
8. 触发词链 19->7、Anima 正文 6->7 恢复
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
WF = os.path.join(HERE, "..", "Anima-艺术构图_提示词模板工作流.json")
K2 = os.path.join(HERE, "..", "Krea2-艺术构图-提示词模板工作流.json")
OFFICIAL = os.path.join(ROOT, "custom_nodes", "Comfyui-Anima-Wardrobe-V6", "workflows",
                        "Anima-艺术构图_哑光人物_29B_16x9.json")

errors, warns = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warns.append(msg)


with open(WF, encoding="utf-8") as f:
    wf = json.load(f)

nodes = wf["nodes"]
links = wf["links"]
id2node = {n["id"]: n for n in nodes}

assert wf["last_node_id"] == max(id2node), "last_node_id 与实际节点不符"
assert wf["last_link_id"] == len(links), "last_link_id 与 links 表不符"
if len(id2node) != len(nodes):
    err("存在重复节点 id")
print(f"[meta] nodes={len(nodes)} links={len(links)} groups={len(wf['groups'])} "
      f"seed_widgets={wf.get('seed_widgets')}")

# 1+2. 连线完整性
for lid, sid, sslot, did, dslot, ltype in links:
    if sid not in id2node:
        err(f"link {lid}: 源节点 {sid} 不存在"); continue
    if did not in id2node:
        err(f"link {lid}: 目标节点 {did} 不存在"); continue
    src, dst = id2node[sid], id2node[did]
    if sslot >= len(src["outputs"]):
        err(f"link {lid}: 源插槽 {sid}[{sslot}] 越界"); continue
    if dslot >= len(dst["inputs"]):
        err(f"link {lid}: 目标插槽 {did}[{dslot}] 越界"); continue
    so, di = src["outputs"][sslot], dst["inputs"][dslot]
    if lid not in (so.get("links") or []):
        err(f"link {lid}: 源输出 {sid}[{sslot}] 未登记该 link")
    if di.get("link") != lid:
        err(f"link {lid}: 目标输入 {did}[{dslot}].link={di.get('link')} 不符")
    st, dt = so["type"], di["type"]
    if st != dt and "*" not in (st, dt):
        # 逗号复合类型取交集（如 STRING ⊂ AUTOCOMPLETE_TEXT_PROMPT,STRING）
        if not (set(st.split(",")) & set(dt.split(","))):
            err(f"link {lid}: 类型不匹配 {sid}:{st} -> {did}:{dt}")

for n in nodes:
    for i, di in enumerate(n["inputs"]):
        lk = di.get("link")
        if lk is not None:
            rec = next((l for l in links if l[0] == lk), None)
            if rec is None:
                err(f"节点 {n['id']}[{i}].link={lk} 不在 links 表")
            elif rec[3] != n["id"] or rec[4] != i:
                err(f"节点 {n['id']}[{i}].link={lk} 反向登记为 {rec[3]}[{rec[4]}]")
for n in nodes:
    for o, so in enumerate(n["outputs"]):
        for lk in (so.get("links") or []):
            rec = next((l for l in links if l[0] == lk), None)
            if rec is None:
                err(f"节点 {n['id']} 输出[{o}] 登记了不存在的 link {lk}")
            elif rec[1] != n["id"] or rec[2] != o:
                err(f"节点 {n['id']} 输出[{o}] link {lk} 反向登记为 {rec[1]}[{rec[2]}]")

# 3. 禁用类型扫描
for n in nodes:
    t = n["type"]
    if t.startswith("XB_") or "Power Lora Loader" in t:
        err(f"应剔除的节点类型残留: {n['id']} {t}")
    if n.get("mode", 0) != 0:
        warn(f"节点 {n['id']} mode={n['mode']}（非激活状态）")

# 4. widgets 一致性（LoraManager DOM 节点 7/19 的 widgets_values 是复合结构，跳过长度比对）
WIDGET_ORDER = {
    8: ["text"], 10: ["width", "height", "batch_size"], 13: ["filename_prefix"],
    11: ["seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
    16: ["seed", "control_after_generate", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
}
SKIP_LEN_CHECK = {7, 19}
for n in nodes:
    if "widgets_values_named" not in n or n["id"] in SKIP_LEN_CHECK:
        continue
    nid = n["id"]
    if nid in WIDGET_ORDER and list(n["widgets_values_named"].keys()) != WIDGET_ORDER[nid]:
        err(f"节点 {nid} named 键序 {list(n['widgets_values_named'].keys())} != 期望 {WIDGET_ORDER[nid]}")
    vals, named = n["widgets_values"], n["widgets_values_named"]
    if len(vals) != len(named):
        err(f"节点 {nid} widgets_values({len(vals)}) 与 named({len(named)}) 长度不符")
    else:
        for k, v in zip(named.keys(), vals):
            if named[k] != v:
                err(f"节点 {nid} widget '{k}' 值不符: {named[k]!r} vs {v!r}")

# 5. 模型文件存在性（LoRA 支持 models/loras 任意深度子目录）
def exists(rel):
    return os.path.isfile(os.path.join(ROOT, rel))


def find_file(rel_dir, basename):
    base = os.path.join(ROOT, rel_dir)
    for dirpath, _, files in os.walk(base):
        if basename in files:
            return True
    return False

MODELS = [
    "models/diffusion_models/Anima/anima29B_v10_bf16.safetensors",
    "models/text_encoders/Anima/qwen_3_06b_base.safetensors",
    "models/vae/qwen_image_vae.safetensors",
]
for rel in MODELS:
    if not exists(rel):
        err(f"模型缺失: {rel}")

# 6. LoRA 配方 = 官方基线（节点 19 与官方逐行比对 active/strength）
with open(OFFICIAL, encoding="utf-8") as f:
    off = json.load(f)
off19 = next(n for n in off["nodes"] if n["id"] == 19)
off_rows = off19["widgets_values"][2]
my19 = id2node.get(19)
if my19 is None or my19["type"] != "Lora Loader (LoraManager)":
    err("节点 19 不是 Lora Loader (LoraManager)")
else:
    my_rows = my19["widgets_values"][2]
    if len(my_rows) != len(off_rows):
        err(f"LoRA 行数 {len(my_rows)} != 官方 {len(off_rows)}")
    for i, (mr, orow) in enumerate(zip(my_rows, off_rows)):
        for key in ("name", "strength", "active", "clipStrength"):
            if mr.get(key) != orow.get(key):
                err(f"LoRA 行 {i} ({orow.get('name')}): {key} = {mr.get(key)!r} != 官方 {orow.get(key)!r}")
        lora_base = str(mr["name"]).replace("\\", "/").split("/")[-1] + ".safetensors"
        if mr["active"] and not find_file("models/loras", lora_base):
            err(f"激活的 LoRA 文件缺失: {lora_base}")
        if not mr["active"] and find_file("models/loras", lora_base):
            warn(f"LoRA {mr['name']} 文件已就位但官方配方中关闭（保持官方默认）")

# 7. KSampler 官方参数 + er_sde 注册
def check(nid, expect):
    n = id2node.get(nid)
    if n is None:
        err(f"节点 {nid} 不存在"); return
    if n["type"] != "KSampler":
        err(f"节点 {nid} 类型 {n['type']} != KSampler"); return
    for k, v in expect.items():
        if n["widgets_values_named"].get(k) != v:
            err(f"节点 {nid} '{k}' = {n['widgets_values_named'].get(k)!r} != {v!r}")

check(11, {"seed": 265521198872240, "control_after_generate": "fixed", "steps": 16,
           "cfg": 2.0, "sampler_name": "er_sde", "scheduler": "beta", "denoise": 1})
check(16, {"seed": 265521198872241, "control_after_generate": "fixed", "steps": 6,
           "cfg": 2.0, "sampler_name": "er_sde", "scheduler": "beta", "denoise": 0.2})

with open(os.path.join(ROOT, "comfy", "samplers.py"), encoding="utf-8") as f:
    samplers_src = f.read()
m = re.search(r"KSAMPLER_NAMES\s*=\s*\[(.*?)\]", samplers_src, re.S)
names = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
for s in ("er_sde", "euler"):
    if s not in names:
        err(f"核心 KSAMPLER_NAMES 未注册 {s}")
print(f"[core] KSAMPLER_NAMES 含 er_sde: {'er_sde' in names}")

# 8. 触发词链与正向链
def has_link(sid, did, dslot):
    return any(l[1] == sid and l[3] == did and l[4] == dslot for l in links)

if not has_link(19, 7, 2):
    err("触发词链 19.trigger_words -> 7.trigger_words1 缺失")
if not has_link(6, 7, 3):
    err("Anima 正文 6.text -> 7.text 缺失")
if not has_link(19, 7, 0) or not has_link(19, 8, 0):
    err("lora CLIP -> Prompt/负向 编码链路缺失")
n7 = id2node.get(7)
if n7 and n7["type"] != "Prompt (LoraManager)":
    err(f"节点 7 类型 {n7['type']} != Prompt (LoraManager)")
if n7 and n7["inputs"][1].get("link") is not None:
    warn("节点 7 seed 输入被连接（官方未连接）")

# 负向词长版
neg = id2node[8]["widgets_values_named"]["text"]
if len(neg) < 300 or "glossy skin" not in neg:
    err(f"负向词异常: 长度 {len(neg)}")

# LazySwitch 默认 true
sw = id2node[18]
if 1 not in (sw.get("widgets_values") or []) and sw.get("widgets_values") != [True]:
    err(f"LazySwitch 默认值异常（期望 true）: {sw.get('widgets_values')}")

# 对照 K2 已验收成品的 KSampler named 键序
if os.path.isfile(K2):
    with open(K2, encoding="utf-8") as f:
        k2 = json.load(f)
    k2_ks = next(n for n in k2["nodes"] if n["type"] == "KSampler")
    for nid in (11, 16):
        mine = list(id2node[nid]["widgets_values_named"].keys())
        ref = list(k2_ks["widgets_values_named"].keys())
        if mine != ref:
            err(f"节点 {nid} KSampler named 键序 {mine} != K2 成品 {ref}")
else:
    warn("K2 成品不存在，跳过对照")

print()
for w in warns:
    print(f"[WARN] {w}")
for e in errors:
    print(f"[ERROR] {e}")
print()
print("RESULT:", "PASS ✓" if not errors else f"FAIL ✗ ({len(errors)} errors, {len(warns)} warns)")
sys.exit(1 if errors else 0)
