from typer.testing import CliRunner

runner = CliRunner()


# def test_read_config_runs() -> None:
#
#     r = runner.invoke(app, ["read_config"])
#     assert r.exit_code == 0
#     assert "app_name" in r.stdout
