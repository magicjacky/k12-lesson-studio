# 多媒体视觉多样化（`ImageGen`）与 Three.js 代码驱动教学视频（`render_video.mjs`）工程规范（v5.0）

> 核心理念：
> 1. **教学动态演示视频严禁使用 AI 文生/图生视频工具（如 `VideoGen`）！** 一律使用本 Skill 内置的 **Three.js 确定性代码视频引擎（`assets/three.min.js` + `assets/video_stage.html` + `scripts/render_video.mjs`）** 逐帧渲染生成 1280×720 30fps 带拟声音频的高清 MP4——100% 严守数学/物理公式与刻度守恒、零 AI 穿帮变形、零「AI生成」角标、本机 30 秒直出、Skill 总体积轻巧（< 1 MB，无需 Remotion 巨型依赖）。
> 2. **PPT 配图严禁重复、严禁同质化棚拍堆砌！** 整套 11 页课件最多生成 **3–4 张题材、景别、光影情绪完全不同** 的 `ImageGen` 无字视觉图；其余页面必须使用 `ppt_kit.py` 原生矢量工程图解、代码视频与瑞士排版，确保零撞脸、零复用（`audit_pptx.py` 硬性拦截重复图片）。

---

## 一、PPT 配图「视觉防重复矩阵」与 `ImageGen` 6 段提示词公式

**绝对红线**：
- **0 复用**：同一张图片绝不允许出现在 2 页及以上（例如绝不允许把第 2 页的沙堆图直接缩小贴到第 7 页例题里！第 7 页应改用 `ppt_kit.py` 的原生矢量标注蓝图 `add_cone_blueprint_card()`）。
- **0 同质化**：严禁连续多页都画“深色大理石桌上摆玻璃杯”。全套最多生成 **4 张 `ImageGen` 图**，必须分属 **4 种截然不同的视觉世界**：

| 槽位 | 所在页 | 视觉世界与光影情绪（彼此必须显著区分！） | 严禁雷同点 |
|---|---|---|---|
| **主图 1 · 电影封面** | P01 | 深海曜石暗调雕塑棚拍（主体严锁右 48%，左 48% 净黑留白） | 仅 P01 使用暗调静物大片 |
| **主图 2 · 真实生活现场** | P02 | 明亮自然日光纪实/微缩户外实景（如阳光下的金黄粮仓/工地沙堆、生活真实器物） | 必须明亮自然光，严禁暗黑棚拍 |
| **主图 3 · 反例冲突对比** | P06 | 明亮暖象牙白/浅灰建筑博物馆顶光微距，改用**哑光陶土/磨砂彩釉/彩色亚克力几何教具**形成高反差对比（底明显不等或高明显不等） | 严禁再用深绿大理石+透明玻璃杯！必须换材质与明亮色温 |
| **主图 4 · 课堂剧场/应用收官** | P11 | 等轴测全息光学/未来课堂交互沙盘或真实建筑地标摄影（如圆锥形天文台穹顶、建筑结构） | 严禁重复 P01 静物构图 |

> **P03（猜想分工）、P05（公式高潮推导）、P07（例题精讲）一律不生成 AI 照片**，直接调用 `ppt_kit.py` 原生矢量图解（`add_equal_base_height_gauge`、`add_three_to_one_derivation_graphic`、`add_cone_blueprint_card`）——信息密度更准、希沃白板可拆改、彻底消灭配图同质化！

### `ImageGen` 每张图必填 6 段提示词公式

```text
[1. 镜头与单幅构图约束]
  - 写明机位角度、焦段与单幅连续构图：ONE single continuous unbroken scene — STRICTLY NO split-screen, NO diptych border, NO vertical divider line, NO collage frames.
[2. 主体物理与几何精确锚定]
  - 写死不可出错的学科几何/科学形态（如圆锥必为针尖锐顶 <2mm，严禁平顶杯；反例必须肉眼一眼看出“宽矮 vs 细高”强烈对比）。
[3. 材质、布光与差异化色温锁定]
  - 按上表 4 种不同视觉世界锁死材质、自然光/博物馆顶光/曜石暗光与背景色，避免整套课件像同一种塑料模板。
[4. PPT 原生排版安全负空间配比]
  - 全出血封面：主体严锁右 48%，左 48% 干净负空间；跨页半幅图：四周留足安全边不裁切主体。
[5. 干净无杂物约束]
  - Zero extra props, zero floating hands, zero cartoon outlines, zero clipart/vector look.
[6. 零文字硬负向约束（每条必带！）]
  - Strictly NO text, NO letters, NO numbers, NO formulas, NO tick labels, NO arrows, NO captions, NO logos, NO watermarks anywhere in the image.
```

