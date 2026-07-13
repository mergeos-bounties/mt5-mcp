from typer.testing import CliRunner

from mt5_mcp.cli import app

runner = CliRunner()


def test_version():
    r = runner.invoke(app, ["version"])
    assert r.exit_code == 0
    assert "0.1.0" in r.stdout


def test_demo():
    r = runner.invoke(app, ["demo"])
    assert r.exit_code == 0
    assert "demo complete" in r.stdout


def test_tools_list():
    r = runner.invoke(app, ["tools", "list"])
    assert r.exit_code == 0
    assert "mt5_order_send" in r.stdout
