# 教室大屏双模式互动 HTML 工程级设计蓝图（v5.1 全学科主题 × 内置引擎底盘版）

> 核心理念：**第一优先是学科知识/几何/科学 100% 准确，第二优先才是动效视频级视觉美感！**
> 严禁从零徒手重写数千行 CSS、模态弹窗和 PK 脚手架！**直接复用本技能内置的 `assets/theater_base.html` + `assets/theater_config.schema.json` + `scripts/build_html.py`**，只需在工作空间临时目录生成 `<work_dir>/theater_config.json` 与 `<work_dir>/theater_scenes.js`（约 250–420 行），即可在语数英理化生史地任意学科下稳定产出零报错、零按钮失灵、零溢出的离线单文件网页。

---

## 零、内置底盘 `window.THEATER` 极简接口速查

`k12_studio.py build-html` 会校验 `<work_dir>/theater_config.json`（支持直接设置 `"theme": "math" | "chinese" | "english" | "science" | "physics" | "chemistry" | "biology" | "history" | "geography"` 自动切换全站配色变量）并注入 `assets/theater_base.html`。底盘已内置顶栏、底部时间轴、拖拽 360° 旋转、离线 `<video>` 播放器（在 `films` 里设 `"isVideo": true`）、4 队 3D 光影柱 PK 与全局事件委托弹窗。

在 `<work_dir>/theater_scenes.js` 末尾调用一次 `THEATER.registerScenes({...})` 即可接管全部非视频分镜：
```js
const T = window.THEATER;
// 可直接复用：
// - 3D 直观相机（pitch > 0 为自然 3/4 俯视看顶面，pitch = 1.3 为顶视俯拍，绝不会倒看底面）
//   T.cam, T.project(p), T.camKF(kfs, p), T.resetCam()
// - 实体外法线背面剔除：T.isFrontFacing(pts, solidCenter) -> 返回 { n, d } 或 null
// - 绘图与特效：T.ctx, T.poly, T.fillPoly, T.line, T.text, T.glowDot, T.floorGlow, T.withReflection,
//   T.shadeHex, T.rgba, T.spawnSpark, T.spawnDrop, T.spawnRipple, T.addPulse, T.audio
// - 数学与控制：T.clamp, T.lerp, T.smooth01, T.easeOut, T.easeIn, T.easeInOut, T.PI, T.TAU,
//   T.switchFilm(i, auto), T.seek(p), T.updateFormula(), T.updateDirector(), T.$, T.$$
T.registerScenes({
  draw(filmIdx, p, t, dt) { /* 仅画本分镜 3D/2D 动画、光路、意象画卷或标尺 */ },
  buildCtl(filmIdx, bodyEl, titleEl, hintEl) { /* 构建右侧控制面板；独立跳转按钮绝不复用 .scn 类名 */ },
  formula(filmIdx) { return { tag: '...', main: '...', row: '...', num: '...' }; },
  director(filmIdx) { return { v1: '...', v2: '...' }; },
  soundCue(filmIdx, cross) { /* 可选：if (cross(0.3)) T.audio.whoosh(); */ },
  onSwitchFilm(filmIdx) { /* 可选：重置该分镜局部交互状态 */ }
});
```

---

## 一、编写 `<work_dir>/theater_scenes.js` 前的 5 条工程铁律

### 1. 几何与科学不变量合同（Pre-Code Invariant Contract）
在写动画代码前，先核清初态（`t=0`）与终态（`t=1`）的精确坐标与学科守恒关系：
- **共享基准地平面铁律**：同一场景并列站立的所有器皿或模型必须共用同一底面坐标 `floorY = -H_ref / 2`，严禁悬空错位。
- **旋转归位精确收敛铁律**（如圆柱切偶数 `N` 扇形拼近似长方体）：偶数片终态朝向严格归 `0`，奇数片严格归 `π`，旋转插值消去初始角 `tc` 走最短角差 `diff = ((targetRot - tc + π) % 2π + 2π) % 2π - π`，终态叠加半透明参考框。
- **理化生史地学科守恒**：物理折射严格按斯涅尔定律 `n1·sin(θ1) = n2·sin(θ2)` 实时解算光线折角；凸透镜成像严格按 `1/f = 1/u + 1/v` 联动像距与倒正虚实；化学微粒反应前后原子总数严格守恒；语文/历史时空漫游节点年代与原句逐字核实。