---

## 二、Three.js 代码驱动教学演示视频工程规范（`render_video.mjs`）

### 1. 为什么用内置 Three.js 引擎，而不用 AI 视频或重型 Remotion？
- **100% 教学准确**：物体尺寸、等底等高对齐、1/3→2/3→3/3 容积增长、3D 沙粒/液滴下落轨迹与实时数字卡片全由数学方程单源驱动，绝不穿帮。
- **0 角标、0 外部依赖**：直接复用本 Skill 内置的 `assets/three.min.js`（593 KB）与 `assets/video_stage.html`，无需安装数百 MB 的 `node_modules` 或 Remotion；自带纯 Node 合成拟声音频（倾倒沙声/水流声/清脆刻度音叉/收官和弦）。
- **全学科通用**：通过编写约 **180–320 行** 的纯 JS 场景脚本 `.build/video_scene.js` 并调用 `VIDEO_STAGE.register({ ... })`，即可渲染任意学科 3D 动效大片。

### 2. 场景脚本编写铁律（`VIDEO_STAGE.register`）
1. **确定性纯函数**：`renderFrame(ctx, frame, t, duration, progress)` 只依赖 `t` 与 `progress`（随机数一律用 `ctx.seededRng()`），绝不使用 `Date.now()` 或 `Math.random()`，确保每一帧零闪烁。
2. **强制复用内置 3D 实验器皿与运动学组件（严禁徒手写穿模/倒尖顶圆锥！）**：
   - `video_stage.html` 已内置通过实机验真的透明水晶器皿与粒子流组件（130–220 行即可写出电影级精确演示，绝不缩小玻璃壳或从圆锥尖顶倒沙！）：
     - `const cyl = helpers.createCrystalCylinder({ radius: 0.86, height: 2.58, ringFractions: [1/3, 2/3, 1] })` → `cyl.group.position.set(2.55, 0, 0); scene.add(cyl.group);`；每帧调用 `const topY = cyl.setFill(fill01, moundAmp)` 与 `cyl.setRingGlow(k, flash)`。
     - `const cone = helpers.createCrystalConeVessel({ radius: 0.86, height: 2.58, x: cx })` → **开口朝上的刚性空心水晶圆锥 + 独立透明底座**，`scene.add(cone.standGroup); scene.add(cone.moveGroup);`；每帧调用 `cone.setFill(remFrac)`（玻璃壳恒定不变，仅内部细沙按体积立方根缩小！），倾倒时直接用 `const pose = cone.solvePourPose(new THREE.Vector3(cylX - 0.08, H + 0.34, 0), tiltRad)`（`tiltRad` 从 `-1.98` 平滑到 `-2.28`），圆锥本体自然悬在圆柱左上方、敞口正对圆柱中心！
     - `const stream = helpers.createPourStream({ count: 220 })` → `scene.add(stream.group);`；每帧调用 `stream.update(active, pose.spoutWorld, new THREE.Vector3(cylX, topY, 0), t, flowEnv)`。
   - **镜头安全距与 HUD 零碰撞**：相机放在 `(-0.35, 3.55, 12.2)`、盯向 `(-0.2, 1.95, 0)` 确保抬起倾倒的圆锥 100% 留在画幅内；实时数据卡 `helpers.hud.drawMetricCard(42, 102, 320, 106, ...)` 固定放在**左上角**（标题下方），把右上半区完整留给空中倾倒圆锥，绝不遮挡！**片尾结论横幅（`drawFormulaBanner(42, 102, 540, 104, ...)`）出现时必须隐藏/替代左上角实时数据卡，严禁两张卡片同时叠画！**
