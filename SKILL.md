---
name: k12-lesson-studio
display_name: "中小学全学科课件一键制作"
display_name_en: "K12 Lesson Studio — All-Subject Teaching Prep"
version: "5.0.1"
license: PolyForm-Noncommercial-1.0.0
author: "丰泽AI"
category: education
visibility: "public"
homepage: https://github.com/magicjacky/k12-lesson-studio
description: "中小学全学科课件一键制作（K12 Lesson Studio v5.0，全包体积 < 0.85 MB）。输入正版教材 PDF 或课题，一句话串联完成 5 步高准确度备课闭环：(1) 真教材 PDF 版本核验与原页节选及禁超纲红线清单；(2) 整章课时规划与带课堂高频卡壳救场表的打印版 Word 教案；(3) 视觉零重复希沃可编辑 11 页 PPT（4 槽位差异化无字大片 + 原生矢量蓝图 + 内置 Three.js 代码渲染 0 角标带声 3D 演示视频 + SHA-256 防重复与防重叠自动验真）；(4) 断网单文件 3D 大屏互动实验与全班 4 队光影柱 PK 网页；(5) Python 验算 100 分学生/教师 Word 试卷、批量阅卷诊断与 1 页错题急救小卡 + 3 级变式题。触发词：备课、写教案、做课件、授课PPT、3D演示视频、课堂互动HTML、出测试卷、批量改卷、错题急救卡、中小学全学科课件一键制作、k12-lesson-studio。"
description_zh: "输入真教材 PDF，一句话跑通教案与课堂救场表、视觉零重复可改希沃 PPT、Three.js 3D 代码演示视频、断网大屏互动 PK 网页、防幻觉试卷与错题急救卡，中小学全学科通用"
description_en: "Turn any K12 textbook PDF into verified lesson plans, zero-duplicate editable PPTX decks, deterministic Three.js 3D teaching videos, offline interactive 3D classroom PK HTML labs, verified exams, and remediation cards"
examples_zh:
  - "用中小学全学科课件一键制作技能，帮我核对这本六年级数学教材的《圆柱与圆锥》单元，出整章课时规划和打印版教案"
  - "按刚才定好的教案，做一套 11 页视觉不重复的希沃可编辑 PPT，并用 Three.js 代码引擎生成一段圆锥倒沙 3D 演示视频嵌进第 4 页"
  - "帮我做一个断网能直接双击打开的教室大屏 3D 互动与 4 队抢答 PK 网页，再出一份 100 分随堂卷并批改课后测试文件夹里的答卷"
examples_en:
  - "Use K12 Lesson Studio to verify this textbook unit PDF and generate a unit pacing plan plus printable lesson plan DOCX"
  - "Build a zero-duplicate 11-slide editable PPTX deck with an embedded Three.js code-rendered 3D science/math demonstration video"
  - "Create an offline single-file 3D interactive classroom lab with 4-team PK mode, a verified 100-point test, and remediation cards"
---

# 中小学全学科课件一键制作（K12 Lesson Studio v5.0 · 准确第一 × Three.js 代码视频 × 视觉零重复版）

> **最高优先级铁律：第一优先永远是「内容、算式、几何、物理 100% 准确」；第二优先才是「视觉高级、丰富多样、绝不撞脸」。**
> 本 Skill 已内置轻量级全栈工程底盘（全包总体积 < 0.85 MB，零 `npm` 安装依赖）：**环境自检器（`scripts/doctor.py`）**、**Three.js 确定性代码视频引擎（`assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`）**、**PPT 视觉零重复杂志与矢量图解库（`scripts/ppt_kit.py`）**、**全学科离线互动剧场引擎（`assets/theater_base.html` + `scripts/build_html.py`）** 与 **全套自动验收脚本**。严禁调用 AI 视频生成工具（`VideoGen`），所有教学演示视频一律用内置 Three.js 引擎代码渲染直出！

## 0. 自动环境体检与依赖补齐（首次运行自动执行，零命令行门槛）

