# B(l)utter 中文说明

Flutter 移动应用逆向工具。它会根据目标应用里的 Flutter/Dart 信息，自动准备匹配的 Dart AOT Runtime，再运行 `blutter` 做分析。

当前已知限制：

- 目前主要支持 Android `libapp.so`
- 目前仓库说明里只明确支持 `arm64`
- 首次分析某个 Dart 版本时，可能需要下载 Dart SDK 源码并编译，耗时会明显更长

## 这个工具到底怎么用

你需要给它提供下面两种输入之一：

- 一个 APK 文件
- 一个已经从 APK 中解出来的 `lib/arm64-v8a` 目录，目录里至少要有 `libapp.so` 和 `libflutter.so`

程序入口是：

```bash
python3 blutter.py <输入路径> <输出目录>
```

例如：

```bash
python3 blutter.py path/to/app.apk out_dir
python3 blutter.py path/to/lib/arm64-v8a out_dir
```

如果本地还没有匹配当前 Dart 版本的构建产物，它会自动做下面这些事：

1. 从目标文件中提取 Dart 版本和快照信息
2. 拉取匹配版本的 Dart SDK 源码
3. 用 `cmake + ninja` 编译 Dart VM 静态库
4. 编译对应版本的 `blutter`
5. 对 `libapp.so` 进行分析并生成输出文件

## 最推荐的使用方式：Docker

这个项目最稳妥的用法是跑在 Linux 容器里，因为它本身就更偏向 Linux 构建环境。Windows 下建议直接使用 Docker Desktop。

### 1. 准备条件

- 已安装 Docker Desktop，且能正常执行 `docker`
- 当前目录就是本仓库根目录

### 2. 构建镜像

在仓库根目录执行：

```bash
docker build -t blutter:local .
```

这个镜像会安装项目需要的依赖：

- `python3`
- `git`
- `cmake`
- `ninja`
- `build-essential`
- `pkg-config`
- `libicu-dev`
- `libcapstone-dev`
- `python3-pyelftools`
- `python3-requests`

### 3. 创建缓存卷

建议先创建下面 4 个 Docker volume。这样第一次编译出的缓存会保留下来，后面再次分析时会快很多。

```bash
docker volume create blutter-dartsdk
docker volume create blutter-build
docker volume create blutter-packages
docker volume create blutter-bin
```

它们分别对应容器内这些目录：

- `/app/dartsdk`
- `/app/build`
- `/app/packages`
- `/app/bin`

### 4. 查看帮助

先确认镜像能启动：

```bash
docker run --rm blutter:local
```

默认会输出命令行帮助。

### 5. 分析 APK

假设你的 APK 文件放在当前目录，文件名是 `app.apk`：

```bash
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "${PWD}:/work" blutter:local /work/app.apk /work/out
```

含义是：

- 把当前目录挂载到容器里的 `/work`
- 容器读取 `/work/app.apk`
- 分析结果写到 `/work/out`

运行结束后，你可以直接在当前目录看到 `out` 文件夹。

### 6. 分析已经解包的 `lib` 目录

如果你已经手动把 APK 中的 `lib/arm64-v8a` 解出来了：

```bash
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "${PWD}:/work" blutter:local /work/lib/arm64-v8a /work/out
```

要求这个目录里至少有：

- `libapp.so`
- `libflutter.so`

### 7. 首次运行为什么很慢

第一次运行慢是正常现象。常见原因有：

- 需要从目标文件里识别 Dart 版本
- 需要拉取对应版本的 Dart SDK 源码
- 需要在容器里编译 Dart VM
- 需要编译 `blutter`

只要上面的 Docker volume 没删，后续再次分析相同或相近版本时通常会快很多。

## 用 docker compose 会更省事

仓库里已经加了 [docker-compose.yml](docker-compose.yml)。它把这几个缓存卷都固化进去了：

- `blutter-dartsdk`
- `blutter-build`
- `blutter-packages`
- `blutter-bin`

这样你不需要每次都手写一长串 `-v` 参数。

### 1. 先构建

```powershell
docker compose build
```

### 2. 先看帮助

```powershell
docker compose run --rm blutter
```

### 3. 分析当前仓库目录里的 APK

如果你把 `app.apk` 放在仓库根目录，直接执行：

```powershell
docker compose run --rm blutter /work/app.apk /work/out
```

### 4. 分析别的目录里的 APK

