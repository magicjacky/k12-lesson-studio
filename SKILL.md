---
name: k12-lesson-studio
display_name: "中小学全学科课件一键制作"
display_name_en: "K12 Lesson Studio — All-Subject Teaching Prep"
version: "5.1.0"
license: PolyForm-Noncommercial-1.0.0
author: "丰泽AI"
category: education
visibility: "public"
homepage: https://github.com/magicjacky/k12-lesson-studio
description: "中小学全学科课件一键制作（K12 Lesson Studio v5.1，全包体积 < 0.90 MB）。通过统一命令行入口 k12_studio.py 串联中小学全学科 5 步高准确度备课闭环：(1) 真教材 PDF 电子版/扫描版自动识别、书签节选与禁超纲红线清单；(2) 整章课时规划与带课堂高频卡壳救场表的打印版 Word 教案；(3) 视觉零重复希沃可编辑 11 页 PPT（自动居中裁切不拉伸 + 全学科原生矢量流程图/对比卡/概念中枢/几何光路蓝图 + Three.js 代码渲染 0 角标带声 3D 视频 + SHA-256 防重复与防重叠验真）；(4) 断网单文件全学科主题 3D 互动剧场与全班 4 队光影柱 PK 网页；(5) 单源 JSON 验算 100 分学生作答卷（带虚线答题栏）与教师红笔解析卷、批量阅卷诊断及 2 页错题急救小卡。触发词：备课、写教案、做课件、授课PPT、3D演示视频、课堂互动HTML、出测试卷、批量改卷、错题急救卡、中小学全学科课件一键制作、k12-lesson-studio。"
description_zh: "输入真教材 PDF（兼容电子版与扫描件），一句话跑通教案、视觉零重复希沃 PPT、Three.js 3D 代码演示视频、断网大屏互动 PK 网页、红笔解析试卷与错题急救卡，中小学全学科通用"
description_en: "Turn any K12 textbook PDF (electronic or scanned) into verified lesson plans, zero-duplicate all-subject editable PPTX decks, deterministic Three.js 3D videos, offline interactive 3D classroom PK HTML labs, red-ink teacher exams, and remediation cards"
examples_zh:
  - "用中小学全学科课件一键制作技能，帮我核对这本六年级数学教材的《圆柱与圆锥》单元，出整章课时规划和打印版教案"
  - "按刚才定好的教案，做一套 11 页视觉不重复的希沃可编辑 PPT，并用 Three.js 代码引擎生成一段 3D 演示视频嵌进第 4 页"
  - "帮我做一个断网能直接双击打开的教室大屏 3D 互动与 4 队抢答 PK 网页，再出一份 100 分随堂双卷并批改课后测试文件夹里的答卷"
examples_en:
  - "Use K12 Lesson Studio to verify this textbook unit PDF and generate a unit pacing plan plus printable lesson plan DOCX"
  - "Build a zero-duplicate 11-slide editable PPTX deck with all-subject vector diagrams and an embedded Three.js 3D teaching video"
  - "Create an offline single-file 3D interactive classroom lab with 4-team PK mode, a verified 100-point student/teacher exam pair, and remediation cards"
---

# 中小学全学科课件一键制作（K12 Lesson Studio v5.1 · 全学科统一 CLI 版）

> **最高优先级铁律：第一优先永远是「内容、算式、几何、物理、课文 100% 准确」；第二优先才是「视觉高级、丰富多样、绝不撞脸」。**
> 本技能通过统一入口 `k12_studio.py` 驱动全栈轻量底盘（全包 < 0.90 MB，零 `npm` 安装依赖）：支持**电子版/扫描版教材自动识别与拼图提取**、**全学科原生可编辑 PPT 矢量图解与版式库（`scripts/ppt_kit.py`）**、**Three.js 全学科 3D 代码视频引擎（`assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`）**、**全学科主题离线互动剧场（`assets/theater_base.html` + `scripts/build_html.py`）** 及 **单源双卷/红笔解析导出与静态验真器**。严禁调用 AI 视频生成工具（`VideoGen`），所有教学演示视频一律使用内置 Three.js 引擎代码渲染直出！

## 0. 自动环境体检与依赖补齐（首次运行自动执行，零命令行门槛）

首次在当前电脑运行前，先执行 1 秒体检（纯标准库实现，未装第三方包也能正常返回 JSON）：

