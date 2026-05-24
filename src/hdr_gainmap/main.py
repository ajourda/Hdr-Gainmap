import typer
from hdr_gainmap.preset import Preset

app = typer.Typer(
    add_completion=False,
    help="Convert SDR + HDR images to HDR with Gain Map (UltraHDR)",
    no_args_is_help=True,
)


def run_sdr_hdr(
    sdr_path: str,
    hdr_path: str,
    output_path: str | None = None,
    preset: Preset = Preset.default,
    tag: bool = False,
    keep_temp_files: bool = False,
):
    from hdr_gainmap.gen.sdr_hdr_to_hdrgm import SdrHdrToHdrgm

    process = SdrHdrToHdrgm(
        sdr_path=sdr_path,
        hdr_path=hdr_path,
        hdrgm_path=output_path,
        preset=preset,
        tag=tag,
        keep_temp_files=keep_temp_files,
    )
    process.validate()
    process.run()


def run_sdr_sdr_ev(
    sdr_path: str,
    sdrev_path: str,
    ev: float,
    output_path: str | None = None,
    preset: Preset = Preset.default,
    tag: bool = False,
    keep_temp_files: bool = False,
):
    from hdr_gainmap.gen.sdr_sdr_ev_to_hdrgm import SdrSdrEvToHdrgm

    process = SdrSdrEvToHdrgm(
        sdr_path=sdr_path,
        sdr_ev_path=sdrev_path,
        ev=ev,
        hdrgm_path=output_path,
        preset=preset,
        tag=tag,
        keep_temp_files=keep_temp_files,
    )
    process.validate()
    process.run()


def run_sdr_ev(
    sdr_path: str,
    ev: float,
    output_path: str | None = None,
    preset: Preset = Preset.default,
    tag: bool = False,
    keep_temp_files: bool = False,
):
    from hdr_gainmap.gen.sdr_ev_to_hdrgm import SdrToHdrgm

    process = SdrToHdrgm(
        sdr_path=sdr_path,
        ev=ev,
        hdrgm_path=output_path,
        preset=preset,
        tag=tag,
        keep_temp_files=keep_temp_files,
    )
    process.validate()
    process.run()


def run_sdr_tm(
    sdr_path: str,
    output_path: str | None = None,
    preset: Preset = Preset.default,
    tag: bool = False,
    keep_temp_files: bool = False,
):
    from hdr_gainmap.gen.sdr_to_hdrgm import SdrTmToHdrgm

    process = SdrTmToHdrgm(
        sdr_path=sdr_path,
        hdrgm_path=output_path,
        preset=preset,
        tag=tag,
        keep_temp_files=keep_temp_files,
    )
    process.validate()
    process.run()


def run_dir(
    dir: str,
    preset: Preset = Preset.default,
    tag: bool = False,
    keep_temp_files: bool = False,
):
    print(f"Batch mode (sdr + hdr) on directory: {dir}")
    from hdr_gainmap.gen import sdr_hdr_to_hdrgm

    sdr_hdr_to_hdrgm.process_folder(
        input_directory=dir,
        keep_temp_files=keep_temp_files,
    )


@app.command()
def main(
    sdr: str = typer.Option(None, "--sdr", "-s", help="Path to sdr image (.jpg)"),
    hdr: str = typer.Option(None, "--hdr", "-H", help="Path to hdr image (.avif)"),
    sdrev: str = typer.Option(
        None, "--sdrev", "-se", help="Path to sdr image with ev (.jpg)"
    ),
    ev: float = typer.Option(None, "--ev", "-e", help="EV value (ex: 2)", min=0, max=4),
    output: str = typer.Option(
        None, "--output", "-o", help="Path to output image (.jpg)"
    ),
    preset: Preset = typer.Option(
        Preset.default, "--preset", "-p", help="Preset for process"
    ),
    tag: bool = typer.Option(False, "--tag", "-t", help="Add hdr tag on image"),
    keep_temp_files: bool = typer.Option(
        False, "--keep-temp-files", "-k", help="Keep gain map and metadata"
    ),
    dir: str = typer.Option(
        None, "--dir", "-d", help="Dir path to process (sdr + hdr)"
    ),
):
    """
    Convert SDR/HDR images to Ultra HDR (Gain Map).

    Sample usage:

    SDR+HDR: --sdr img.jpg --hdr img.avif
    SDR+SDR_EV+EV: --sdr img.jpg --sdrev img_ev.jpg --ev 2
    SDR+EV: --sdr img.jpg --ev 2

    Batch: --dir /path/to/dir
    """

    # sdr + hdr mode
    if sdr and hdr:
        run_sdr_hdr(sdr, hdr, output, preset, tag, keep_temp_files)
        return

    # sdr + sdr ev mode
    if sdr and sdrev and ev is not None:
        run_sdr_sdr_ev(sdr, sdrev, ev, output, preset, tag, keep_temp_files)
        return

    # sdr ev mode
    if sdr and ev is not None:
        run_sdr_ev(sdr, ev, output, preset, tag, keep_temp_files)
        return

    # sdr tonemap mode
    if sdr is not None:
        run_sdr_tm(sdr, output, preset, tag, keep_temp_files)
        return

    # Batch mode
    if dir:
        run_dir(dir, preset, tag, keep_temp_files)
        return

    # else
    raise typer.BadParameter(
        "Cannot detect ht wanted mode !\n"
        "Samples:\n"
        "  SDR+HDR: --sdr img.jpg --hdr img.avif\n"
        "  SDR+SDR_EV+EV: --sdr img.jpg --sdrev img_ev.jpg --ev 2\n"
        "  SDR+EV: --sdr img.jpg --ev 2\n"
        "  Batch SDR+HDR: --dir /chemin/du/dossier"
    )


def run() -> None:
    import sys

    if len(sys.argv) == 1:
        sys.argv.append("--help")

    app()
