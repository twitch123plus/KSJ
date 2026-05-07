from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_frames(input_dir: Path, count: int = 8) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, count + 1):
        frame = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        frame.paste((180, 40, 40, 255), (136, 112, 184, 208))
        frame.save(input_dir / f"frame_{index:02d}.png")


class PostProcessCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        temp_root = Path(temp_dir.name)
        input_dir = temp_root / "input"
        output_dir = temp_root / "output"
        write_frames(input_dir)

        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "post_process.py"),
                "idle",
                str(input_dir),
                str(output_dir),
                *args,
            ],
            check=True,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return output_dir

    def test_cli_exports_preview_gif_by_default(self) -> None:
        output_dir = self.run_cli()

        self.assertTrue((output_dir / "idle_preview.gif").exists())
        self.assertTrue((output_dir / "idle_sheet_aligned.png").exists())

    def test_cli_can_skip_preview_gif(self) -> None:
        output_dir = self.run_cli("--no-gif")

        self.assertFalse((output_dir / "idle_preview.gif").exists())
        self.assertTrue((output_dir / "idle_sheet_aligned.png").exists())


if __name__ == "__main__":
    unittest.main()
