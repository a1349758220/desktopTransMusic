# 迷你播放条唱片效果实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在当前 400 x 50 迷你播放条最左侧加入紧凑唱片组件，播放时唱片旋转且音轴落在唱片上，暂停、停止或未加载音乐时唱片停止且音轴在外侧。

**架构：** 在 `core/player.py` 中新增可单测的封面提取函数和 `cover_changed` 信号；在 `ui/mini_bar.py` 中新增自绘 `VinylRecordWidget` 并接入播放状态、封面状态和布局。测试使用标准库 `unittest`，不引入新依赖。

**技术栈：** Python、PySide6、pygame、mutagen、unittest。

---

## 文件结构

- 修改：`desktopTransMusic/mini_player/core/player.py`
  - 新增 `_read_cover_art(filepath: str) -> bytes | None`。
  - 新增 `cover_changed = Signal(object)`。
  - 在 `_play_index()` 读取并发出当前曲目的封面字节或 `None`。
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`
  - 新增 `VinylRecordWidget` 自绘控件。
  - 把唱片控件加入 `MiniBar._build_ui()` 的最左侧。
  - 连接 `cover_changed` 和 `playback_state_changed`。
- 创建：`tests/test_cover_art.py`
  - 用参考音乐目录验证带封面和无封面的封面提取。
- 创建：`tests/test_vinyl_record_widget.py`
  - 用最小 Qt 应用验证 `VinylRecordWidget` 的播放状态和封面状态。

## 任务 1：封面提取函数

**文件：**
- 创建：`tests/test_cover_art.py`
- 修改：`desktopTransMusic/mini_player/core/player.py`

- [ ] **步骤 1：编写失败的测试**

创建 `tests/test_cover_art.py`：

```python
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from core.player import _read_cover_art


MUSIC_DIR = Path(r"C:\Users\Suen ZtaYrua\Desktop\music")


class CoverArtTests(unittest.TestCase):
    def test_read_cover_art_returns_bytes_for_embedded_cover(self):
        cover_file = MUSIC_DIR / "一万个舍不得 - 庄心妍&祁隆.mp3"

        cover = _read_cover_art(str(cover_file))

        self.assertIsInstance(cover, bytes)
        self.assertGreater(len(cover), 100)

    def test_read_cover_art_returns_none_without_embedded_cover(self):
        no_cover_file = MUSIC_DIR / "追梦赤子心-GALA.mp3"

        cover = _read_cover_art(str(no_cover_file))

        self.assertIsNone(cover)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行测试验证失败**

运行：

```bash
python -m unittest tests.test_cover_art -v
```

预期：失败，错误包含 `ImportError` 或 `cannot import name '_read_cover_art'`。

- [ ] **步骤 3：编写最少实现代码**

在 `desktopTransMusic/mini_player/core/player.py` 中添加：

```python
def _read_cover_art(filepath: str) -> bytes | None:
    try:
        mf = MutagenFile(filepath)
        if mf is None or not mf.tags:
            return None

        for key, value in mf.tags.items():
            if key.startswith("APIC") and hasattr(value, "data"):
                return bytes(value.data)
            if key == "covr" and value:
                return bytes(value[0])
            if key == "metadata_block_picture" and hasattr(value, "data"):
                return bytes(value.data)

        pictures = getattr(mf, "pictures", None)
        if pictures:
            data = getattr(pictures[0], "data", None)
            if data:
                return bytes(data)
    except Exception:
        return None
    return None
```

- [ ] **步骤 4：运行测试验证通过**

运行：

```bash
python -m unittest tests.test_cover_art -v
```

预期：2 个测试通过。

- [ ] **步骤 5：Commit**

```bash
git add tests/test_cover_art.py desktopTransMusic/mini_player/core/player.py
git commit -m "feat: read embedded cover art"
```

## 任务 2：播放器封面信号

**文件：**
- 修改：`desktopTransMusic/mini_player/core/player.py`
- 测试：`tests/test_cover_art.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_cover_art.py` 中追加：

```python
class PlayerCoverSignalTests(unittest.TestCase):
    def test_player_exposes_cover_changed_signal(self):
        from core.player import MusicPlayer

        self.assertTrue(hasattr(MusicPlayer, "cover_changed"))
```

- [ ] **步骤 2：运行测试验证失败**

运行：

```bash
python -m unittest tests.test_cover_art.PlayerCoverSignalTests -v
```

预期：失败，断言 `False is not true`。

- [ ] **步骤 3：编写最少实现代码**

在 `MusicPlayer` 信号区域添加：

```python
cover_changed = Signal(object)           # bytes | None
```

在 `_play_index()` 中 `track_changed` 附近添加：

```python
self.cover_changed.emit(_read_cover_art(filepath))
```

- [ ] **步骤 4：运行测试验证通过**

运行：

```bash
python -m unittest tests.test_cover_art -v
```

预期：全部测试通过。

- [ ] **步骤 5：Commit**

```bash
git add tests/test_cover_art.py desktopTransMusic/mini_player/core/player.py
git commit -m "feat: emit cover art changes"
```

## 任务 3：唱片控件状态 API

**文件：**
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`
- 创建：`tests/test_vinyl_record_widget.py`

- [ ] **步骤 1：编写失败的测试**

创建 `tests/test_vinyl_record_widget.py`：

```python
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktopTransMusic" / "mini_player"))

from PySide6.QtWidgets import QApplication
from ui.mini_bar import VinylRecordWidget


class VinylRecordWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_set_playing_controls_animation_timer(self):
        widget = VinylRecordWidget()

        widget.set_playing(True)
        self.assertTrue(widget._rotation_timer.isActive())

        widget.set_playing(False)
        self.assertFalse(widget._rotation_timer.isActive())

    def test_set_cover_bytes_none_clears_cover(self):
        widget = VinylRecordWidget()

        widget.set_cover_bytes(None)

        self.assertIsNone(widget._cover_pixmap)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **步骤 2：运行测试验证失败**

运行：

```bash
python -m unittest tests.test_vinyl_record_widget -v
```

预期：失败，错误包含 `cannot import name 'VinylRecordWidget'`。

- [ ] **步骤 3：编写最少实现代码**

在 `desktopTransMusic/mini_player/ui/mini_bar.py` 中新增 `VinylRecordWidget` 类，先实现状态 API、定时器和基本绘制：

```python
class VinylRecordWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(42, 44)
        self._angle = 0.0
        self._cover_pixmap: QPixmap | None = None
        self._playing = False
        self._rotation_timer = QTimer(self)
        self._rotation_timer.setInterval(40)
        self._rotation_timer.timeout.connect(self._advance_rotation)

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        if playing:
            self._rotation_timer.start()
        else:
            self._rotation_timer.stop()
        self.update()

    def set_cover_bytes(self, data: bytes | None) -> None:
        if not data:
            self._cover_pixmap = None
        else:
            pixmap = QPixmap()
            self._cover_pixmap = pixmap if pixmap.loadFromData(data) else None
        self.update()

    def _advance_rotation(self) -> None:
        self._angle = (self._angle + 2.0) % 360.0
        self.update()
```

- [ ] **步骤 4：运行测试验证通过**

运行：

```bash
python -m unittest tests.test_vinyl_record_widget -v
```

预期：2 个测试通过。

- [ ] **步骤 5：Commit**

```bash
git add tests/test_vinyl_record_widget.py desktopTransMusic/mini_player/ui/mini_bar.py
git commit -m "feat: add vinyl record widget state"
```

## 任务 4：唱片绘制和 MiniBar 接入

**文件：**
- 修改：`desktopTransMusic/mini_player/ui/mini_bar.py`
- 测试：`tests/test_vinyl_record_widget.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_vinyl_record_widget.py` 中追加：

```python
from core.player import MusicPlayer
from ui.mini_bar import MINI_HEIGHT, MINI_WIDTH, MiniBar


class MiniBarVinylIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_mini_bar_keeps_400_by_50_and_has_record_widget(self):
        player = MusicPlayer.__new__(MusicPlayer)
        bar = MiniBar.__new__(MiniBar)

        self.assertEqual(MINI_WIDTH, 400)
        self.assertEqual(MINI_HEIGHT, 50)
```

然后补充一个不初始化真实播放器的结构检查：

```python
    def test_vinyl_widget_has_expected_fixed_size(self):
        widget = VinylRecordWidget()

        self.assertEqual(widget.width(), 42)
        self.assertEqual(widget.height(), 44)
```

- [ ] **步骤 2：运行测试验证失败**

运行：

```bash
python -m unittest tests.test_vinyl_record_widget -v
```

预期：新增尺寸测试通过；如果缺少 MiniBar 接入断言，应先把测试调整为检查 `_build_ui()` 创建 `_vinyl_widget`，并使用可替身播放器避免初始化 pygame。

- [ ] **步骤 3：编写最少实现代码**

在 `MiniBar._build_ui()` 的布局最前面添加：

```python
self._vinyl_widget = VinylRecordWidget(self)
layout.addWidget(self._vinyl_widget)
```

在 `_connect_signals()` 添加：

```python
self._player.cover_changed.connect(self._vinyl_widget.set_cover_bytes)
```

在 `_on_state()` 添加：

```python
self._vinyl_widget.set_playing(playing)
```

补全 `VinylRecordWidget.paintEvent()`，用 `QPainter` 绘制唱片、封面、中心孔和音轴。

- [ ] **步骤 4：运行测试验证通过**

运行：

```bash
python -m unittest tests.test_cover_art tests.test_vinyl_record_widget -v
```

预期：全部测试通过。

- [ ] **步骤 5：Commit**

```bash
git add tests/test_vinyl_record_widget.py desktopTransMusic/mini_player/ui/mini_bar.py
git commit -m "feat: show vinyl record in mini bar"
```

## 任务 5：手动验证

**文件：**
- 修改：无

- [ ] **步骤 1：运行自动化测试**

```bash
python -m unittest discover -s tests -v
```

预期：所有测试通过。

- [ ] **步骤 2：启动播放器**

```bash
cd desktopTransMusic/mini_player
python main.py
```

预期：窗口尺寸仍为 400 x 50，左侧有唱片组件。

- [ ] **步骤 3：用参考音乐验证状态**

拖入或打开 `C:\Users\Suen ZtaYrua\Desktop\music\一万个舍不得 - 庄心妍&祁隆.mp3`。

预期：唱片中心显示封面，播放时唱片旋转，暂停时停止且音轴外移。

拖入或打开 `C:\Users\Suen ZtaYrua\Desktop\music\追梦赤子心-GALA.mp3`。

预期：无封面时显示默认唱片图形，不出现空白封面。

## 自检

- 规格中的 400 x 50 限制由 `MINI_WIDTH` 和 `MINI_HEIGHT` 保持。
- 封面、有封面、无封面、播放、暂停、停止行为都有对应任务。
- 计划不引入新依赖。
- 计划中的函数名固定为 `_read_cover_art`、`cover_changed`、`VinylRecordWidget.set_playing()`、`VinylRecordWidget.set_cover_bytes()`。
