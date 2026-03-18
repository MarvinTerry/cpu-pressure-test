# CPU Frequency Performance Plotting

本项目用于整理和可视化通过 `s-tui` 采集到的 CPU 监控数据。

当前脚本会批量读取 `data/` 目录下的实验 CSV，提取以下指标并生成图表：

- 横轴：`Time`
- 纵轴：`Temp:Soc_Thermal,0`
- 纵轴：`Frequency:Core 0`
- 纵轴：`Frequency:Core 1`
- 纵轴：`Frequency:Core 2`
- 纵轴：`Util:Avg`

每个实验 CSV 会生成一张 PNG 图片，输出到 `plots/` 目录。

## 数据来源

实验数据由 `s-tui` 导出得到。

`s-tui` 是一个终端下的 CPU 监控工具，可以显示温度、频率、功耗、利用率等信息，也支持将统计结果保存为 CSV。根据 `s-tui` 官方 README，可使用 `--csv` 开启 CSV 导出，使用 `--csv-file` 指定输出文件名。

本项目中的原始数据文件位于 `data/` 目录，例如：

- `data/s-tui_log_2026-03-18_12_06_24.csv`
- `data/s-tui_log_2026-03-18_12_23_39.csv`
- `data/s-tui_log_2026-03-18_12_32_54.csv`

## s-tui 使用方式

### 安装 s-tui

可以按官方方式安装：

```bash
pip install s-tui --user
```

如果是 Debian / Ubuntu 系，也可以直接使用系统包：

```bash
sudo apt install s-tui
```

如果你还希望在 `s-tui` 中进行压力测试，可以额外安装 `stress`：

```bash
sudo apt install stress
```

### 启动 s-tui

最基础的启动方式：

```bash
s-tui
```

常见操作方式：

- 使用方向键或 `hjkl` 在侧边栏中移动
- 在 `Graphs` 中选择要显示的图
- 在 `Summaries` 中选择要显示的统计项
- 按 `q` 退出

查看命令行帮助：

```bash
s-tui --help
```

### 导出 CSV

采集实验数据时，建议直接导出到本项目的 `data/` 目录：

```bash
s-tui --csv --csv-file data/s-tui_log_$(date +%F_%H_%M_%S).csv
```

如果你的终端环境对鼠标支持不稳定，可以加上：

```bash
s-tui --no-mouse --csv --csv-file data/s-tui_log_$(date +%F_%H_%M_%S).csv
```

## 图表标题说明

图表标题来自 `data/DISCRIPTION.csv`。

该文件当前使用两列：

- `file_name`：实验 CSV 路径
- `conditioon`：该次实验条件说明

示例：

```csv
file_name,conditioon
data/s-tui_log_2026-03-18_12_06_24.csv, no heat sink and exposed in air
data/s-tui_log_2026-03-18_12_23_39.csv, no heat sink and fixed in model
```

绘图脚本会按文件名匹配描述，并将描述写入图表标题。如果某个实验 CSV 在 `DISCRIPTION.csv` 中没有对应描述，则回退为 CSV 文件名。

## 测试条件说明

本项目中的测试平台为 Firefly `ROC-RK3588S-PC` 主板。

`data/DISCRIPTION.csv` 中各实验条件的含义如下：

- `no heat sink and exposed in air`：主板未安装散热器，裸板暴露在空气中运行
- `no heat sink and fixed in model`：主板未安装散热器，放置在无人机球壳内部进行封闭测试
- `heat sink with fan on and exposed in air`：主板安装 Firefly 官方散热器，风扇开启，暴露在空气中运行
- `heat sink with fan off and exposed in air`：主板安装 Firefly 官方散热器，风扇关闭，暴露在空气中运行

也就是说：

- `no heat sink` 表示裸板运行，不安装 heat sink
- `fixed in model` 表示主板固定在无人机球壳内部，属于封闭环境测试
- `heat sink` 表示使用 Firefly 官方散热器

如果需要对外同步测试条件，可以使用下面这段描述：

> 测试使用 Firefly ROC-RK3588S-PC 主板进行。`no heat sink` 条件下为裸板运行；`fixed in model` 表示将主板放入无人机球壳内部进行封闭测试；`heat sink` 条件下使用 Firefly 官方散热器，其中分别测试了风扇开启和关闭两种情况。

## 图表处理方式

绘图脚本为：

```bash
plot_csv_charts.py
```

处理逻辑如下：

1. 批量扫描 `data/*.csv`
2. 自动跳过 `data/DISCRIPTION.csv`
3. 读取每个实验 CSV 的 `Time` 列并转换为时间轴
4. 提取以下 5 个指标：
   - `Temp:Soc_Thermal,0`
   - `Frequency:Core 0`
   - `Frequency:Core 1`
   - `Frequency:Core 2`
   - `Util:Avg`
5. 为每个实验绘制一张图
6. 图中使用 3 个共享时间轴的子图：
   - 上方：SoC 温度
   - 中间：3 个核心频率
   - 下方：平均利用率
7. 输出为 `plots/<csv文件名>.png`

之所以拆成 3 个子图，而不是把所有指标叠在同一个坐标轴里，是因为温度、频率、利用率量纲不同，分开展示更容易比较趋势。

## Python 环境与依赖

本项目使用 `uv + venv` 管理 Python 环境。

### 初始化环境

```bash
uv venv .venv
uv sync
```

### 主要依赖

- `pandas`
- `matplotlib`

依赖定义在 `pyproject.toml` 中，锁定结果在 `uv.lock` 中。

## 图表生成方式

在项目根目录运行：

```bash
uv run python plot_csv_charts.py
```

执行后会自动：

- 读取 `data/` 下所有实验 CSV
- 读取 `data/DISCRIPTION.csv` 中的实验描述
- 生成对应图表到 `plots/`

## 输出目录

- 原始实验数据：`data/`
- 图表输出目录：`plots/`
- Matplotlib 本地缓存：`.cache/matplotlib/`

## 参考

`s-tui` 使用说明参考其官方项目页面与 README：

- https://github.com/amanusk/s-tui
- https://amanusk.github.io/s-tui/
