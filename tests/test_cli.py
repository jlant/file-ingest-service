from typer.testing import CliRunner

from python_service_template.cli import app

runner = CliRunner()


def test_hello_runs() -> None:
    r = runner.invoke(app, ["hello", "--name", "Jeremiah"])
    assert r.exit_code == 0
    assert "Hello, Jeremiah" in r.stdout
