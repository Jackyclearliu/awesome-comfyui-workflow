#!/usr/bin/env python3
"""Dump official Anima workflow node configs for diagnosis."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OFFICIAL = os.path.join(ROOT, "custom_nodes", "Comfyui-Anima-Wardrobe-V6", "workflows",
                        "Anima-艺术构图_哑光人物_29B_16x9.json")

with open(OFFICIAL, encoding="utf-8") as f:
    wf = json.load(f)

for n in sorted(wf["nodes"], key=lambda x: x["id"]):
    print(f"== node {n['id']} [{n['type']}] title={n.get('title')!r} mode={n.get('mode', 0)}")
    ins = [(i['name'], i['type'], i.get('link'), (i.get('widget') or {}).get('name')) for i in n.get('inputs', [])]
    outs = [(o['name'], o['type']) for o in n.get('outputs', [])]
    if ins:
        print("   in :", ins)
    if outs:
        print("   out:", outs)
    wv = n.get('widgets_values')
    if wv is not None:
        s = repr(wv)
        print("   widgets:", s[:400] + ("..." if len(s) > 400 else ""))
    wn = n.get('widgets_values_named')
    if wn:
        print("   named  :", repr(wn)[:400])
print("\n== links")
for l in wf["links"]:
    print("  ", l)
