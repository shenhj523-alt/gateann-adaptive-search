# GateANN adaptive search budget

计算机系统设计课程实验的扩展实现。基于 GateANN-public 的固定提交 `71e87cbf0e25c0400c0109dd25a64a7c4dccc9dd`，复用原有的过滤、图穿越和异步读盘路径。课程数据与索引通过课程仓库取得。 [上游 GateANN](https://github.com/GyuyeongKim/GateANN-public) · [课程仓库](https://gitee.com/wei-fangyu/fvs-course-lab)

## 策略

- 每条查询先使用基础预算 L，在同一有序候选队列中保留至多 2L 个候选，起初仅扩展前 L 个。
- 活跃范围耗尽、精确匹配候选少于 2K 且保留区仍有未访问候选时，依次扩大至 L + ⌊L/2⌋ 和 2L。原候选、访问标记和已完成的距离计算继续使用。
- 匹配候选数是触发启发式。它不能保证目标召回率。默认使用固定预算，`GATEANN_ADAPTIVE_L=1` 启用策略。本实验使用 GateANN 的 YFCC mode 8。

## 复现

先按课程 README 准备固定版本 GateANN、AIO 构建依赖、YFCC 数据及 Formal 索引。在 GateANN 源码根目录应用补丁，然后重新编译。

```bash
git apply --check /path/to/gateann-adaptive-search/adaptive-budget.patch
git apply /path/to/gateann-adaptive-search/adaptive-budget.patch
cmake --build build --target search_disk_index_yfcc -j 2

python3 /path/to/gateann-adaptive-search/benchmark.py \
  --binary build/tests/search_disk_index_yfcc \
  --index-prefix /path/to/formal_index/yfcc \
  --dataset /path/to/yfcc_course_v1/formal_1000000 \
  --output ./adaptive-results
```

脚本对 Low、Medium、High 分别运行固定 L=320、自适应 L=320→480→640 和固定 L=640，默认三轮，每轮轮换方案执行顺序。固定 1 线程、beamwidth=8、K=10、FullAdj 邻居上限 32。记录 Recall@10、平均时延、平均逻辑 I/O、过滤跳过数、触发扩展数和达到预算上限的查询数。平均时延使用查询阶段计时除以查询数。

环境为 Ubuntu 24.04 WSL2，ext4 虚拟磁盘位于机械硬盘上。绝对时延仅适用于该环境。

## 三轮测试结果

Formal 数据包含 100 万条 YFCC 向量，每个负载 200 条查询。下表为各指标的三轮中位数。 [逐轮 CSV](results.csv)

| 负载 | 策略 | Recall@10 (%) | 平均时延 (ms) | 平均逻辑 I/O / 查询 | 扩展查询数 / 200 |
|---|---|---:|---:|---:|---:|
| Low | 固定 320 | 34.30 | 46.45 | 4.38 | 0 |
| Low | 自适应 | 51.60 | 92.69 | 7.41 | 198 |
| Low | 固定 640 | 51.80 | 86.51 | 7.72 | 0 |
| Medium | 固定 320 | 72.05 | 178.38 | 16.75 | 0 |
| Medium | 自适应 | 83.80 | 240.94 | 22.32 | 135 |
| Medium | 固定 640 | 87.10 | 319.62 | 31.95 | 0 |
| High | 固定 320 | 93.20 | 469.10 | 46.77 | 0 |
| High | 自适应 | 94.15 | 456.83 | 47.31 | 12 |
| High | 固定 640 | 98.65 | 840.02 | 88.92 | 0 |

Low 中有 191 条查询达到自适应上限，召回接近固定 640，但平均时延中位数更高。Medium 的自适应结果落在两档固定预算之间，节省了相对固定 640 的一部分 I/O 和时延，同时牺牲了 3.30 个百分点的召回。High 很少扩展，平均时延的轮间波动应结合原始 CSV 阅读。实验测量范围为平均查询时延和逻辑 I/O，尾时延、峰值内存及 SSD 性能仍需另行测试。