首次在当前电脑运行前，先执行 1 秒体检（纯标准库实现，未装第三方包也能正常返回 JSON）：

```bash
python "{skill_dir}/scripts/doctor.py" doctor
```

- 若 `ok` 为 `true`，直接跳过安装进入正式步骤；
- 若 `ok` 为 `false`，请直接代用户执行镜像加速安装（无需让用户手动开终端）：

```bash
python "{skill_dir}/scripts/doctor.py" setup --mirror
```

*(自动安装 `pymupdf`、`python-docx`、`python-pptx`、`pillow`，优先清华镜像并自动回退 PyPI；3D 代码视频渲染与 HTML 自动验收复用本机 Chrome/Edge、Node.js 与 `ffmpeg`，无需安装任何 `npm` 依赖包。)*

---

## 一、全流程铁律（全学科通用，每步必守）

0. **全学科自动适配 + 大白话自动扩写**
   - 接到任务先识别学科与学段，查阅 `{skill_dir}/references/subject-playbooks.md`，匹配专属策展主题、差异化视觉题材、3D 代码视频选题、防错红线与互动原型。
   - **绝不把简短大白话直接转发给生图或代码生成**：必须先按参考规范扩写为 6 段生图公式、确定性 Three.js 分镜脚本或带数学不变量合同的互动蓝图。
1. **真教材为准，严禁超纲与数值矛盾**
   - 凡 `01-教材/` 下已有 PDF，先调用 `scripts/extract_textbook.py` 实地读取目录、版本、例题、图注与留白，按 `references/lesson-and-exam-templates.md` 固定 6 段格式生成 `教材核验清单.md`。
   - 若缺教材 PDF，提示用户在 WorkBuddy 技能市场安装「国家中小学智慧教育平台资源下载」技能获取正版教材，或直接拖入本地 PDF。
   - **学段边界与单一数据源**：小学数学严禁引入方程与未学公式；试卷、教案答案、HTML 公式卡与阅卷统计数必须由 Python/JS 单源计算并断言验算。
2. **PPT 视觉零重复 + 希沃全可编辑底线**
   - 整套 PPT 最多调用 `ImageGen` 生成 **3–4 张题材、材质、光影完全不同的无字主视觉**；**严禁同一张图重复贴到两页，严禁连续多页堆砌相似暗黑玻璃静物！** 探究标尺、公式推演、教材例题蓝图一律用 `ppt_kit.py` 原生矢量组件构建。
   - 全部教学标题、公式、步骤、标注与表格 100% 为 PPT 原生可编辑对象；生成后必跑 `py {skill_dir}/scripts/audit_pptx.py <pptx> --render-sheet .build/ppt_contact_sheet.png`（强制校验 0 占位符、全页 Notes、0 越界、0 重叠、**0 重复图片**、内嵌视频非空）。
3. **教学演示视频一律采用 Three.js 代码渲染（禁用 `VideoGen`！）**
   - 严禁调用 WorkBuddy 内置 `VideoGen` 生成教学视频（杜绝物理变形、刻度误差、AI 角标与漫长云端排队）。
   - 所有动态演示视频均编写精简 Three.js 场景脚本 `.build/video_scene.js`（180–320 行），运行 `node {skill_dir}/scripts/render_video.mjs` 离线直出 1280×720 30fps 带拟声音频的 H.264 MP4 + 封面帧 PNG + 1 张 4×4 16 格 `contact_sheet.png`，肉眼检查 1 张总览图确认无穿模无遮挡后直嵌 PPT 与 HTML。
4. **诚实边界与无 Git 纪律**
   - 模拟样卷须如实注明；真实手写拍照卷须提醒教师人工抽检；禁止执行任何 `git` 命令；每步脚本验真 + 1 轮单图总览肉眼复核无硬伤即交付，不无意义空转。

---

## 二、标准本地工作空间目录结构