```bash
python "{skill_dir}/k12_studio.py" doctor
```

- 若 `ok` 为 `true`，直接跳过安装进入正式步骤；
- 若 `ok` 为 `false`，直接代用户执行清华镜像加速安装（自动回退官方 PyPI，无需手动开终端）：

```bash
python "{skill_dir}/k12_studio.py" setup --mirror
```

---

## 一、全流程铁律（语数英理化生史地道法通用，每步必守）

0. **全学科自动适配 + 大白话自动扩写**
   - 接到任务先识别学科与学段，查阅 `references/subject-playbooks.md`，自动匹配专属色彩主题（`math` / `chinese` / `english` / `science` / `physics` / `chemistry` / `biology` / `history` / `geography`）、4 槽位差异化视觉题材、Three.js 3D 场景基元、学科防错红线与互动原型。
   - **绝不把简短大白话直接转发给生图或代码生成**：必须先按参考规范扩写为 6 段生图公式、确定性 Three.js 分镜脚本或带几何/科学不变量合同的互动配置。
1. **真教材为准（兼容电子版与纯图片扫描版），严禁超纲与数值矛盾**
   - 凡 `01-教材/` 下已有 PDF，先调用 `k12_studio.py scan-pdf` 与 `extract-pdf` 提取书签目录、审定年份与章节页。若检测到扫描版页面，脚本会自动渲染高清页面图与拼图总览 `<work_dir>/scanned_pages/pages_contact_sheet.png` 供视觉核对原文、插图与留白，按 `references/lesson-and-exam-templates.md` 固定 6 段输出 `01-教材/教材核验清单.md`。
   - 若缺教材 PDF，提示用户在技能市场安装「国家中小学智慧教育平台资源下载」获取正版教材，或直接拖入本地 PDF。
   - **学段边界与单一数据源**：小学数学严禁引入方程与超纲公式；语文古诗文与生字注音逐字核对教材；物理光路/受力、化学配平严格自洽；试卷、教案答案、HTML 题卡与阅卷统计必须由单源数据导出并断言验算。
2. **PPT 视觉零重复 + 全学科原生矢量图解 + 希沃全可编辑底线**
   - 整套 PPT 最多调用 `ImageGen` 生成 **3–4 张题材、材质、光影完全不同的无字主视觉**（插入时统一调用 `add_picture_cover()` 自动居中裁切，绝不拉伸变形）；**严禁同一张图重复贴到两页！**
   - 脉络流程、正反对比、核心意象中枢、几何/光学/电路蓝图、3 列梯度练兵、2×2 避坑矩阵与 40:60 原生汇总表一律使用 `scripts/ppt_kit.py` 原生可编辑矢量与版式组件构建。
   - 生成后必跑 `python "{skill_dir}/k12_studio.py" audit-pptx "<out_dir>/deck.pptx" --render-sheet "<work_dir>/ppt_sheet.png"`（强校验 0 占位符、全页讲稿备注、0 越界、0 重叠、**0 重复图片**、内嵌视频非空）。
3. **教学演示视频一律采用 Three.js 代码渲染（禁用 `VideoGen`！）**
   - 所有动态原理演示均在工作空间临时目录编写精简场景脚本 `<work_dir>/scene.js`，调用 `video_stage.html` 内置的全学科 3D 基元（器皿倾倒、激光光路与透镜、3D 球棍分子、血管/水循环粒子流管道、三维力矢量箭头），通过 `k12_studio.py render-video` 离线直出 1280×720 30fps 带拟声音频 MP4、封面帧、轻量化 HTML 内嵌版 MP4 与 4×4 总览图。
4. **诚实边界与无 Git 纪律**
   - 模拟样卷须如实注明；真实手写拍照卷须提醒教师人工抽检；全程禁止执行任何 `git` 命令；每步脚本验真 + 1 张拼图总览肉眼复核无硬伤即交付。

---

## 二、标准本地工作空间目录结构

