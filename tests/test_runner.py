from unittest.mock import patch

from fertility_popeve.annotation.runner import run_vep


def test_run_vep_builds_expected_command():
    with patch("fertility_popeve.annotation.runner.subprocess.run") as run:
        run_vep("input.vcf.gz", "output.vep.vcf")

    command = run.call_args.args[0]
    assert command[0] == "vep"
    assert "--offline" in command
    assert command[command.index("-i") + 1] == "input.vcf.gz"
    assert command[command.index("-o") + 1] == "output.vep.vcf"
    assert run.call_args.kwargs == {"check": True}
