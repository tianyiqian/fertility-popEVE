# Fertility-popEVE 模型优化指南

## 目标

本项目以跨物种模型的 EVE 分数为输入，并使用妇产队列中的变异观察情况进行按蛋白的 Gaussian Process（GP）校准。输出不是临床诊断结论，而是队列特异的变异出现概率及其不确定性，供后续基因负担和表型关联分析使用。

## 数据与标签定义

候选空间来自 `models/popeve_data/grch38_popEVE_ukbb_20250715.vcf.gz`：该文件包含基因组坐标、RefSeq 蛋白、氨基酸突变和 EVE/ESM1v/popEVE 分数。训练标签 `cohort_observed` 定义为：候选 DNA 变异是否至少在一个通过质量控制的妇产队列先证者中观察到。

同一氨基酸突变可由多个 DNA 变异编码。构建时按 `protein_id + mutant` 合并；任一编码在队列中出现即标记为 1。基础输入分数为 EVE，因此新 GP 是对妇产队列观察模式的校准，而不是重训练 EVE 蛋白语言/进化模型。

## 完整工作流

1. 从全部先证者 gVCF 做联合调用，得到标准化、拆分多等位、通过变异质量控制的联合 VCF。
2. 用 VEP 注释、提取错义变异并建立 `protein_table.parquet`。
3. 构建候选空间：

```bash
conda run -n popeve python scripts/14_build_gp_candidate_space.py
```

输出 `data/gp/candidate_space.parquet`。其中包含全部候选错义变异、EVE 分数以及 `cohort_observed`。

4. 构建每蛋白训练表和准入报告：

```bash
conda run -n popeve python scripts/11_build_gp_training.py
```

输出 `data/gp/training/*.csv` 与 `training_readiness.csv`。

5. 在 GP 环境中训练所有通过准入的蛋白：

```bash
conda env update -n fertility_gp -f environment/fertility_gp.yml
conda run -n fertility_gp python scripts/15_train_fertility_popeve.py
```

每个蛋白输出到 `data/gp/models/`：`*.pt` 为模型状态，`*_history.csv` 为 ELBO 损失，`*_scores.csv` 为每个候选突变的预测概率和 5%/95% 区间。

## 科学准入标准

默认要求每个蛋白至少有 100 个候选错义变异和 10 个队列观察到的突变。低于该阈值的蛋白不训练，因为极少阳性样本会导致 GP 只拟合采样稀疏性，而不是妇产相关约束。阈值记录在 `config/config.yaml`；改变阈值必须在分析报告中说明并进行敏感性分析。

当前 `joint_test` 仅是开发测试数据：75 个蛋白共 123 个观察变异、每蛋白最多 8 个，因此不会产生正式模型。这是预期的质量保护。正式训练必须切换到 2,572 个先证者 gVCF 的全队列联合 VCF。

## 评估与解释

训练后至少检查：训练损失是否稳定；预测概率是否随 EVE 呈合理趋势；不同蛋白的阳性数与分数分布；已知致病/良性集合或独立留出队列上的排序能力。不要将 GP 概率直接解释为个人患病概率，也不要把病例队列中的“观察到”当作致病标签。

## 可复现性

训练固定随机种子 42，并保存模型、训练历史、输入评分范围及预测区间。每次训练应保留输入 VCF、VEP/参考版本、样本纳入排除规则、祖源与覆盖度质控、代码 commit 和配置文件副本。
