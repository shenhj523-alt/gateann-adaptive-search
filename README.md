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