```text
当前工作空间/
├─ 01-教材/           # 正版教材 PDF、本章原页节选 PDF、教材核验清单.md（固定 6 段）
├─ 02-教案/           # 整章课时规划（2页）与分课时教案（3–4页，含高频卡壳救场表）.md/.docx
├─ 03-授课PPT/        # 单页试水稿 + 11 页视觉零重复可编辑定稿 .pptx（内嵌 Three.js 视频与 Notes）
├─ 04-大屏互动HTML/   # 单文件离线双模式大屏互动网页 .html（实时 3D + 内嵌 Three.js 视频 + 4 队 PK）
├─ 演示视频/          # 内置 Three.js 引擎代码渲染的高清带声 1280×720 30fps MP4（0 角标）
└─ 05-课后测改补/     # 学生卷/教师卷 .docx、课后测试/、程序化阅卷诊断报告、错题急救小卡与3级变式题 .docx
```

---

## 三、五步标准工作流（按用户当前一句话自动路由）

### 步骤 1：教材核验与章节提取
- 运行 `{skill_dir}/scripts/extract_textbook.py` 核验 `01-教材/` PDF 版本、审定年份与起止页，无损导出本章节选 PDF，按 `references/lesson-and-exam-templates.md` 第一节固定 6 段输出 `01-教材/教材核验清单.md`。

### 步骤 2：教学评一致性教案（整章规划 + 分课时打印稿）
- 读取 `教材核验清单.md`，按 `references/lesson-and-exam-templates.md` 第二节产出 `整章课时规划.md/.docx`（2 页 A4）与核心课时教案 `.md/.docx`（3–4 页 A4，`scripts/md_to_docx.py --compact`，必含分钟节奏表、板书、≥5 条卡壳救场表与 Python 验算随堂题答案）。

### 步骤 3：11 页视觉零重复电影杂志级授课 PPT（`ppt_kit.py` + 差异化 `ImageGen` + Three.js 代码视频直嵌）
1. 阅读 `{skill_dir}/references/themes.md`、`references/media-prompt-engineering.md` 与 `references/subject-playbooks.md`，确立 11 页「视觉零重复」分镜矩阵（除用户明确直接出整套外，默认先出 1 页核心页定风格）。
2. **先生成 Three.js 3D 代码演示视频（禁止调用 `VideoGen`！限 1 次渲染检查，勿空转）**：
   - 编写精简 `.build/video_scene.js`（控制在 130–220 行内，直接调用 `helpers.createCrystalCylinder / createCrystalConeVessel / createPourStream / hud.drawMetricCard` 与精确 `solvePourPose()`，确保玻璃壳刚性不缩小、开口倾倒对准中心、左上数据卡零遮挡、含拟声音频 `audioCues`）。
   - 运行一键渲染并同时产出封面帧与 4×4 16 帧总览图：
     ```bash
     node "{skill_dir}/scripts/render_video.mjs" --scene .build/video_scene.js --out "演示视频/<课题>_3D代码演示.mp4" --poster .build/video_poster.png --poster-sec 8.5 --contact-sheet .build/video_contact_sheet.png
     ```
   - 仅用 `ViewImage` 检查 1 张 `.build/video_contact_sheet.png`，确认物理精准无穿模后**立刻进入第 3 步生图与 PPT 拼装**（严禁抽多张单帧反复微调耗尽轮数）。
3. **精简生成 3–4 张「视觉世界完全不同」的 `ImageGen` 无字主图**（用 `ToolSearch` 加载 `ImageGen`，严格按 `references/media-prompt-engineering.md` 6 段公式与 4 槽位差异化矩阵：P01 暗调雕塑封面、P02 明亮自然日光生活实景、P06 暖白顶光彩陶/彩色教具反例图、P11 全息舞台或地标建筑；**严禁多页重复深色大理石玻璃杯**）。
4. **复用 `{skill_dir}/scripts/ppt_kit.py` 拼装 11 页 `.pptx`**：
   - P03 用 `add_equal_base_height_gauge()` 原生矢量等底等高标尺图（不放 AI 照片）；
   - P04 用 `add_video_slide()` 离线内嵌刚渲染好的 Three.js MP4 与 `.build/video_poster.png`；
   - P05 用 `add_three_to_one_derivation_graphic()` 原生矢量三锥映射三层圆柱图解（绝不复用 P04 截图）；
   - P07 用 `add_cone_blueprint_card()` 原生矢量标注蓝图（绝不复用 P02 沙堆图！）；
   - 全部 11 页带原生淡出转场与完整教师讲稿备注。