更常见的情况是 APK 不在仓库目录，而是在别的目录。此时先设置 `BLUTTER_WORKDIR`，让 Compose 把那个目录挂载到容器里的 `/work`。

PowerShell 示例：

```powershell
$env:BLUTTER_WORKDIR = "D:\Samples\flutter-app"
docker compose run --rm blutter /work/app.apk /work/out
```

如果你分析完成后不想保留这个环境变量：

```powershell
Remove-Item Env:BLUTTER_WORKDIR
```

### 5. 分析已经解包的 `lib/arm64-v8a`

```powershell
$env:BLUTTER_WORKDIR = "D:\Samples\flutter-app"
docker compose run --rm blutter /work/lib/arm64-v8a /work/out
```

### 6. 常用额外参数

强制重编译：

```powershell
$env:BLUTTER_WORKDIR = "D:\Samples\flutter-app"
docker compose run --rm blutter /work/app.apk /work/out --rebuild
```

跳过分析相关功能：

```powershell
$env:BLUTTER_WORKDIR = "D:\Samples\flutter-app"
docker compose run --rm blutter /work/app.apk /work/out --no-analysis
```

### 7. Compose 方案和 `docker run` 的区别

- `docker run` 更直接，适合临时跑一次
- `docker compose` 更省事，缓存卷已经写进配置里，命令更短
- 两者本质上跑的是同一个镜像，分析结果没有区别

## Windows PowerShell 下怎么用

如果你是在 Windows PowerShell 里执行，上面的命令可以直接用。最常见的场景就是：

```powershell
docker build -t blutter:local .
docker volume create blutter-dartsdk
docker volume create blutter-build
docker volume create blutter-packages
docker volume create blutter-bin
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "${PWD}:/work" blutter:local /work/app.apk /work/out
```

如果你不想依赖当前目录，也可以把挂载写成绝对路径，例如：

```powershell
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "D:\Samples\flutter-app:/work" blutter:local /work/app.apk /work/out
```

## 常用参数

### 强制重新编译

如果你更新了仓库，或者怀疑已有构建产物不对，可以加 `--rebuild`：

```bash
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "${PWD}:/work" blutter:local /work/app.apk /work/out --rebuild
```

### 跳过代码分析相关功能

```bash
docker run --rm -it -v blutter-dartsdk:/app/dartsdk -v blutter-build:/app/build -v blutter-packages:/app/packages -v blutter-bin:/app/bin -v "${PWD}:/work" blutter:local /work/app.apk /work/out --no-analysis
```

### 没有 `libflutter.so` 时手动指定 Dart 版本

这是少见场景。你可以直接把输入当成 `libapp.so`，并手动指定版本：

```bash
python3 blutter.py path/to/libapp.so out_dir --dart-version 3.4.2_android_arm64
```

如果你想用 Docker 做这个场景，也可以照样把输入文件挂进 `/work` 后追加参数。

## 输出结果里会有什么

常见输出包括：

- `asm/*`：带符号的汇编结果
- `blutter_frida.js`：Frida 脚本模板
- `objs.txt`：对象池完整导出
- `pp.txt`：对象池里的 Dart 对象

## 目录说明

- `bin`：每个 Dart 版本对应的 `blutter` 可执行文件
- `blutter`：C++ 源码
- `build`：构建目录
- `dartsdk`：拉取下来的 Dart Runtime 源码
- `external`：Windows 下用到的第三方库
- `packages`：编译后的 Dart Runtime 静态库
- `scripts`：辅助脚本

## 直接本机运行

如果你不使用 Docker，也可以直接在本机运行，但需要自己准备好构建环境。

Linux 下依赖大致如下：

```bash
apt install python3-pyelftools python3-requests git cmake ninja-build \
    build-essential pkg-config libicu-dev libcapstone-dev
```

然后执行：

```bash
python3 blutter.py path/to/app.apk out_dir
```

## 排错建议

### 容器启动了，但输出目录没有结果

先检查：

- 输入路径是不是挂载到 `/work` 下面了
- 传入的是 APK，还是包含 `libapp.so` 和 `libflutter.so` 的目录
- 输出目录参数是不是写成了容器内路径，例如 `/work/out`

### 第一次运行卡很久

优先看是不是在做这些事情：

- `git clone` Dart SDK
- `cmake` 配置
- `ninja` 编译

这通常不是卡死，而是在首次准备工具链和产物。

### 想彻底重来

可以删除这些 Docker volume 后重新跑：

```bash
docker volume rm blutter-dartsdk blutter-build blutter-packages blutter-bin
```