3. **其余内置灯光、材质与 HUD 工具（直接调用 `ctx.helpers`）**：
   - `helpers.setupStudioLights({ theme })`（支持 `'obsidian'` / `'linen'` / `'laser'`）
   - `helpers.makeMarbleTable(w, d, dark)` / `helpers.makeGlassMat()` / `helpers.makeBrassMat()` / `helpers.makeSandMat()`
   - `helpers.project(vec3)`（3D 转 2D 像素坐标，画 `1/3`、`2/3`、`3/3 满` 实时跟随标牌）
   - `helpers.hud.drawHeader(...)`、`helpers.hud.drawMetricCard(...)`、`helpers.hud.drawFormulaBanner(...)`、`helpers.hud.drawSubtitle(...)`、`helpers.hud.drawCallout(...)`
4. **拟声音频节拍（`audioCues`）**：支持 `'pour'`（细沙流）、`'water'`（流水）、`'whoosh'`（转场气声）、`'chime'`（刻度晶铃）、`'fanfare'`（结论和弦），自动合成为带 AAC 音轨的离线 MP4。

### 3. 一键渲染与单图 16 帧高效验收（限 1 次渲染，严禁抽单帧反复空转！）
```bash
node "{skill_dir}/scripts/render_video.mjs" \
  --scene .build/video_scene.js \
  --out "演示视频/<课题>_3D代码演示.mp4" \
  --poster .build/video_poster.png \
  --poster-sec 8.5 \
  --contact-sheet .build/video_contact_sheet.png
```
- **高效纪律**：直接调用内置 `createCrystalCylinder / createCrystalConeVessel / createPourStream` 一次写准，渲染完毕后**只需用 `ViewImage` 看 1 张 `.build/video_contact_sheet.png`**；确认无穿模无遮挡后**立即进入下一步生图与 PPT 拼装，严禁额外抽取多张单帧反复微调耗尽轮数！**
- 验收通过后，若 MP4 > 1.8 MB 可用 `ffmpeg` 压一份 `960×540` 轻量化副本供单文件离线 HTML base64 内嵌；PPT 第 4 页直接用 `ppt_kit.py` 的 `add_video_slide()` 内嵌该 MP4 + `--poster` 封面帧。

---

## 三、全学科差异化 `ImageGen` + Three.js 代码视频配方速查

| 学科 | PPT 4 槽位差异化 `ImageGen` 题材（严禁雷同） | Three.js 代码视频（`render_video.mjs`）黄金场景 |
|---|---|---|
| **数学** | P01 曜石几何雕塑封面 / P02 日光户外实景（粮堆/建筑）/ P06 暖白台面彩陶反例教具 / P11 全息交互舞台 | 3 满金沙圆锥精确倾倒填满等底等高圆柱（含实时体积卡与 `1/3` 刻度脉冲）；圆柱侧面展平；32 份扇形咬合长方体 |
| **物理** | P01 暗室光学棱镜 / P02 日光真实生活现象（彩虹/潜望镜）/ P06 浅灰实验台反例对比 / P11 光学实验室全景 | 3D 激光束精确遵循斯涅尔定律折射与全反射演示；凸透镜移动物距实时成像动画；单摆周期对比 |
| **化学** | P01 暗调晶体分子艺术 / P02 日光厨房/自然界反应实景 / P06 暖白实验台对比烧杯 / P11 现代化学实验室 | 3D 分子键断裂与重组动画；滴定液滴落引发溶液颜色连续渐变与沉淀生成 |
| **生物** | P01 显微荧光生命雕塑 / P02 自然日光生态摄影 / P06 亮色解剖教具对比 / P11 生态观察台 | 3D 血管中红细胞流经肺泡携氧变色；叶片叶绿体光合能量流动画 |
| **语文 / 英语 / 史地** | P01 宋画/胶片主题封面 / P02 日光人文地理实景 / P06 对比器物或风貌静物 / P11 主题舞台 | 3D 立体地形沙盘水循环与发光河流路径；古诗意象镜头漫游与逐句光影字幕；3D 方位介词微缩方块演播 |
