# 在 Mac 上编译（不依赖 GitHub）

这个包里的东西是完整的：8 个 Swift 文件、XcodeGen 配置、Info.plist、entitlements、36 张立绘、两份 JSON 配置、App 图标。
**全程不需要 GitHub、不需要联网下载代码**，只要一台装了 Xcode 的 Mac。

## 一、准备（一次性）

1. **装 Xcode**：App Store 搜「Xcode」→ 安装（约 15 GB，装完打开一次，同意协议，等它装完组件）
2. **装 XcodeGen**（把 `project.yml` 变成 `.xcodeproj` 的小工具）：

```bash
# 有 Homebrew 的话
brew install xcodegen

# 没有 Homebrew，国内网络建议直接用清华镜像装 Homebrew 再装：
export HOMEBREW_BREW_GIT_REMOTE=https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git
export HOMEBREW_CORE_GIT_REMOTE=https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git
/bin/bash -c "$(curl -fsSL https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/install/raw/master/install.sh)"
brew install xcodegen
```

## 二、生成工程并打开

```bash
cd <解压后的目录>/lulu-ios
xcodegen generate            # 生成 LuluPet.xcodeproj
open LuluPet.xcodeproj       # 用 Xcode 打开
```

## 三、签名并装到 iPhone

1. Xcode 左侧点项目 → **TARGETS 选 `PetApp`** → **Signing & Capabilities**
2. 勾上 **Automatically manage signing**
3. **Team** 选你自己的 Apple ID（没有就点 `Add an Account` 登录，免费账号即可，会显示为 "Personal Team"）
4. 如果 bundle id `com.lulu.pet.app` 被占用，改成 `com.你的名字.lulupet`（改完 Xcode 会自动重建描述文件）
5. iPhone 用数据线连上 Mac，顶部设备选择器选你的 iPhone → 点 ▶️ Run
6. 首次运行手机去 **设置 → 通用 → VPN 与设备管理** 信任一下开发者证书
7. iOS 26 首次装还会要求开 **开发者模式**：设置 → 隐私与安全性 → 开发者模式 → 打开 → 重启

## 四、想连桌面小组件一起装

默认的 `project.yml` 就是**两个 target 全量版**（主 App + 小组件 + 灵动岛），Xcode 里选 scheme `PetApp` 直接 Run 就会把小组件一起装进去。

免费 Apple ID 的限制依然存在：**App Groups 拿不到**，小组件会显示默认快照（立绘 + "噜噜正在发呆"），主 App 内一切正常。
想彻底正常，需要 99 美元/年的开发者账号，然后在 Xcode 里给两个 target 都勾上 App Groups → `group.com.lulu.pet`。

## 五、编译报错怎么办

把 Xcode 里红色的报错（或 Report navigator 里的完整日志）发回给我，通常是个别 API 签名细节，一两轮能改完。
这个工程的 Swift 代码**还没有被任何 Xcode 真正编译过**，第一次编译有小概率需要微调。
