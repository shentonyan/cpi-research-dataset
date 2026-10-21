# 检索、筛选与证据边界

**公开版本补充（2026-10-22）：** 本文描述最初检索过程。完整原始响应与摘要缓存现保留在私有/本地备份中，不在公开仓库历史里；公开库保留查询日志、书目、规则标签与筛选决定，第三方原始摘要不转载。完整重跑筛选需重新取得本地输入，不能仅凭移除摘要的公开快照复现所有判断。见 [公开版本说明](public-release.md) 和 [项目声明](../DISCLAIMER.md)。

本库是面向持续研究的可扩展文献数据集，不宣称穷尽、完成系统综述或确认研究空白。出版日期截点为 **2026-10-21**；检索与构建跨至 **2026-10-22**。API 返回时间保存在原始响应封装中。当前年份尚未结束，年度数量不可与完整年份直接比较。

## 检索范围

核心对象：物流、制造与供应网络语境中的 Cyber-Physical Internet（CPI／元联网）。背景对象包括 Physical Internet、数字互操作、数物物流、超互联物流以及直接被核心种子引用的方法研究。

检索不用单独的 CPI 缩写作主词，避免消费者价格指数、处理器指标等同名噪声。保留早期同名 Cyber-Physical Internet 研究作术语溯源，但单列 `terminology_history`，不混入现代物流 CPI 核心。

数据源与实际执行记录：

| 来源 | 执行方式 | 状态与边界 |
|---|---|---|
| Crossref | 7 个检索流、注册 DOI 解析、10 个种子的参考文献一跳扩展 | 完成；相关度排序、每流有页数上限，不是 Boolean 全检 |
| DataCite | CPI 短语检索与 PI 题名检索 | 结果及 API 计数存档；可能匹配描述、全文或宽泛术语，之后才筛选 |
| HAL | CPI 短语与 PI 题名检索 | 返回记录及摘要；并非法国或全球所有研究的完整索引 |
| arXiv | PI/CPI 题名检索 | XML 原始响应存档；预印本与期刊版可能重复 |
| DBLP | CPI/PI 检索 | 本轮批量 API 遇到 HTTP 429，未把失败伪记成零篇；个别网页线索仍可用于 DOI 种子发现 |
| 出版社、大学机构库、资助方、会议网站 | 补充检索与来源页核对 | 精选元数据见 `data/curated_sources.json`；不是这些网站的全站爬取 |
| OpenAlex | 未执行 | 无可用密钥，按检索技能要求不调用无密钥接口 |
| Scopus / Web of Science / CNKI / ProQuest | 未执行 | 未获得订阅检索结果；不能声称覆盖这些库 |

## 检索表达式与截断

权威表达式与上限在 `scripts/harvest.py` 的 `STREAMS`；HAL/DBLP/arXiv 在 `scripts/discover.py`。实际请求 URL、返回条数、API 报告的命中数、时间在 `data/search_log.json`、`data/raw/` 和 `data/supplemental_discovery.json`。

Crossref 流：Cyber-Physical Internet 题名（最多 1,000）；CPI 全字段短语（最多 1,000）；Physical Internet 题名（最多 2,000）；Cyber physical logistics 题名（最多 300）；digital twins physical internet（最多 300）；hyperconnected logistics 题名（最多 300）；元联网（最多 200）。

Crossref 不保证严格短语、AND 或同义词语义；其百万级模糊命中总数不是本领域文献数量。使用 `sort=score&order=desc`，保留实际返回结果，然后在题名和可用摘要上规则筛选。原始 `crossref_*` 无 ranked 前缀文件为首次发现默认排序问题时保留的试探请求，最终构建只使用 `crossref_ranked_*`、DOI 解析和补充来源，不将试探请求视作正式检索流。

DataCite 每流最多 1,000 条；HAL 各流上限 500/1,000；arXiv 上限 300。当前查询结果是否达到上限，应以保存的原始计数为准。扩展检索时不能只增大 README 的数字，需实际更新原始记录与筛选结果。

## 去重与版本

