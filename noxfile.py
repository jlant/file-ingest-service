import nox

PY = ["3.11", "3.12"]


@nox.session(python=PY)
def tests(session: nox.Session) -> None:
    session.install(".")
    session.install("pytest", "pytest-cov")
    session.run("pytest", "-q")


@nox.session(python=PY)
def lint(session: nox.Session) -> None:
    session.install(".")
    session.install("ruff", "pyright")
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")
    session.run("pyright")


@nox.session(python=PY)
def fmt(session: nox.Session) -> None:
    session.install("ruff")
    session.run("ruff", "format", "src", "tests")
    session.run("ruff", "check", "--fix", "src", "tests")
