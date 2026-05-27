# 播放列表微型指示器 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在迷你条上新增可点击的 "N/M ▾" 播放列表指示器，点击弹出迷你曲目列表，支持点击跳转切歌。

**架构：** 两个新组件（`TrackIndicator`、`TrackPopup`）嵌入 `mini_bar.py`，复刻现有右键菜单的深色半透明样式。`player.py` 新增一个 `jump_to` 方法。零新文件，零新依赖。

**技术栈：** Python 3.13、PySide6

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `mini_player/core/player.py` | MusicPlayer — 新增 `jump_to()` 跳转播放 | 修改 |
| `mini_player/ui/mini_bar.py` | MiniBar — 新增 TrackIndicator、TrackPopup 类，插入布局 | 修改 |

---

### 任务 1：MusicPlayer 新增 `jump_to` 方法

**文件：**
- 修改：`desktopTransMusic/mini_player/core/player.py`

- [ ] **步骤 1：添加 `jump_to` 方法**

在 `cycle_repeat_mode` 方法之后（约第 167 行），`# ── Internals` 注释之前，插入：

```python
    def jump_to(self, index: int) -> None:
        """Jump to a specific track index in the playlist."""
        if 0 <= index < len(self._playlist):
            self._play_index(index)
```

- [ ] **步骤 2：验证语法**

运行：`cd "D:/gitWorkSpace/desktopTransMusic/desktopTransMusic/mini_player" && source ../../.venv/Scripts/activate && python -m py_compile core/player.py`
预期：无输出（编译成功）

- [ ] **步骤 3：Commit**

```bash
git add desktopTransMusic/mini_player/core/player.py
git commit -m "feat(player): add jump_to method for playlist track jumping"
```

---

### 任务 2：创建 TrackPopup 弹出列表组件

**文件：**
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`

- [ ] **步骤 1：在 SeekSlider 类之后、MiniBar 类之前添加 TrackPopup 类**

```python
class TrackPopup(QWidget):
    """Popup playlist list that appears below the track indicator."""
    track_selected = Signal(int)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedWidth(220)
        self._playlist: list[str] = []
        self._current_index: int = 0
        self._labels: list[QLabel] = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 4, 6, 4)
        self._layout.setSpacing(1)
        self.setStyleSheet("""
            TrackPopup {
                background: rgba(30, 30, 40, 240);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
            }
        """)
        self.installEventFilter(self)

    def set_tracks(self, playlist: list[str], current_index: int) -> None:
        """Rebuild the track list from playlist paths."""
        import os
        self._playlist = playlist
        self._current_index = current_index
        for lbl in self._labels:
            self._layout.removeWidget(lbl)
            lbl.deleteLater()
        self._labels.clear()

        max_show = 8
        indices = list(range(len(playlist)))
        if len(playlist) > max_show:
            half = max_show // 2
            if current_index <= half:
                indices = list(range(max_show - 1)) + [-1]
            elif current_index >= len(playlist) - half:
                indices = list(range(len(playlist) - max_show + 1, len(playlist)))
                indices = [-1] + indices
            else:
                start = current_index - half + 1
                indices = [-1] + list(range(start, start + max_show - 2)) + [-1]

        for i in indices:
            if i == -1:
                lbl = QLabel("...")
                lbl.setEnabled(False)
                lbl.setStyleSheet("color: rgba(200,200,215,60); padding: 2px 8px; font-size: 10px;")
            else:
                name = os.path.basename(playlist[i])
                display = f"{i + 1}. {name}"
                lbl = QLabel(display)
                lbl.setProperty("track_index", i)
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                if i == current_index:
                    lbl.setStyleSheet(
                        "color: rgba(220,220,235,220); padding: 2px 8px; font-size: 10px; "
                        "background: rgba(255,255,255,18); border-radius: 3px;"
                    )
                else:
                    lbl.setStyleSheet(
                        "color: rgba(200,200,215,160); padding: 2px 8px; font-size: 10px; "
                        "border-radius: 3px;"
                    )
                lbl.installEventFilter(self)
            self._labels.append(lbl)
            self._layout.addWidget(lbl)

        h = min(len(indices), max_show) * 20 + 10
        self.setFixedHeight(h)

    def eventFilter(self, obj, event) -> bool:
        from PySide6.QtCore import QEvent as _QEvent
        if isinstance(obj, QLabel) and obj.property("track_index") is not None:
            etype = event.type()
            if etype == _QEvent.Type.MouseButtonPress:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    self.track_selected.emit(idx)
                self.hide()
                return True
            elif etype == _QEvent.Type.Enter:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    obj.setStyleSheet(
                        "color: rgba(220,220,235,200); padding: 2px 8px; font-size: 10px; "
                        "background: rgba(255,255,255,10); border-radius: 3px;"
                    )
            elif etype == _QEvent.Type.Leave:
                idx = obj.property("track_index")
                if idx != self._current_index:
                    obj.setStyleSheet(
                        "color: rgba(200,200,215,160); padding: 2px 8px; font-size: 10px; "
                        "border-radius: 3px;"
                    )
        return False

    def show_at(self, anchor: QWidget) -> None:
        """Position popup below the anchor widget."""
        pos = anchor.mapToGlobal(QPoint(0, anchor.height() + 2))
        self.move(pos)
        self.show()