```text
当前工作空间/
├─ 01-教材/           # 正版教材 PDF、本章节选 PDF、教材核验清单.md（固定 6 段）
├─ 02-教案/           # 整章课时规划（2 页）与分课时教案（3–4 页，含高频卡壳救场表）
├─ 03-授课PPT/        # 单页试水稿 + 11 页视觉零重复可编辑定稿 .pptx（内嵌 Three.js 视频与讲稿备注）
├─ 04-大屏互动HTML/   # 单文件离线双模式大屏互动网页 .html（实时 3D + 内嵌视频 + 4 队 PK）
├─ 演示视频/          # 内置 Three.js 引擎代码渲染的高清带声 1280×720 30fps MP4（0 角标）
└─ 05-课后测改补/     # 学生作答卷/教师红笔解析卷 .docx、课后测试/、阅卷诊断报告、错题急救小卡与3级变式题.docx
```

---

## 三、五步标准工作流（按用户当前一句话自动路由）

### 步骤 1：教材核验与章节提取（电子版 + 扫描件双兼容）
```bash
python "{skill_dir}/k12_studio.py" scan-pdf "<input.pdf>" --keyword "<单元关键词>"
python "{skill_dir}/k12_studio.py" extract-pdf "<input.pdf>" --start 18 --end 40 --out-pdf "01-教材/<本章节选>.pdf" --out-txt "<work_dir>/chapter_raw.txt"
```
- 若返回 `scanned_pages_detected` 非空，直接用 `ViewImage` 查看自动生成的 `<work_dir>/scanned_pages/pages_contact_sheet.png` 核对原页内容，按 `references/lesson-and-exam-templates.md` 第一节输出 `01-教材/教材核验清单.md`。

### 步骤 2：教学评一致性教案（整章规划 + 分课时打印稿）
- 按 `references/lesson-and-exam-templates.md` 第二节编写 Markdown（含分钟节奏表、板书方框、≥5 条课堂高频卡壳救场表与验算答案），调用统一命令导出紧凑 A4 Word：
```bash
python "{skill_dir}/k12_studio.py" docx "<work_dir>/lesson_plan.md" "02-教案/<课题>_教案.docx" --compact
```

### 步骤 3：11 页视觉零重复授课 PPT（`scripts/ppt_kit.py` + 差异化 `ImageGen` + Three.js 代码视频直嵌）
1. 阅读 `references/themes.md`、`references/media-prompt-engineering.md` 与 `references/subject-playbooks.md`，确立 11 页分镜矩阵（除用户明确直接出整套外，默认先出 1 页核心页定风格）。
2. **先渲染 Three.js 3D 代码演示视频（禁止调用 `VideoGen`！）**：
   - 在临时目录编写 `<work_dir>/scene.js`（130–240 行，直接调用 `helpers` 内置器皿/光学/分子/流道/矢量组件与左上 `drawMetricCard`），一键同时产出 PPT 高清版、HTML 轻量版、封面帧与 4×4 总览图：
     ```bash
     python "{skill_dir}/k12_studio.py" render-video --scene "<work_dir>/scene.js" --out "演示视频/<课题>_3D代码演示.mp4" --compact-out "<work_dir>/video_compact.mp4" --poster "<work_dir>/video_poster.png" --poster-sec 8.5 --contact-sheet "<work_dir>/video_sheet.png"
     ```
   - 用 `ViewImage` 检查 1 张 `<work_dir>/video_sheet.png` 确认物理精准无穿模后进入生图与拼装。
3. **精简生成 3–4 张「视觉世界完全不同」的 `ImageGen` 无字主图**（按 `references/media-prompt-engineering.md` 6 段公式：P01 暗调封面、P02 明亮日光实景、P06 暖白台面对比器物、P11 全息舞台或地标实景）。
4. **复用 `scripts/ppt_kit.py` 拼装 11 页 `.pptx`**：
   - 图文跨页调用 `add_hero_slide()` / `add_split_visual_slide()`（自动居中裁切不拉伸）与 `add_video_slide()`；
   - 原理推演、脉络对比与例题蓝图按学科调用原生矢量组件：`add_process_timeline_card()`、`add_comparison_matrix_card()`、`add_concept_hub_card()`、`add_subject_blueprint_card()`（立体几何亦可调 `add_equal_base_height_gauge()`、`add_three_to_one_derivation_graphic()`、`add_cone_blueprint_card()`）；
   - 练习、避坑与小结页直接调用 `add_tiered_practice_slide()`、`add_pitfall_matrix_slide()`、`add_summary_table_slide()`。
