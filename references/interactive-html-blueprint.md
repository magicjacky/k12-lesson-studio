# 教室大屏双模式互动 HTML 工程级设计蓝图（v4.1 准确第一 × 内置引擎底盘版）

> 核心理念：**第一优先是数学/几何/科学 100% 准确，第二优先才是动效视频级视觉美感！**
> 严禁从零徒手重写 2,500 行 CSS、模态弹窗和 PK 脚手架！**必须直接复用本 Skill 内置的 `assets/theater_base.html` + `scripts/build_html.py`**，你只需编写 `config.json` 与 `scenes.js`（约 250–400 行），即可在任何学科下稳定产出零报错、零按钮失灵、零视角倒翻的离线大片网页。

---

## 零、内置底盘 `window.THEATER` 极简接口速查（`scenes.js` 必读）

`build_html.py` 会把你的 `config.json` 注入 `window.CONFIG`，把 `scenes.js` 注入 `theater_base.html` 末尾。底盘已内置顶栏、底部时间轴、拖拽 360° 旋转、离线 `<video>` 播放器（只需在 `config.json` 的 `films` 里给实景视频分镜设 `"isVideo": true`）、4 队 3D 光影柱 PK 与全局事件委托弹窗。

在 `scenes.js` 末尾调用一次 `THEATER.registerScenes({...})` 即可接管全部非视频分镜：
```js
const T = window.THEATER;
// 可直接复用：
// - 3D 直观相机（重要：pitch > 0 为自然 3/4 俯视看顶面！pitch = 1.3 为顶视俯拍！绝不会倒看底面！）
//   T.cam, T.project(p), T.camKF(kfs, p), T.resetCam()
// - 实体外法线背面剔除：T.isFrontFacing(pts, wedgeCenter) -> 返回 { n, d } 或 null
// - 绘图与特效：T.ctx, T.poly, T.fillPoly, T.line, T.text, T.glowDot, T.floorGlow, T.withReflection,
//   T.shadeHex, T.rgba, T.spawnSpark, T.spawnDrop, T.spawnRipple, T.addPulse, T.audio
// - 数学与控制：T.clamp, T.lerp, T.smooth01, T.easeOut, T.easeIn, T.easeInOut, T.PI, T.TAU,
//   T.switchFilm(i, auto), T.seek(p), T.updateFormula(), T.updateDirector(), T.$, T.$$
T.registerScenes({
  draw(filmIdx, p, t, dt) { /* 仅画本分镜 3D/2D 动画与标尺 */ },
  buildCtl(filmIdx, bodyEl, titleEl, hintEl) { /* 构建右侧控制面板；独立按钮绝不复用 .scn 类名 */ },
  formula(filmIdx) { return { tag: '...', main: '...', row: '...', num: '...' }; },
  director(filmIdx) { return { v1: '...', v2: '...' }; },
  soundCue(filmIdx, cross) { /* 可选：if (cross(0.3)) T.audio.whoosh(); */ },
  onSwitchFilm(filmIdx) { /* 可选：重置该分镜局部交互状态 */ }
});
```

---

## 一、写 `scenes.js` 前的 5 条工程铁律（每条必须先算清、再落码！）

### 1. 数学与几何不变量合同（Pre-Code Geometry Contract）
在写任何 3D/2D 动画代码前，必须先在注释中写出并校验每段动画的**初态（`t=0`）与终态（`t=1`）精确坐标方程**：
- **共享基准地平面铁律**：同一场景中并列站立的所有物体（如等底等高的圆锥与圆柱，甚至反例变矮圆柱），**必须共用同一个底面世界坐标 `floorY = -H_ref / 2`**，严禁一个物体画在 `y = 0..H`、另一个画在 `y = -H/2..+H/2` 导致悬空穿帮！
- **旋转归位精确收敛铁律**（以“圆柱切扇形拼近似长方体”为例，其他几何拼接同理）：
  - 设扇形份数为偶数 `N`，半径 `r`，圆心角 `α = 2π/N`，弦宽 `c = 2r·sin(α/2)`，三角形高 `hTri = r·cos(α/2)`，水平居中起点 `x0 = -(N/4 - 0.25)·c`。
  - 偶数片（`j = i/2`）终态顶点 `(x0 + j·c, 0, -hTri/2)`，终态朝向必须严格归零 `targetRot = 0`；
  - 奇数片（`j = (i-1)/2`）终态顶点 `(x0 + (j + 0.5)·c, 0, +hTri/2)`，终态朝向必须严格归 `π`（`targetRot = π`）；
  - 旋转插值**必须消去初始角 `tc`** 并走最短角差：`diff = ((targetRot - tc + π) % 2π + 2π) % 2π - π`，`rot = tc + diff * ease(er)`（**绝不可写成 `tc + targetRot * er` 导致每片仍歪向原始圆周角！**）。
  - 终态（`p >= 0.84`）叠加极细半透明香槟金虚线长方体参考框，让学生切换 `8 / 16 / 32 / 64` 份时肉眼直观看到边缘越来越紧贴真正长方体。
- **相机俯仰角符号与背面剔除自检**：
  - 使用内置底盘 `THEATER.project(p)` 时，坐标系已固化为 **`pitch > 0` 即自然 3/4 俯视视角**（`pitch ≈ 0.38–0.50` 清晰看到顶面与正面，`pitch ≈ 1.25–1.35` 俯拍顶面，绝不会倒看底面）；
  - 实体多面体直接调用 `THEATER.isFrontFacing(pts, solidCenter)` 做外法线背面剔除，按返回的 `d` 从远到近排序绘制，彻底消除 Z-fighting。