```

- [ ] **步骤 2：验证语法**

运行：`cd "D:/gitWorkSpace/desktopTransMusic/desktopTransMusic/mini_player" && source ../../.venv/Scripts/activate && python -m py_compile ui/mini_bar.py`
预期：无输出（编译成功）

- [ ] **步骤 3：Commit**

```bash
git add desktopTransMusic/mini_player/ui/mini_bar.py
git commit -m "feat(ui): add TrackPopup component for playlist selection"
```

---

### 任务 3：创建 TrackIndicator 计数标签组件

**文件：**
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`

- [ ] **步骤 1：在 TrackPopup 类之后添加 TrackIndicator 类**

```python
class TrackIndicator(QLabel):
    """Clickable track count indicator: '3 / 12 ▾'."""
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("0 / 0 ▾", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: rgba(200, 200, 215, 150);
                font-size: 10px;
                padding: 2px 6px;
                background: rgba(255, 255, 255, 8);
                border-radius: 4px;
            }
            QLabel:hover {
                color: rgba(220, 220, 235, 200);
                background: rgba(255, 255, 255, 18);
            }
        """)
        self._current: int = 0
        self._total: int = 0

    def set_count(self, current: int, total: int) -> None:
        self._current = current
        self._total = total
        self.setText(f"{current + 1} / {total} ▾")

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
```

- [ ] **步骤 2：验证语法**

运行：同任务 2 步骤 2。

- [ ] **步骤 3：Commit**

```bash
git add desktopTransMusic/mini_player/ui/mini_bar.py
git commit -m "feat(ui): add TrackIndicator clickable count label"
```

---

### 任务 4：集成 TrackIndicator 和 TrackPopup 到 MiniBar

**文件：**
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`

- [ ] **步骤 1：在 `__init__` 中初始化 popup**

在 `self._seeking = False` 之后添加：

```python
        # Playlist popup
        self._track_popup: TrackPopup | None = None
```

- [ ] **步骤 2：在 `_build_ui` 中插入指示器**

找到 `layout.addWidget(self._btn_repeat)` 之后的 `layout.addSpacing(4)`，将其替换为指示器：

将：
```python
        layout.addWidget(self._btn_repeat)

        layout.addSpacing(4)

        # Progress
```

改为：
```python
        layout.addWidget(self._btn_repeat)

        # Track indicator (playlist position)
        self._track_indicator = TrackIndicator(self)
        layout.addWidget(self._track_indicator)

        # Progress
```

- [ ] **步骤 3：删除紧接着的 `layout.addSpacing(4)` 行**（如果指示器替换了它）

注意滚动条前后 spacing 保持一致。指示器替换了循环按钮后的 spacing(4)，所以直接删除那行 spacing(4)。

- [ ] **步骤 4：在 `_connect_signals` 中添加信号连接**

在 `_connect_signals` 方法的末尾（`self._player.repeat_mode_changed.connect(...)` 之后），添加：

```python
        self._track_indicator.clicked.connect(self._on_track_indicator_clicked)
```

- [ ] **步骤 5：更新 `_on_track` 以刷新指示器**

在 `_on_track` 方法末尾添加：

```python
        self._track_indicator.set_count(self._player.current_index, len(self._player.playlist))
```

- [ ] **步骤 6：添加弹窗交互方法**

在 `_quit_app` 方法之后添加两个新方法：

```python
    def _ensure_popup(self) -> TrackPopup:
        if self._track_popup is None:
            self._track_popup = TrackPopup(None)
            self._track_popup.track_selected.connect(self._player.jump_to)
        return self._track_popup

    def _on_track_indicator_clicked(self) -> None:
        popup = self._ensure_popup()
        if popup.isVisible():
            popup.hide()
            return
        popup.set_tracks(self._player.playlist, self._player.current_index)
        popup.show_at(self._track_indicator)
```

- [ ] **步骤 7：验证语法**

运行：`cd "D:/gitWorkSpace/desktopTransMusic/desktopTransMusic/mini_player" && source ../../.venv/Scripts/activate && python -m py_compile ui/mini_bar.py`
预期：无输出（编译成功）

- [ ] **步骤 8：手动验证**

运行应用：`cd "D:/gitWorkSpace/desktopTransMusic/desktopTransMusic/mini_player" && source ../../.venv/Scripts/activate && python main.py`

验证清单：
1. 打开音乐文件 → 指示器显示 "1 / N ▾"
2. 点击指示器 → 弹出列表，当前曲目高亮
3. 点击列表中其他曲目 → 切换到该曲目播放
4. 点击指示器再次 → 列表收起
5. 使用上一首/下一首按钮 → 指示器数字跟随更新
6. 点击列表外空白处 → 列表消失

- [ ] **步骤 9：Commit**

```bash
git add desktopTransMusic/mini_player/ui/mini_bar.py
git commit -m "feat(ui): integrate TrackIndicator and TrackPopup into MiniBar"
```

---

## 自检

1. **规格覆盖度** — 三项技能需求全部覆盖：`jump_to`（任务 1）、TrackPopup（任务 2）、TrackIndicator（任务 3）、集成布局与信号连接（任务 4）
2. **占位符扫描** — 无 TODO、无待定内容、无 "添加适当错误处理" 等模糊描述
3. **类型一致性** — `jump_to` 接收 `int`，`track_selected` 信号发射 `int`，`set_tracks` 参数一致，`set_count` 使用 `current + 1` 展示

---

## 依赖说明

任务 3 可并行于任务 1+2，任务 4 依赖前三者全部完成。
