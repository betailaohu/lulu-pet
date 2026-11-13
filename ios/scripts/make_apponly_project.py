#!/usr/bin/env python3
"""生成「只含主 App」的 XcodeGen spec，给免费 Apple ID 侧载用。

为什么需要：
  免费开发者账号只能给主 App 建 provisioning profile，包内嵌的 Widget Extension
  （PetWidget.appex）用的是另一个 bundle id，侧载工具重签时经常报
  "Application is missing the application-identifier entitlement" 而装不进去。
  更关键的是免费账号拿不到 App Groups，小组件本来就读不到主 App 的数据。
  所以默认出「纯主 App」包 —— 能装、能跑、主 App 功能完整，只是没有桌面小组件。

用法：
  python3 ios/scripts/make_apponly_project.py           # 生成 ios/project-apponly.yml
  cd ios && xcodegen generate --spec project-apponly.yml

有付费开发者账号时不要用这个脚本，直接用 project.yml（两个 target 全量）。
"""

import os
import sys

try:
    import yaml
except ImportError:
    sys.exit("[FAIL] 需要 PyYAML：python3 -m pip install pyyaml")

HERE = os.path.dirname(os.path.abspath(__file__))
IOS = os.path.dirname(HERE)
SRC = os.path.join(IOS, "project.yml")
DST = os.path.join(IOS, "project-apponly.yml")


def main():
    with open(SRC, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    targets = spec.get("targets", {})
    if "PetApp" not in targets:
        sys.exit("[FAIL] project.yml 里找不到 PetApp target")

    # 1. 去掉 Widget Extension target
    removed = targets.pop("PetWidget", None)
    if removed is None:
        print("[WARN] project.yml 里本来就没有 PetWidget，按纯主 App 处理")

    # 2. 去掉主 App 对 Widget 的依赖（不删的话 xcodegen 会报 target not found）
    app = targets["PetApp"]
    deps = app.get("dependencies")
    if deps:
        kept = [d for d in deps if d.get("target") != "PetWidget"]
        if kept:
            app["dependencies"] = kept
        else:
            app.pop("dependencies", None)

    # 3. scheme 只保留主 App（原来也只有它，稳妥起见再确认一次）
    schemes = spec.get("schemes", {})
    schemes.pop("PetWidget", None)

    with open(DST, "w", encoding="utf-8") as f:
        f.write("# 自动生成，不要手改。源文件是 project.yml，\n")
        f.write("# 生成命令：python3 ios/scripts/make_apponly_project.py\n")
        yaml.safe_dump(spec, f, allow_unicode=True, sort_keys=False)

    print("[OK] 写出 {}".format(os.path.relpath(DST, IOS)))
    print("[OK] targets: {}".format(", ".join(targets.keys())))
    print("[OK] PetApp dependencies: {}".format(app.get("dependencies", "无")))


if __name__ == "__main__":
    main()
