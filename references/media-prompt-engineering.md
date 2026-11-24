# 多媒体视觉多样化（`ImageGen`）与 Three.js 全学科代码视频（`render_video.mjs`）规范（v5.1）

> 核心理念：
> 1. **教学动态演示视频严禁使用 AI 视频工具（如 `VideoGen`）！** 一律使用本技能内置的 **Three.js 确定性代码视频引擎（`assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`）** 逐帧渲染 1280×720 30fps 带拟声音频的高清 MP4——100% 严守数学/物理/化学守恒、零 AI 穿帮变形、零角标、30 秒本机直出。
> 2. **PPT 配图严禁重复、严禁同质化棚拍堆砌！** 整套 11 页课件最多生成 **3–4 张题材、景别、光影完全不同** 的 `ImageGen` 无字主视觉（经 `add_picture_cover()` 自动居中裁切零拉伸）；其余页面一律使用 `scripts/ppt_kit.py` 全学科原生矢量图解与瑞士排版（`scripts/audit_pptx.py` 硬性拦截 SHA-256 重复图片）。

---

## 一、PPT 配图「4 槽位视觉防重复矩阵」与 `ImageGen` 6 段提示词公式

| 槽位 | 所在页 | 视觉世界与光影情绪（彼此必须显著区分） | 严禁雷同点 |
|---|---|---|---|
| **主图 1 · 电影封面** | P01 | 深色焦点棚拍或宋画/暗室光学雕塑封面（主体严锁右 48%，左 48% 干净留白） | 仅 P01 使用暗调封面静物 |
| **主图 2 · 真实生活现场** | P02 | 明亮自然日光纪实/户外实景（粮仓沙堆、彩虹桥梁、植物生态、历史遗迹、生活场景） | 必须明亮自然光，严禁暗黑棚拍 |
| **主图 3 · 反例/冲突对比** | P06 | 明亮暖象牙白/浅灰博物馆顶光微距，采用彩陶/彩色亚克力/实验对比器物形成强反差 | 严禁重复 P01 材质与暗色背景 |
| **主图 4 · 课堂剧场/拓展收官** | P11 | 等轴测全息课堂交互沙盘或真实建筑/科学地标摄影 | 严禁重复 P01 静物构图 |

> **P03（探究/脉络）、P05（核心推导/概念中枢）、P07（例题/结构精讲）一律不贴 AI 照片**，直接调用 `scripts/ppt_kit.py` 原生可编辑矢量组件（`add_process_timeline_card`、`add_comparison_matrix_card`、`add_concept_hub_card`、`add_subject_blueprint_card` 或立体几何专属组件）！

### `ImageGen` 每张图必填 6 段提示词公式
```text
[1. 镜头与单幅构图约束] ONE single continuous unbroken scene — STRICTLY NO split-screen, NO diptych border, NO collage frames.
[2. 主体学科形态精确锚定] 写死不可出错的几何/物理/器物/时代细节（如圆锥针尖锐顶、凸透镜双凸曲率、宋代服饰器物准确）。
[3. 材质、布光与差异化色温锁定] 按 4 槽位锁定自然日光 / 暖白顶光 / 暗室激光 / 宋画宣纸光感，杜绝塑料感同质化。
[4. PPT 原生排版安全负空间配比] 封面主体锁右 48%、左 48% 净留白；半幅插图四周留安全余量防裁切。
[5. 干净无杂物约束] Zero extra props, zero floating hands, zero cartoon outlines, zero clipart look.
[6. 零文字硬负向约束] Strictly NO text, NO letters, NO numbers, NO formulas, NO arrows, NO logos, NO watermarks anywhere.
```

---

## 二、Three.js 全学科代码驱动教学视频规范（`k12_studio.py render-video`）