### 2. 单一数据源计算铁律（严禁手敲中间数！）
- 左侧公式/核心要点卡、画布标尺、底部导演参数栏的所有数值，必须从同一组 JS 变量实时导出，严禁硬编码可能自相矛盾的中间结果；`questions` 题库在生成 `<work_dir>/theater_config.json` 时由 Python 先行断言 `answerText` 与 `opts[a]` 一致（`scripts/build_html.py` 亦会自动强校验）。

### 3. `1280×720` 严格非重叠安全分区预算
整屏固定 `1280×720`（居中按比例自适应缩放，零滚动溢出），严格按 5 大安全区排布：

| 安全区 | 像素边界 (`1280×720`) | 承载元素 |
| --- | --- | --- |
| 悬浮磨砂顶栏 | `x: 16..1264, y: 10..56` | 课题徽标、模式切换、视角重置/动效/音效/全屏 |
| 左上标题 + 核心卡片 | `x: 34..330, y: 78..410` | 分镜标题、简介、动态浮现公式/知识卡（宽 ≤ `296px`） |
| **中央 3D / 视频主舞台** | **`x: 345..1020, y: 80..565`** | **3D 互动模型、光路/流道、尺寸标尺、内嵌离线 3D 视频** |
| 右上导演控制卡 | `x: 1048..1264, y: 70..420` | 滑块/份数/情景/倍速/重播/跳转按钮（宽 `216px`） |
| 底部字幕 + 电影时间轴 | `x: 14..1266, y: 580..708` | 流光电影字幕 + 底部 64px 导演台（分镜切换/播放/进度轨） |

### 4. 离线内嵌 3D 代码视频分镜 + 动态弹窗事件委托
- 直接把步骤 3 `k12_studio.py render-video --compact-out "<work_dir>/video_compact.mp4"` 产出的 `960×540` 轻量 MP4 传给 `k12_studio.py build-html --video`，自动 base64 内嵌为离线 `<video>` 分镜，支持倍速、重播与时间轴字幕同步。
- 动态注入按钮统一走事件委托，独立跳转按钮不复用 `.scn` 类名。

### 5. 模式二：全学科主题 4 队 3D 光影能量柱 PK 竞技场
- 左 `36%` 悬浮聚光灯题卡（倒计时 + 6–8 道教材验算题 + 玻璃态选项 + `<dialog>` 步进解析 + 颁奖按钮），右 `64%` 反光舞台矗立 4 根垂直发光 3D 能量柱（`+1` 弹簧压实 + 彩屑烟花 + 冠军皇冠 + 三层颁奖台）。

---

## 二、强制自动化 + 单图总览验收闸门（`k12_studio.py audit-html`）

生成 `.html` 后必跑以下两步验收：
1. **无头浏览器全自动点击与 WebGL/视频核验**：
   ```bash
   python "{skill_dir}/k12_studio.py" audit-html "<out_dir>/lab.html" --shots-dir "<work_dir>/html_shots"
   ```
   强制断言：`external_urls` 为空、`syntax_error` 为 `null`、双模式 `1280×720` 零溢出、`<video>` `readyState >= 3`、解析与颁奖弹窗开关正常、`errors` 为空。
2. **肉眼检查 1 张 4×4 总览图 `<work_dir>/html_shots/audit_contact_sheet.png`**：核对几何/光路形态、算式一致性与安全区无遮挡后即可交付。
