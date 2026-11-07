import os
from pathlib import Path
import subprocess
import tempfile

import yaml


WORKFLOW = Path(".github/workflows/terraform-test.yaml")
ENGINE = os.environ["CHECK_ENGINE"]
STEPS = yaml.safe_load(WORKFLOW.read_text())["jobs"]["test"]["steps"]


def workflow_script(name):
    matches = [step["run"] for step in STEPS if step.get("name") == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one workflow step: {name}")
    return matches[0]


DIRECTORY_GUARD = workflow_script("Require explicitly configured test directory")
NATIVE_TEST = workflow_script("Run native tests and require executed tests")
INIT = workflow_script("Initialize without a backend")
VALIDATE = workflow_script("Validate before test-only output overrides")
PASSING_TEST = '''
run "synthetic_plan" {
  command = plan
  assert {
    condition     = output.value
    error_message = "Synthetic assertion."
  }
}
'''


def execute(script, directory, env):
    return subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=directory,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def require_success(script, directory, env):
    result = execute(script, directory, env)
    if result.returncode != 0:
        raise AssertionError(result.stdout)
    return result.stdout


def require_rejection(script, directory, env, diagnostic):
    result = execute(script, directory, env)
    if result.returncode == 0 or diagnostic not in result.stdout:
        raise AssertionError(
            f"Expected rejection containing {diagnostic!r}; "
            f"exit={result.returncode}\n{result.stdout}"
        )


def check_case(case):
    with tempfile.TemporaryDirectory(prefix="native-guard-") as temporary:
        directory = Path(temporary)
        (directory / "main.tf").write_text('output "value" {\n  value = true\n}\n')
        env = {
            **os.environ,
            "TF_IN_AUTOMATION": "true",
            "TF_INPUT": "false",
            "CHECK_ENGINE": ENGINE,
            "CHECK_DIRECTORY": str(directory),
            "TEST_DIRECTORY": "tests",
            "RUNNER_TEMP": str(directory),
        }
        test_file = directory / "root.tftest.hcl"
        if case == "assertion":
            test_file.write_text(PASSING_TEST.replace("output.value", "!output.value"))
        elif case == "zero-run":
            test_file.write_text("variables {}\n")
        elif case == "missing-directory":
            test_file.write_text(PASSING_TEST)
        elif case != "missing-files":
            raise AssertionError(f"Unknown case: {case}")

        require_success(INIT, directory, env)
        require_success(VALIDATE, directory, env)
        if case == "missing-directory":
            # Prove the unchanged root test passes before naming a missing directory.
            require_success(NATIVE_TEST, directory, env)
            env["TEST_DIRECTORY"] = "missing"
            require_rejection(
                DIRECTORY_GUARD,
                directory,
                env,
                "::error::Explicit test-directory does not exist or is not a directory",
            )
        else:
            diagnostic = {
                "assertion": "Error: Test assertion failed",
                "zero-run": "::error::The native test command must report at least one passing run",
                "missing-files": "::error::No test files found in the module root or test-directory",
            }[case]
            require_rejection(NATIVE_TEST, directory, env, diagnostic)
        print(f"{ENGINE}: {case} rejected as required")


for case in ("assertion", "zero-run", "missing-files", "missing-directory"):
    check_case(case)
