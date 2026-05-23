import sys
from pathlib import Path

from hdr_gainmap.main import run


def test_app() -> None:
    sdr_image = Path(__file__).parent.parent / "samples/input_sdr.jpg"
    hdr_image = Path(__file__).parent.parent / "samples/input_hdr.avif"
    output = Path(__file__).parent.parent / "output.jpg"

    arguments = [
        "--sdr",
        str(sdr_image),
        "--hdr",
        str(hdr_image),
        "--output",
        str(output),
    ]

    sys.argv.extend(arguments)

    run()


def test_web_app() -> None:
    run()
