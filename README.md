# CPI Research Dataset · 元联网研究文献库

**公开研究索引 · Cyber-Physical Internet · 文献、数据线索与证据来源**

面向 CPI 专题研究的可追溯文献数据集。出版日期截止 **2026-10-21**，构建于 **2026-10-22**。当前保留 **1,071 条分层记录**，其中 **43 条 CPI 核心记录**；这不是独立研究或同行评审论文数量，也不是穷尽性系统综述。

## 从这里开始

**[项目声明与文献使用说明](DISCLAIMER.md)** · [权利边界](RIGHTS.md) · [PDF 本地分析与写作](docs/pdf-workflow.zh-CN.md)。公开内容不包含论文原文、提取全文或第三方原始摘要；科研用途本身不替代具体授权条件。

**在线访问：[CPI 研究网站与学术地图](https://cpi-research-atlas.shentonyan.chatgpt.site)**。网站和 GitHub 仓库公开；下载原文和原始摘要缓存保留在本地或私有备份中。GitHub 文件页不会执行 HTML，因此请使用这个网站入口。

![CPI 学术地图预览](assets/academic-map.png)

地图包含主题共现、局部文献引用、研究时间线，可选择节点、检索文献、筛选年份与缩放。离线打开 `map.html` 也能使用。关系依据、范围与局限见 [学术地图方法](docs/academic-map.zh-CN.md)。

- **阅读**：[CPI 核心文献索引](docs/core-reading-index.zh-CN.md) · [研究路线与精读问题](docs/research-guide.zh-CN.md)
- **导入 Zotero**：[RIS 书目](data/processed/library.ris) · [BibTeX](data/processed/library.bib)
- **分析**：[全部 CSV](data/processed/corpus.csv) · [核心 CSV](data/processed/core_cpi.csv) · [JSONL](data/processed/corpus.jsonl) · [SQLite](data/processed/library.sqlite)
- **开始精读**：[研究提取表](data/processed/research_extraction_template.csv)
- **核验**：[方法与覆盖缺口](docs/methodology.zh-CN.md) · [字段字典](docs/data-dictionary.md) · [实际统计](data/processed/summary.json) · [PI/CPI网页线索与编码框架](docs/web-source-synthesis.zh-CN.md) · [外部来源台账](data/external_source_register.json)
- **浏览**：克隆或下载仓库后，双击根目录 `index.html`。离线支持题名、作者、DOI、关键词检索，按范围与年份筛选；不启用公开 Pages。

## 当前覆盖

| 范围 | 记录数 |
|---|---:|
| CPI 核心研究 | 43 |
| CPI 关联语境 | 5 |
| Physical Internet 基础 | 548 |
| 支撑技术与方法 | 118 |
| 种子参考背景 | 334 |
| 同名术语与历史 | 12 |
| 研究项目与动态 | 7 |
| 资源与数据入口 | 4 |

候选去重后 **5,067 条**，规则排除 **3,996 条**，**990 条含 DOI**。公开版本不转载第三方原始摘要，原检索中可取得摘要的记录用 `source_abstract_available` 标记，阅读请访问来源链接。排除记录保留于 [筛选决定](data/processed/screening_decisions.csv)，版本候选见 [可能版本](data/processed/possible_versions.json)。书目数量不等于独立研究数量。

来源包括 Crossref、DataCite、HAL、arXiv，以及大学机构库、出版社、会议和资助方页面。查询设有分页上限；没有 Scopus、WoS、CNKI 订阅检索。DBLP 遭遇限流。公开版本保留查询日志、来源、书目与筛选结果；完整原始响应保留在私有/本地研究输入中，详见 [公开版本说明](docs/public-release.md)。不把访问失败当成零篇结果。

## 证据状态

已归档并验证校验值的原始 PDF：**0**。本轮机构库全文下载受超时、TLS 或访问限制影响，详见 [全文清单](data/fulltext_manifest.json)。**没有把书目解析或机器抽取当成完成全文精读**；精读提取字段保留为空。

已发现 HKU CPI 配套数据的概念与版本 DOI，但 Figshare 明确标注文件禁运，因此仅收录公开元数据，没有获取禁运文件。记录类型、同行评审状态、全文状态和数据可得性分开管理。

## 本地重建与检索

需要 Python 3.10+。从仓库根目录运行：

```text
python -m pip install -r requirements.txt
python scripts/build_map.py
python scripts/finalize.py
python scripts/validate_public.py
python scripts/search.py "routing AND carbon" --tier core_cpi
```

已发布书目与地图可直接使用。完整重跑筛选需要本地原始输入；需要扩展检索时，运行采集脚本后再执行 `build.py`。原始缓存和下载的 PDF 写入忽略目录，`build.py` 在公开导出前移除原始摘要。不要直接上传采集目录；公开包使用 `scripts/package_public.py`。

## 研究纪律与私有性

标签由规则产生，不是已核验的方法分类。收录不表示支持论文结论；新闻、资助愿景、数值模拟、实验室演示和真实运营证据需要分别评价。术语历史不等于物流 CPI 直接研究。没有检出某个主题不证明研究空白。

仓库与网站公开。PDF 原文、提取全文和原始摘要缓存不随公开版本发布。公开不等于对第三方材料统一授权，详见 [项目声明](DISCLAIMER.md)、[权利边界](RIGHTS.md)及[本地 PDF 工作方式](docs/pdf-workflow.zh-CN.md)。

用户提供的行业网页和百科入口作为外部线索单独登记，不计入文献数量或学术证据。可读取页面的概念归纳、不可访问页面的状态，以及后续精读编码建议见 [PI/CPI网页线索与编码框架](docs/web-source-synthesis.zh-CN.md)。