5. **强制双重验收**：运行 `py {skill_dir}/scripts/audit_pptx.py <pptx> --render-sheet .build/ppt_contact_sheet.png`（确认 `passed: true`、`duplicate_images: []`、`text_overlaps: []`、`videos` 非空），仅用 `ViewImage` 检查这 1 张 `.build/ppt_contact_sheet.png` 无误后交付。

### 步骤 4：动效视频级单文件离线「3D 教室大屏互动剧场 HTML」（复用 `theater_base.html` + `build_html.py`）
1. 阅读 `{skill_dir}/references/interactive-html-blueprint.md`，**严禁从零手敲整份 2,000+ 行 HTML/CSS/弹窗/PK 脚手架**，强制复用 `{skill_dir}/assets/theater_base.html` 与 `{skill_dir}/scripts/build_html.py`。
2. 编写精简的 `.build/make_config.py`（≤ 120 行，含 Python 公式与题库断言）与 `.build/theater_scenes.js`（280–450 行，严守几何不变量与单源算式）。
3. 若步骤 3 已生成 Three.js 代码演示视频，用 `ffmpeg` 压一份约 0.9–1.4 MB 的 `960×540` 轻量化 MP4 传入 `build_html.py --video <compact.mp4> --poster <poster.png>` 自动 base64 内嵌为第 4 个离线视频分镜。
4. 运行 `node {skill_dir}/scripts/audit_html.mjs <html路径> .build/audit_shots`（校验 0 外链、0 报错、1280×720 零溢出、`<video>` 就绪、弹窗全可点，并拼出 1 张 4×4 `audit_contact_sheet.png`），用 `ViewImage` 看这 1 张总览图核验无误后交付。

### 步骤 5：防幻觉出卷 → 程序化批量阅卷诊断 → 错题急救小卡与 3 级变式题
- 按 `references/lesson-and-exam-templates.md` 第三节，先跑 Python 断言校验总分 `== 100` 与每题纯学段答案，输出学生卷（2 页）与教师卷（3 页）；批改 `05-课后测改补/课后测试/` 时由 Python 结构化统计杜绝表文矛盾，产出 4 页诊断报告与 2 页 A4 `错题急救小卡与3级变式题.docx`。

---

## 四、内置底盘、参考文档与自动化验真工具索引（全包 < 1 MB）

- `assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`：**零依赖 Three.js 确定性代码视频渲染与拟声音频合成引擎**（1280×720 30fps H.264+AAC MP4 + 封面帧 + 4×4 16 格总览图，0 角标）
- `assets/theater_base.html` + `scripts/build_html.py`：**全学科已验证离线互动剧场引擎底盘与单文件拼装器**
- `scripts/ppt_kit.py`：**16:9 博物馆杂志可编辑 PPT 拼装与原生矢量图解库**（含封面、离线视频页、等底等高标尺、三锥映射推导图、建筑标注蓝图、原生转场与讲稿备注）
- `scripts/audit_pptx.py` / `scripts/audit_html.mjs`：PPTX（含**重复图片 SHA-256 拦截**、0 重叠、视频检测与 LibreOffice 单图总览）与 HTML 全自动验收脚本
- `scripts/extract_textbook.py` / `scripts/md_to_docx.py`：真教材提取与 A4 Word 转换引擎
- `references/`：`media-prompt-engineering.md`、`themes.md`、`subject-playbooks.md`、`interactive-html-blueprint.md`、`lesson-and-exam-templates.md`
