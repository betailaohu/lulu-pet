"""项目自检：配置一致性、素材覆盖、Kotlin 引用完整性（无需编译环境）。

用法：python .research/verify_project.py
"""
import glob
import json
import os
import re
import struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "shared")
ASSETS = os.path.join(ROOT, "android", "app", "src", "main", "assets")
LULU = os.path.join(ROOT, "assets", "lulu")
JAVA = os.path.join(ROOT, "android", "app", "src", "main", "java")

ok, bad = [], []


def check(cond, label):
    (ok if cond else bad).append(label)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def raw(path):
    with open(path, "rb") as fh:
        return fh.read()


def frame_ids(folder):
    return sorted(
        n[len("frame-"):-4]
        for n in os.listdir(folder)
        if n.startswith("frame-") and n.endswith(".png")
    )


# 1. 共享配置合法且副本一致
for cfg in ("manifest.json", "state.json"):
    s, a = os.path.join(SHARED, cfg), os.path.join(ASSETS, cfg)
    check(os.path.isfile(s) and os.path.isfile(a), "{} 存在".format(cfg))
    if os.path.isfile(s) and os.path.isfile(a):
        json.loads(read(s))
        json.loads(read(a))
        check(raw(s) == raw(a), "{} 副本与 shared 字节一致".format(cfg))

# 2. 素材覆盖：manifest / 素材包 / Android assets 三方一致
m = json.loads(read(os.path.join(SHARED, "manifest.json")))
expected = sorted(m["frameFiles"])
check(len(expected) == 36, "manifest frameFiles = 36")
check(frame_ids(LULU) == expected, "assets/lulu 帧集合与 manifest 一致")
check(frame_ids(os.path.join(ASSETS, "frames")) == expected, "Android assets 帧集合与 manifest 一致")
check(os.path.isfile(os.path.join(LULU, "character.png")), "character.png 存在")
check(os.path.isfile(os.path.join(ASSETS, "character.png")), "Android character.png 存在")

# 2b. PNG 规格：512x512、RGBA（color type 6），不依赖 Pillow
def png_header(path):
    with open(path, "rb") as fh:
        head = fh.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h, head[25]


for folder, label in (
    (LULU, "assets/lulu"),
    (os.path.join(ASSETS, "frames"), "Android"),
    (os.path.join(ROOT, "ios", "Resources", "Frames"), "iOS"),
):
    bad_spec = []
    for fid in expected:
        path = os.path.join(folder, "frame-{}.png".format(fid))
        info = png_header(path) if os.path.isfile(path) else None
        if info != (512, 512, 6):
            bad_spec.append(fid)
    check(not bad_spec, "{} 36 张均为 512x512 RGBA（异常: {}）".format(
        label, ",".join(bad_spec[:5]) or "无"
    ))
check(os.path.isfile(os.path.join(LULU, "asset_provenance.json")), "素材来源记录存在")

# 3. 绘制清单与 manifest 一致
brief = json.loads(read(os.path.join(LULU, "drawing_brief.json")))
bids = sorted(f["id"] for f in brief["frames"])
check(len(bids) == len(set(bids)) == 36, "drawing_brief 36 帧无重复")
check(bids == expected, "drawing_brief 帧集合与 manifest 一致")
check(os.path.isfile(os.path.join(LULU, "绘制清单.md")), "绘制清单.md 已生成")

# 4. Kotlin 包路径与目录一致、无上游包名残留
kt_files = sorted(glob.glob(os.path.join(JAVA, "**", "*.kt"), recursive=True))
check(len(kt_files) >= 14, "Kotlin 文件数 >= 14（含新增 2 个）")
for p in kt_files:
    src = read(p)
    rel = os.path.relpath(os.path.dirname(p), JAVA).replace("\\", "/")
    expected_pkg = rel.replace("/", ".")
    m_pkg = re.search(r"^package\s+([\w.]+)", src, re.M)
    check(bool(m_pkg) and m_pkg.group(1) == expected_pkg,
          "package 与目录一致: {}".format(os.path.basename(p)))
    check("com.deepfish" not in src, "无上游包名残留: {}".format(os.path.basename(p)))

# 5. 关键初始化与调用点
svc = read(os.path.join(JAVA, "com", "lulu", "pet", "PetService.kt"))
check("PetManifest.init(this)" in svc, "PetService 初始化 PetManifest")
check("PetState.init(this)" in svc, "PetService 初始化 PetState")

pv = read(os.path.join(JAVA, "com", "lulu", "pet", "PetView.kt"))
for call in ("PetManifest.get(", "PetManifest.getPlan(", "PetManifest.frameName(",
             "PetManifest.poseScale(", "PetManifest.multiFrameAction(",
             "PetManifest.restingFrame(", "PetState.onPat()", "PetState.onFeed()",
             "PetState.urgentBehavior()"):
    check(call in pv, "PetView 调用点: {}".format(call.rstrip("(")))
for leftover in ("Behaviors.get(", "Behaviors.getPlan(", "poseVisualScale(",
                 "clickLines.random"):
    check(leftover not in pv, "无残留: {}".format(leftover))
remaining = set(re.findall(r"Behaviors\.(\w+)", pv))
check(remaining <= {"formatLine", "stripHints"},
      "Behaviors 仅保留文本处理（实际: {}）".format(",".join(sorted(remaining)) or "无"))