### 1. 内置全学科 3D 实验与可视化基元速查（`ctx.helpers`，编写 `<work_dir>/scene.js` 直接调用）
1. **舞台灯光、背景主题与桌面**：
   - `registered.theme` 支持 5 套学科背景：`'obsidian'`（数学深海曜石）、`'laser'`（理化暗室光学）、`'emerald'`（生物显微深翠）、`'ink'`（语文/史地宋画青绿墨韵）、`'linen'`（明亮暖亚麻）。
   - `helpers.setupStudioLights({ theme })`、`helpers.makeMarbleTable(w, d, dark)`。
2. **数学 / 化学透明量器与倾倒粒子流**：
   - `helpers.createCrystalCylinder({ radius, height, ringFractions })` → `.setFill(frac, moundAmp)`、`.setRingGlow(idx, flash)`
   - `helpers.createCrystalConeVessel({ radius, height, x, z })` → `.setFill(remFrac)`（玻璃壳刚性不变，内部按立方根守恒缩放）、`.solvePourPose(targetSpoutVec3, tiltRad)`
   - `helpers.createPourStream({ count, color })` → `.update(active, startVec, endVec, t, flowEnv)`
3. **物理光学与力学矢量基元**：
   - `helpers.createLaserBeam({ points, color, radius, glowOpacity })` → `.setPoints([v0, v1, v2, ...])`（多段准直高光激光束，精确演示反射定律、斯涅尔折射、全反射与透镜聚焦）
   - `helpers.createOpticalElement({ kind: 'convex'|'concave'|'prism'|'mirror', width, height, depth, x, y, z })`
   - `helpers.create3DArrow({ from, to, color, shaftRadius, headLength })` → `.setEndpoints(fromVec, toVec)`（三维受力分析、速度合成、空间坐标轴）
4. **化学微观球棍分子基元**：
   - `helpers.createMolecule({ atoms: [{x,y,z,radius,color}], bonds: [[0,1], ...] })` → `.setAtomPos(idx, vec3)`（键轴自动跟随两端原子实时旋转伸缩！）、`.setBondOpacity(idx, alpha)`（化学键断裂与重组动画）
5. **生物 / 地理 / 电学三维流道粒子基元**：
   - `helpers.createFlowPath({ points, closed, tubeRadius, tubeColor, particleCount, particleColor })` → `.update(t, speed, activeFrac)`（半透明三维平滑管道 + 高亮流动粒子群，适用于体肺血液循环、叶脉光合运输、地理水循环水汽河流、闭合电路电流）
6. **2D 高清数据与公式 HUD（零遮挡安全布局）**：
   - `helpers.project(vec3)`（3D 坐标转屏幕像素）、`helpers.hud.drawHeader(eyebrow, title, pill)`、`helpers.hud.drawMetricCard(42, 102, 320, 106, ...)`（固定左上角）、`helpers.hud.drawFormulaBanner(42, 102, 540, 104, ...)`（出现时替换左上数据卡，绝不叠画）、`helpers.hud.drawCallout(...)`、`helpers.hud.drawSubtitle(...)`。
7. **确定性纯函数与拟声音效（`audioCues`）**：
   - `renderFrame(ctx, frame, t, duration, progress)` 严禁调 `Math.random()`（统一用 `ctx.seededRng()`）；`audioCues` 支持 `'pour'`、`'water'`、`'whoosh'`、`'chime'`、`'fanfare'` 自动合成 44.1kHz 音轨。

### 2. 一键双轨渲染与单图 16 帧验收
```bash
python "{skill_dir}/k12_studio.py" render-video \
  --scene "<work_dir>/scene.js" \
  --out "演示视频/<课题>_3D代码演示.mp4" \
  --compact-out "<work_dir>/video_compact.mp4" \
  --poster "<work_dir>/video_poster.png" \
  --poster-sec 8.5 \
  --contact-sheet "<work_dir>/video_sheet.png"
```
- 一步同时产出 PPT 高清内嵌版 MP4、离线 HTML 轻量化 `960×540` MP4、高清封面帧与 4×4 16 格总览图；仅用 `ViewImage` 检查 1 张 `<work_dir>/video_sheet.png` 无穿模无遮挡后立即推进下一步。