5. **强制双重验收**：运行 `python "{skill_dir}/k12_studio.py" audit-pptx "03-授课PPT/<课件>.pptx" --render-sheet "<work_dir>/ppt_sheet.png"`，确认 `passed: true`、`duplicate_images: []`、`text_overlaps: []`，并用 `ViewImage` 核验 1 张 `<work_dir>/ppt_sheet.png`。

### 步骤 4：单文件离线「3D 教室大屏互动剧场 HTML」（复用 `assets/theater_base.html`）
1. 阅读 `references/interactive-html-blueprint.md` 与 `assets/theater_config.schema.json`，在临时目录生成通过验算的 `<work_dir>/theater_config.json`（设置学科主题 `"theme": "math"|"chinese"|"english"|"science"|"biology"|"history"` 与 4 队 PK 题库）和 `<work_dir>/theater_scenes.js`（250–420 行）。
2. 一键拼装并执行无头浏览器全自动点击与零溢出验收：
```bash
python "{skill_dir}/k12_studio.py" build-html --config "<work_dir>/theater_config.json" --scenes "<work_dir>/theater_scenes.js" --video "<work_dir>/video_compact.mp4" --poster "<work_dir>/video_poster.png" --out "04-大屏互动HTML/<课题>_大屏互动实验室.html"
python "{skill_dir}/k12_studio.py" audit-html "04-大屏互动HTML/<课题>_大屏互动实验室.html" --shots-dir "<work_dir>/html_shots"
```
3. 用 `ViewImage` 检查 1 张 `<work_dir>/html_shots/audit_contact_sheet.png` 确认几何与算式准确无遮挡后交付。

### 步骤 5：单源防幻觉双卷 → 批量阅卷诊断 → 2 页错题急救小卡
- 参照 `assets/exam_spec.schema.json` 与 `references/lesson-and-exam-templates.md` 第三节生成 `<work_dir>/exam_spec.json`，一条命令校验总分 `== 100` 并**同源导出**学生卷与教师红笔卷 Markdown，再转 Word（学生卷自动带 `[试卷抬头]` 与虚线 `[答题线:N]` 且防漏答案；教师卷自动红字高亮 `【答案】`/`【解析】`/`【评分标准】`）：
```bash
python "{skill_dir}/k12_studio.py" verify-exam "<work_dir>/exam_spec.json" --export-student-md "<work_dir>/exam_student.md" --export-teacher-md "<work_dir>/exam_teacher.md"
python "{skill_dir}/k12_studio.py" docx "<work_dir>/exam_student.md" "05-课后测改补/<课题>_学生测试卷.docx" --mode student --compact
python "{skill_dir}/k12_studio.py" docx "<work_dir>/exam_teacher.md" "05-课后测改补/<课题>_教师解析卷.docx" --mode teacher --compact
```
- 批改答卷时将逐题得分与错因写入 `<work_dir>/grading_records.json`，运行 `k12_studio.py verify-grading` 单源聚合平均分、中位数与错因占比，导出诊断报告及带 `[分页]` 裁剪排版的 2 页 `05-课后测改补/错题急救小卡与3级变式题.docx`（`--mode card`）。

---

## 四、内置底盘、Schema 与参考文档索引（全包 < 0.90 MB）

- `k12_studio.py` + `scripts/doctor.py`：统一命令行单入口、环境自检、镜像装包与静态资产包完整性自检（`package-audit`）
- `assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`：全学科 Three.js 确定性代码视频与拟声音频合成引擎（支持器皿倾倒、激光透镜光路、3D 球棍分子、血管/水循环粒子管道、力矢量箭头与轻量双轨导出）
- `assets/theater_base.html` + `assets/theater_config.schema.json` + `scripts/build_html.py` + `scripts/audit_html.mjs`：全学科主题离线互动剧场底盘、配置 Schema、拼装器与无头浏览器自动验收器
- `scripts/ppt_kit.py` + `scripts/audit_pptx.py`：全学科 16:9 可编辑 PPT 版式与原生矢量图解库 + 重复图片 SHA-256 拦截与版面验收器
- `scripts/extract_textbook.py` / `scripts/md_to_docx.py` / `scripts/verify_exam.py` + `assets/exam_spec.schema.json`：电子/扫描教材提取、红笔双卷/急救卡 Word 转换与单源试卷阅卷验算引擎
- `references/`：`media-prompt-engineering.md`、`themes.md`、`subject-playbooks.md`、`interactive-html-blueprint.md`、`lesson-and-exam-templates.md`