# 6. PetManifest / PetState 接口完整
pm = read(os.path.join(JAVA, "com", "lulu", "pet", "model", "PetManifest.kt"))
for fn in ("fun init(", "fun get(", "fun getPlan(", "fun frameName(", "fun poseScale(",
           "fun multiFrameAction(", "fun restingFrame(", "fun hasFrame("):
    check(fn in pm, "PetManifest 接口: {}".format(fn.rstrip("(")))
ps = read(os.path.join(JAVA, "com", "lulu", "pet", "PetState.kt"))
for fn in ("fun init(", "fun onPat(", "fun onFeed(", "fun urgentBehavior(",
           "fun statusText(", "fun snapshot("):
    check(fn in ps, "PetState 接口: {}".format(fn.rstrip("(")))

# 7. 协议与上游档案
check(os.path.isfile(os.path.join(ROOT, "android", "LICENSE")), "MIT LICENSE 保留")
check(os.path.isfile(os.path.join(ROOT, "android", "ORIGIN.md")), "ORIGIN.md 存在")

# 8. iOS 工程骨架
ios = os.path.join(ROOT, "ios")
ios_files = (
    "project.yml", "README.md", "打包与安装指南.md",
    "Shared/AppGroup.swift", "Shared/PetManifest.swift",
    "PetApp/App/LuluApp.swift", "PetApp/Views/PetView.swift", "PetApp/Views/SettingsView.swift",
    "PetApp/State/PetState.swift", "PetApp/Info.plist", "PetApp/PetApp.entitlements",
    "PetWidget/LuluWidget.swift", "PetWidget/Info.plist", "PetWidget/PetWidget.entitlements",
    "PetLiveActivity/PetLiveActivity.swift",
    "Resources/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png",
    "Resources/Assets.xcassets/AppIcon.appiconset/Contents.json",
)
for f in ios_files:
    check(os.path.isfile(os.path.join(ios, f)), "iOS 文件: {}".format(f))
swift_files = sorted(glob.glob(os.path.join(ios, "**", "*.swift"), recursive=True))
check(len(swift_files) >= 7, "Swift 文件数 >= 7（实际 {}）".format(len(swift_files)))
for p in swift_files:
    src = read(p)
    check(src.count("{") == src.count("}"),
          "Swift 括号平衡: {}".format(os.path.basename(p)))
proj = read(os.path.join(ios, "project.yml"))
check("PetWidget" in proj and "PetApp" in proj, "project.yml 含两个 target")
check('SWIFT_VERSION: "5.0"' in proj,
      "SWIFT_VERSION 是合法语言版本值（写 5.9 会让 swiftc 报 invalid value）")
check("iOS: \"17.0\"" in proj, "部署目标 iOS 17.0")
check("schemes:" in proj and "PetApp:" in proj, "project.yml 显式声明 scheme")
check("containerBackground" in read(os.path.join(ios, "PetWidget", "LuluWidget.swift")),
      "小组件用 containerBackground（iOS 17 起必需）")
check("import Combine" in read(os.path.join(ios, "PetApp", "State", "PetState.swift")),
      "PetState 显式导入 Combine（ObservableObject 来源）")
check("group.com.lulu.pet" in read(os.path.join(ios, "PetApp", "PetApp.entitlements")),
      "App Group entitlement(主 App)")
check("group.com.lulu.pet" in read(os.path.join(ios, "PetWidget", "PetWidget.entitlements")),
      "App Group entitlement(Widget)")

ios_frames = os.path.join(ios, "Resources", "Frames")
check(os.path.isdir(ios_frames) and frame_ids(ios_frames) == expected,
      "iOS Resources 帧集合与 manifest 一致")
for cfg in ("manifest.json", "state.json"):
    check(raw(os.path.join(SHARED, cfg)) == raw(os.path.join(ios, "Resources", cfg)),
          "iOS {} 与 shared 字节一致".format(cfg))

# 9. 编译通道与素材替换通道
check(os.path.isfile(os.path.join(ROOT, ".github", "workflows", "android-build.yml")),
      "Android CI 工作流存在")
check(os.path.isfile(os.path.join(ROOT, ".github", "workflows", "ios-build.yml")),
      "iOS CI 工作流存在（macOS runner 出未签名 ipa）")
check("Payload" in read(os.path.join(ROOT, ".github", "workflows", "ios-build.yml")),
      "iOS CI 会打成 Payload/*.ipa")
check(os.path.isfile(os.path.join(ROOT, "android", "编译验证指南.md")),
      "编译验证指南存在")
check(os.path.isfile(os.path.join(LULU, "install_assets.py")), "install_assets.py 存在")
check(os.path.isfile(os.path.join(LULU, "绘制清单.md")), "绘制清单.md 存在")
check(os.path.isfile(os.path.join(LULU, "render_brief.py")), "render_brief.py 存在")

is_placeholder = os.path.isfile(os.path.join(LULU, ".placeholder"))

for line in ok:
    print("[OK]", line)
for line in bad:
    print("[FAIL]", line)
print("[INFO] 素材状态: {}".format(
    "仍是占位立绘（用 install_assets.py 安装正式素材）" if is_placeholder else "已安装正式立绘"
))
print("\n=== {} passed, {} failed ===".format(len(ok), len(bad)))