1. DOI 去掉 `https://doi.org/` 并转为小写，作为主要合并键。
2. 没有 DOI 时保留 URL 身份；相同 DOI 的 HAL、DataCite、Crossref 信息补缺，保留多个发现入口。
3. 相同规范化题名、不同 DOI/URL 列入 `possible_versions.json`，不擅自合并。
4. 会议海报、预印本、学位论文及其期刊文章可能属于同一研究。**本库的核心记录数量不是独立研究或同行评审文章数量。**
5. 数据集概念 DOI 与版本 DOI 可能同时存在；`relations` 保存来源声明，版本文件不能当成两份独立实证数据。

## 筛选规则

| 层级 | 规则与用途 |
|---|---|
| `core_cpi` | 题名含 CPI 全称，并有物流/运输/生产/路由等语境；少量机构库记录由来源页明确补充 |
| `cpi_context` | 题名未直接出现全称，但摘要或来源页确认 CPI 研究语境 |
| `physical_internet` | 题名出现 Physical Internet 或 Internet Physique；为基础文献，不自动等同 CPI |
| `enabling_research` | 题名同时含物流对象及数物、孪生、超互联、互操作等支撑主题 |
| `reference_context` | 种子引用、但不满足前述主题门槛；仅作方法背景，不能据此声称与 CPI 直接相关 |
| `terminology_history` | 同名术语、语境未明确为物流 CPI，需进一步判断 |
| `projects_news` | 研究资助、研究讲座和项目动态 |
| `resource_portal` | 会议目录、项目成果与数据入口 |
| `excluded` | 可用题名/摘要无主题信号，或明确晚于截点 |

所有决定保留在 `screening_decisions.csv/jsonl`，包括排除记录。字段缺失导致的假阴性仍可能存在。以固定随机种子抽取纳入/排除各 30 条进行了模型辅助题名检查，具体 ID 与判断见 `data/processed/screening_spotcheck.json`；不是双人独立筛选，不报告虚构的一致性系数。

主题标签来自 `scripts/build.py` 中公开的正则词表，不是作者关键词，也不等于论文实际方法或贡献。跨年度计数、标签交叉等仅可描述这个语料库，不能直接用于宣称整个学科的趋势或空白。

## 元数据、全文与研究结论

- `registry_resolved`：注册元数据已解析，不代表全文已审阅。
- `repository_metadata`：机构库元数据，不保证同行评审状态。
- `source_page_checked_partial_metadata`：来源页确认存在；作者、日期等字段仍可能缺失。
- 所有 `reading_status` 初始均为 `not_read`；未完成系统性全文精读。
- 注册平台和 Crossref 的引文数是动态、不完整的快照，不能相互直接比较。
- API 摘要可能缺失、存在版权约束，或含发布者文本错误；保留来源，后续应与原文核验。
- 不从题名推断结果，不把作者声称的效果提升当成已独立验证的事实；精读提取表先保留空白。

## 全文与数据文件

`data/fulltext_manifest.json` 记录每次尝试、失败原因及成功文件校验值。只归档有明确授权依据的原始 PDF，不绕过登录、付费或禁运。本文献库可以在没有本地 PDF 的情况下完整使用来源链接、摘要和书目。

已发现的 HKU 数据记录 `10.25442/hku.32593509` / `.v1`：Figshare 公共 API 明确返回 `is_embargoed=true` 且不提供文件列表。本轮只收录公开元数据和入口，**未取得数据文件，不能称作可直接复现的数据集**。原始记录在 `data/raw/figshare_32593509.json`。

Georgia Tech 的部分 DataCite 记录同时声明版权保留和 CC0。不能根据其中一个 CC0 字段推定论文全文可以无限制再分发；保留原始声明，未据此批量复制全文。

## 更新与复现

`harvest.py` 使用持久响应缓存；在同一缓存上重建可复现，本地脚本不会承诺互联网搜索结果永远相同。更新请复制一个新工作目录和快照，不覆盖现有原始快照；修改出版截点、运行检索、人工审查版本与例外、重建并验证，再作新的 Git 提交。

经维护者明确授权，审查后的元数据仓库和网站公开；原始研究输入保留在私有备份和本地。未启用定时抓取、GitHub Pages 或外部分析。仓库可见性与网站访问权限分别核验。
