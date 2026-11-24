# K12 全学科课堂 PPT 设计美学、原生矢量库与代码视频融合指南（v5.1）

> 核心理念：**既要博物馆杂志级高级感，也要 11 页视觉丰富零撞脸，更要 100% 全学科教学准确与希沃白板全可改字！**
> 高级感 = **全学科策展色板** + **最多 3–4 张差异化 `ImageGen` 无字主视觉（`add_picture_cover` 自动居中裁切不拉伸、0 重复）** + **`scripts/ppt_kit.py` 全学科原生矢量工程图解** + **P04 离线内嵌 Three.js 3D 代码演示视频** + **全页讲稿备注与淡出转场**。

---

## 一、16:9 黄金版式网格与 11 页「全学科通用零重复」分镜矩阵

画布锁定 **16:9 宽屏（`13.333 in × 7.5 in`）**，通过 `scripts/ppt_kit.py` 复用经过防重叠验真的整页构建器与矢量组件：

| 页序 | 角色定位 | 推荐底色 | 全学科通用构建函数与媒体配方（严禁两页复用同图！） |
|---|---|---|---|
| **P01** | 电影封面 | 深色焦页 | `add_hero_slide()` + **主图 1（`ImageGen` 暗调主题雕塑封面，自动居中裁切）** |
| **P02** | 真实情境导入 | 亮色画廊 | `add_split_visual_slide(..., dark=False)` + **主图 2（`ImageGen` 明亮自然日光实景）** + 3 段条件/问题卡 |
| **P03** | 探究脉络/猜想 | 亮色画廊 | **无 AI 照片！** 左列调 `add_process_timeline_card()`（文史理化生脉络步骤）或 `add_equal_base_height_gauge()`（立体几何标尺）+ 右列探究任务 |
| **P04** | **3D 代码视频页** | **深色剧场** | `add_video_slide()` **离线内嵌 `k12_studio.py render-video` 生成的 1280×720 带声 MP4** + 右侧 3 步观察节拍 |
| **P05** | 核心推导/意象中枢 | 深色焦页 | **无 AI 照片！** 左列核心公式/主旨金句 + 右列调 `add_concept_hub_card()`（语文意象/英语语法/生物结构）或 `add_three_to_one_derivation_graphic()` |
| **P06** | 正反辨析/冲突对比 | 亮色画廊 | `add_split_visual_slide()` 搭配 **主图 3（`ImageGen` 暖白顶光对比教具/器物）**，或调 `add_comparison_matrix_card()` 原生双栏对比矩阵 |
| **P07** | 教材例题/结构精讲 | 亮色画廊 | **无 AI 照片！** 左 38% 调 `add_subject_blueprint_card()`（支持几何/凸透镜/电路等）或 `add_cone_blueprint_card()` + 右 58% 分步板书解析 |
| **P08** | 随堂梯度练兵 | 亮色画廊 | `add_tiered_practice_slide()`：3 列顶线色标练兵卡（★基础 → ★★进阶 → ★★★拔高）+ 底部作答顺序条 |
| **P09** | 高频避坑矩阵 | 亮色画廊 | `add_pitfall_matrix_slide()`：2×2 暖砂纸微底避坑卡（红标典型错因 + 青标救场正解）+ 底部 10 秒自查横幅 |
| **P10** | 一页记住小结 | 深浅 40:60 | `add_summary_table_slide()`：左 40% 深色核心提炼 + 右 60% 原生可编辑对比表格 + 必做/选做/口头分层作业 |
| **P11** | 大屏互动剧场衔接 | 深色焦页 | `add_split_visual_slide(..., dark=True, image_on_left=False)` + **主图 4（`ImageGen` 全息舞台或地标实景）** + 课堂 PK 衔接脚本 |

---

## 二、内置全学科策展色彩系统（`ppt_kit.get_theme(subject)` 自动映射）

1. **`math`（曜石深海 × 博物馆暖亚麻）**：深色 `#0B1A20` + 香槟黄铜 `#E2B45A`；亮色 `#F6F2EA` + 海玻璃青 `#155E68` + 烧陶朱砂 `#C84B31`。
2. **`chinese` / `history` / `geography` / `morality`（宋画青绿 × 古宣茶白）**：深色 `#132624` + 烫金 `#DFB35C`；亮色 `#F7F3E8` + 石青 `#22577A` + 印泥朱砂 `#B83B2A`。
3. **`english`（胶片暖阳 × 釉彩绘本）**：深色 `#18243E` + 暖蜜金 `#F4B942`；亮色 `#FBF7EE` + 釉蓝 `#2563EB` + 珊瑚橘 `#E85D3F`。
4. **`science` / `physics` / `chemistry`（暗室激光 × 钛金光学）**：深色 `#09131F` + 激光青 `#7DD3FC`；亮色 `#F3F6F9` + 翡翠青 `#0F8B74` + 琥珀金 `#D97706`。
5. **`biology`（深翠显微 × 自然暖纸）**：深色 `#0B1E19` + 琥珀金 `#E8BC5A`；亮色 `#F4F8F5` + 森翠 `#0F8B6D` + 暖橙 `#D96B27`。

---

## 三、防重复、零拉伸与希沃可编辑验收铁律

1. **严禁图片拉伸与重复贴图**：插图统一通过 `add_picture_cover()` 按目标框比例自动居中裁切；`k12_studio.py audit-pptx` 自动计算图片 SHA-256 拦截 `duplicate_images`。
2. **100% 原生可编辑对象**：所有标题、公式、步骤、矢量节点与对比表格均为 PPT 原生形状与文本框，进入希沃白板、WPS 与 PowerPoint 可直接双击改字。
3. **双重验收**：运行 `python "{skill_dir}/k12_studio.py" audit-pptx "<out_dir>/deck.pptx" --render-sheet "<work_dir>/ppt_sheet.png"`，确认 `passed: true` 后肉眼复核 1 张 `<work_dir>/ppt_sheet.png` 交付。