### 2. 单一数据源公式校验铁律（严禁手敲中间数！）
- 左侧公式卡、画布三维标尺、底部导演参数栏的所有数字，**必须全部从同一组 JS 变量实时计算导出**：
  - 例：`const pir = 3.14 * r; const vol = pir * r * h;` → 展示 `= πr × r × h = ${pir.toFixed(2)} × ${r.toFixed(1)} × ${h.toFixed(1)}` 与 `${vol.toFixed(2)} cm³`；
  - **绝不允许把中间乘积硬编码成字面量**（防止出现 `12.56 × 2.0 × 5.0 = 62.80` 这种低级算术矛盾！）；
  - 若有示例常数（如圆锥体积例题），必须明确写出 `r=1.5, h=4 → 1/3 × 28.26 = 9.42 cm³`，绝不凭空丢一个无来源的中间数。

### 3. `1280×720` 严格非重叠安全分区预算
整屏固定 `1280×720`（居中按比例缩放，零滚动溢出），严格按 5 大互不入侵的安全区排布，**相机 `cx / cy / dist` 与 `<video>` 坐标必须确保主体与标注 100% 落在中央区**：

| 安全区 | 像素边界 (`1280×720`) | 承载元素 |
| --- | --- | --- |
| 悬浮磨砂顶栏 | `x: 16..1264, y: 10..56` | 课题徽标、模式切换、视角重置/动效/音效/全屏 |
| 左上标题 + 公式卡 | `x: 34..330, y: 78..410` | 分镜标题、1 句简介、动态浮现公式卡（宽 ≤ `296px`） |
| **中央 3D / 视频主舞台** | **`x: 345..1020, y: 80..565`** | **3D 模型、抬起倾倒轨迹、三维尺寸标尺、1/3 刻度、内嵌实景视频** |
| 右上导演控制卡 | `x: 1048..1264, y: 70..420` | 滑块/份数/情景/倍速/重播/跳转按钮（宽 `216px`） |
| 底部字幕 + 电影时间轴 | `x: 14..1266, y: 580..708` | 左下流光电影字幕 + 底部 64px 导演台（分镜切换/播放/进度轨/关键帧） |

### 4. 离线内嵌实景演示视频分镜 + 动态弹窗事件委托铁律
- **实景演示分镜（如 `04 实景倒沙`）**：将 `VideoGen` 生成并转码后的轻量 H.264 MP4（`960×548`，约 `0.8–1.4 MB`）以 base64 Data URI 写入离线 `<video>`；配备 `0.5× / 0.75× / 1× / 1.25×` 倍速、重播、与底部进度条/播放键/顶栏动效与声音开关双向联动、随播放秒数跳步的底部流光字幕；视频框严格落于中央安全区，绝不遮挡标题或字幕。
- **动态按钮事件委托与类名隔离**：
  - 凡由 `innerHTML` 动态注入弹窗或面板的关闭/操作按钮（如 `#expDlg` 右上角 `.xBtn` 与底部 `[data-close]`），**一律使用 `document.addEventListener('click', ...)` 事件委托**，严禁初始化静态绑定导致点不动；
  - 独立跳转按钮（如 `#jumpSandVid`）严禁复用情景单选按钮类名（`.scn`），避免误触发情景重绘；
  - 现代 Web 规范落地：CSS `linear(...)` 物理弹簧缓动（仅用于 `transform`/`scale`，附 `cubic-bezier` 回退）、原生 `<dialog>` + `showModal()` + `closedby="any"`（附坐标外点回退）+ `overscroll-behavior: contain` + `prefers-reduced-motion` 尊重。

### 5. 模式二：暗黑光影综艺级 4 队 3D 能量柱 PK 竞技场
- 与模式一共享深曜石 × 香槟金美学宇宙：左 `36%` 悬浮聚光灯题卡（圆环倒计时 + 8 道 Python 100% 验算教材题 + 玻璃态 `A/B/C/D` 选项 + 居中 `<dialog>` 步进解析 + 鎏金颁奖按钮），右 `64%` 透视反光舞台矗立 4 根垂直发光 3D 能量柱（`+1` 落块弹簧压实 + 鎏金彩屑烟花 + 飘飞冠军皇冠 + 金属三层聚光灯颁奖台）。

---

## 二、强制自动化 + 肉眼几何验收闸门（`scripts/audit_html.mjs`）

生成完 `.html` 后，**必须执行以下两步验收，任一不过绝不交付**：

1. **运行内置脚本**：
   ```bash
   node {skill_dir}/scripts/audit_html.mjs <html路径> <截图输出目录>
   ```
   强制断言：`external_urls` 为空、`syntax_error` 为 null、Mode 1/Mode 2 均为 `1280×720` 零溢出、所有分镜 `<video>` `readyState >= 3`、解析弹窗 `.xBtn` 与底部 `[data-close]` 及颁奖弹窗 100% 可点开关闭、`errors` 为空。
2. **肉眼查看 1 张自动生成的 4×4 总览检查表 `.build/audit_shots/audit_contact_sheet.png`**（严禁为 16 张单图连续调用 16 次看图导致耗时过长；仅在总览发现疑似问题时单独放大对应帧）：
   - **几何形状真像目标吗？**（展开真是平直矩形吗？扇形咬合真是规整 3D 长方体且能看清顶面拼接吗？等底等高圆锥与圆柱真共地平面、顶齐同一高度吗？）
   - **所有算式数字与动态标注自洽不重合吗？**（公式卡中间因子相乘等于结果吗？标尺数值与公式一致吗？浮动标注如「等高」与「水位」保持 ≥ 24px 垂直错位不重影吗？）
   - **有无任何截断或遮挡？**（顶栏有没有切掉物体尖顶？3D 模型有没有撞上左公式卡或右控制卡？）
