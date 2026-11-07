from copy import deepcopy
import os
from pathlib import Path
import subprocess
import tempfile

import yaml


WORKFLOW = Path(".github/workflows/terraform-test.yaml")
ENGINE = os.environ["CHECK_ENGINE"]
DOCUMENT = yaml.safe_load(WORKFLOW.read_text())
STEPS = DOCUMENT["jobs"]["test"]["steps"]


def workflow_step(steps, name):
    matches = [step for step in steps if step.get("name") == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one workflow step: {name}")
    return matches[0]


def workflow_script(name):
    return workflow_step(STEPS, name)["run"]


def check_structure(document):
    job = document["jobs"]["test"]
    steps = job["steps"]
    native = workflow_step(steps, "Run native tests and require executed tests")
    directory = workflow_step(steps, "Require explicitly configured test directory")
    init = workflow_step(steps, "Initialize without a backend")
    if "if" in job or "if" in native:
        raise AssertionError("Native tests must execute unconditionally in the test job")
    if directory.get("if") != "inputs.test-directory != ''":
        raise AssertionError("Explicit-directory guard condition must match nonempty input")
    # PyYAML's YAML 1.1 reader treats the unquoted Actions `on` key as True.
    trigger = document.get("on", document.get(True))
    if trigger["workflow_call"]["inputs"]["test-directory"]["default"] != "":
        raise AssertionError("Omitted directory must retain the empty sentinel default")
    if job["env"]["TEST_DIRECTORY"] != "${{ inputs.test-directory || 'tests' }}":
        raise AssertionError("Directory environment must map the input to its native default")
    if job["env"]["CHECK_ENGINE"] != "${{ matrix.engine == 'opentofu' && 'tofu' || 'terraform' }}":
        raise AssertionError("Regression engines must match the actual job engine mapping")
    if steps.index(directory) >= steps.index(init):
        raise AssertionError("Directory guard must run before initialization")
    if job.get("continue-on-error", False) is not False:
        raise AssertionError("Job must propagate failures")
    for step in (native, directory, init):
        if step.get("continue-on-error", False) is not False:
            raise AssertionError("Guard and initialization steps must propagate failures")
        shell = step.get(
            "shell",
            job.get("defaults", {}).get("run", {}).get(
                "shell", document.get("defaults", {}).get("run", {}).get("shell")
            ),
        )
        # Explicit Actions `bash` means bash --noprofile --norc -e -o pipefail {0}.
        # The implicit Linux shell instead lacks pipefail, so absence is unsafe.
        if shell != "bash":
            raise AssertionError("Explicit Actions bash shell is required for pipefail")


def check_structural_mutations():
    mutations = (
        ("disabled-native", lambda doc: workflow_step(
            doc["jobs"]["test"]["steps"], "Run native tests and require executed tests"
        ).update({"if": False})),
        ("disabled-directory", lambda doc: workflow_step(
            doc["jobs"]["test"]["steps"], "Require explicitly configured test directory"
        ).update({"if": False})),
        ("missing-pipefail-shell", lambda doc: doc["jobs"]["test"]["defaults"]["run"].pop("shell")),
        ("wrong-directory-mapping", lambda doc: doc["jobs"]["test"]["env"].update(
            {"TEST_DIRECTORY": "tests"}
        )),
    )
    for name, mutate in mutations:
        document = deepcopy(DOCUMENT)
        mutate(document)
        try:
            check_structure(document)
        except AssertionError:
            print(f"{ENGINE}: structural mutation {name} rejected as required")
        else:
            raise AssertionError(f"Structural mutation was accepted: {name}")


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


check_structure(DOCUMENT)
check_structural_mutations()
for case in ("assertion", "zero-run", "missing-files", "missing-directory"):
    check_case(case)
