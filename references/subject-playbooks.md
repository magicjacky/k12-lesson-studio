# 全学科备课与视觉多样化创意适配指南（K12 全科通用 · v5.1）

> 无论放入哪一科教材 PDF（电子版或扫描件），第一步自动识别学科与学段，匹配专属**策展色板（`get_theme` 与 `<work_dir>/theater_config.json` 的 `theme`）、4 槽位差异化 `ImageGen` 主视觉、`ppt_kit.py` 原生矢量图解、内置 Three.js 全学科 3D 演示基元（禁用 `VideoGen`）、学科防错红线与大屏 4 队 PK 竞技场**。

---

## 一、全学科自动路由、原生组件与 3D 场景总表

| 学科 | 主题键 (`theme`) | PPT 原生矢量图解首选 (`scripts/ppt_kit.py`) | Three.js 3D 代码视频首选基元 (`video_stage.html`) | 学科防错红线与大屏互动原型 |
| --- | --- | --- | --- | --- |
| **小学/初中数学** | `math` | `add_equal_base_height_gauge` / `add_three_to_one_derivation_graphic` / `add_cone_blueprint_card` / `add_subject_blueprint_card` | `createCrystalCylinder` + `createCrystalConeVessel` + `createPourStream` + `create3DArrow`（`'obsidian'`） | 严守学段算法（小学禁方程，锁定 `π≈3.14`）；3D 展开/切扇拼接/倾倒实验 + **星海/赤焰/翡翠/鎏金 4 队 PK** |
| **语文** | `chinese` | `add_process_timeline_card`（行文/情感脉络）+ `add_concept_hub_card`（古诗核心意象群）+ `add_comparison_matrix_card`（手法对比） | `'ink'` 宋画墨韵舞台 + 3D 山水层叠视差镜头漫游 + `createFlowPath` 行旅路线 + 逐句光影字幕 | 课文、古诗、朝代、生字注音逐字核对教材原文；画卷意象漫游剧场 + **青竹/朱砂/金桂/碧水 4 队飞花令 PK** |
| **英语** | `english` | `add_concept_hub_card`（主题词汇句型网）+ `add_comparison_matrix_card`（时态/句式辨析）+ `add_process_timeline_card`（故事事件链） | `'linen'` / `'obsidian'` 微缩 3D 方位介词剧场 + 时间轴动词状态变化演示 + 节拍字幕 | 严格对照单元词汇表、音标与课标语法边界；情境热区拆音拼句剧场 + **极光/星火/森林/金阳 4 队单词 PK** |
| **物理** | `physics` | `add_subject_blueprint_card(..., kind='convex_lens'|'circuit')` + `add_comparison_matrix_card`（实像vs虚像/串并联对比） | `'laser'` 暗室舞台 + `createLaserBeam` + `createOpticalElement`（斯涅尔折射/透镜聚焦）+ `create3DArrow`（受力矢量） | 严格遵守折射定律、透镜成像公式与受力平衡方程；可拖拽物距/入射角光学实验台 + **极光/雷霆/磁力/星轨 4 队 PK** |
| **化学** | `chemistry` | `add_process_timeline_card`（实验制取与检验步骤）+ `add_comparison_matrix_card`（宏观现象vs微观实质） | `'laser'` 舞台 + `createMolecule`（3D 球棍分子键断裂与重组守恒动画）+ `createCrystalCylinder`（滴定变色） | 方程式严格配平、标明反应条件与沉淀气体符号、原子个数守恒；微粒反应实验室 + **翡翠/焰心/冰晶/紫曜 4 队 PK** |
| **生物** | `biology` | `add_process_timeline_card`（生理循环流程）+ `add_concept_hub_card`（结构与功能适应网）+ `add_comparison_matrix_card`（呼吸vs光合） | `'emerald'` 深翠舞台 + `createFlowPath`（3D 半透明血管/叶脉携氧变色粒子流） | 器官结构名称、瓣膜方向与物质交换流向严谨无误；生命流动 3D 解剖剧场 + **森灵/深蓝/晨光/琥珀 4 队 PK** |
| **历史/地理/道法** | `history` / `geography` | `add_process_timeline_card`（时空大事年表/成因链）+ `add_comparison_matrix_card`（阶段/区域对比）+ `add_concept_hub_card`（区位要素） | `'ink'` / `'obsidian'` 3D 地形沙盘 + `createFlowPath`（水循环水汽/洋流/丝路发光路线蔓延） | 史实年代、地名方位与因果链条逐一核实；流光时空沙盘剧场 + **丝路/沧溟/昆仑/长安 4 队 PK** |

---

## 二、全学科交付五条自检清单

1. **教材核验零超纲**：电子版与扫描件均逐页核对原题、原文与留白，写出 ≥6 条本学段禁超纲红线。
2. **PPT 零重复、零拉伸、全可改**：最多 4 张不同视觉世界 `ImageGen` 图（`add_picture_cover` 自动裁切），原理与例题页全走原生矢量组件，`audit-pptx` 通过。
3. **代码视频零角标、物理准**：统一通过 `k12_studio.py render-video` 输出高清 MP4 与轻量 HTML 版 MP4，1 张 16 格总览图核验无穿模。
4. **互动网页单文件断网秒开**：复用 `assets/theater_base.html` 配置对应学科 `theme`，通过 `audit-html` 全按钮点击与 `1280×720` 零溢出校验。
5. **试卷双卷同源、红笔清晰**：通过 `k12_studio.py verify-exam` 同源生成学生作答卷（带答题线、0 漏答案）与教师朱砂红解析卷，阅卷报告经 `verify-grading` 单源统计零矛盾。
