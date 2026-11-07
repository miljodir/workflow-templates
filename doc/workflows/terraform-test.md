# Terraform and OpenTofu module tests

Runs formatting, backend-free initialization, validation, and native tests on
`ubuntu-latest`. By default, independent jobs check both engines; a failure in
either fails the caller. Each job has a 20-minute timeout and runs in a disposable
copy of the caller's checkout. Neither dependency fixtures nor output overrides
change the published module.

## Caller

Replace the standalone `.github/workflows/terraform-test.yaml` with:

```yaml
name: Module tests
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: module-tests-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  test:
    uses: miljodir/workflow-templates/.github/workflows/terraform-test.yaml@terraform-test/v0
    with:
      terraform-version: "1.x"
      opentofu-version: "1.x"
```

`1.x` floats to the latest stable OpenTofu 1.x release; use a full version
such as `1.13.9` for reproducible runs.

`terraform-test/v0` is a moving major tag that tracks the latest `0.x`
release; pre-1.0 releases may include breaking changes. For a fixed reference, pin a version tag such as
`terraform-test/0.1.0`, or a full commit SHA for the strongest
reproducibility.

No secrets are declared or required. Do **not** add `secrets: inherit`, SSH keys,
cloud credentials, `id-token: write`, `pull_request_target`, or a self-hosted
runner. Fork PRs can run with `contents: read`, subject to GitHub's normal
first-contributor approval and repository Actions policies.

Keep existing tests and test-only fixtures in the module repository. If using
path filters, include all module, test, fixture, script, lockfile, and caller
workflow changes. Omitting path filters avoids accidentally missing coverage.
Existing required status checks may need updating because the job names change.
For multiple modules or engine versions, use caller-level matrix jobs with
`working-directory` or version inputs.

## Inputs

<!-- AUTO-DOC-INPUT:START - Do not remove or modify this section -->

|                                                 INPUT                                                 |  TYPE  | REQUIRED |  DEFAULT   |                                                                        DESCRIPTION                                                                         |
|-------------------------------------------------------------------------------------------------------|--------|----------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                          <a name="input_engine"></a>[engine](#input_engine)                           | string |  false   |  `"both"`  |                Engines to check: both, terraform, <br>or opentofu. Selecting one does <br>not establish compatibility with the <br>other.                  |
|           <a name="input_opentofu-version"></a>[opentofu-version](#input_opentofu-version)            | string |  false   | `"latest"` |                                        OpenTofu version; pin a release <br>supporting the module's test features.                                          |
|              <a name="input_prepare-script"></a>[prepare-script](#input_prepare-script)               | string |  false   |            |          Optional Bash script relative to <br>the module, run before init <br>in a disposable copy to <br>install synthetic dependency fixtures.           |
|          <a name="input_terraform-version"></a>[terraform-version](#input_terraform-version)          | string |  false   |  `"1.x"`   |                                         Terraform version constraint; mocked tests <br>require Terraform >= 1.7.                                           |
|              <a name="input_test-directory"></a>[test-directory](#input_test-directory)               | string |  false   |            | Test directory relative to the <br>module. Empty uses native tests <br>default; an explicit directory must <br>exist. Root tests are also <br>discovered.  |
| <a name="input_test-override-directory"></a>[test-override-directory](#input_test-override-directory) | string |  false   |            |         Optional output override directory relative <br>to the module; copied after <br>Terraform validation but before OpenTofu <br>validation.           |
|          <a name="input_working-directory"></a>[working-directory](#input_working-directory)          | string |  false   |   `"."`    |                                                   Module directory relative to the <br>caller checkout.                                                    |

<!-- AUTO-DOC-INPUT:END -->

Paths must be relative, without `..` components. A configured script must exist;
`test-directory` defaults to an empty sentinel, effectively the native `tests`
directory. Omitting it (or leaving it empty) permits root-only tests when there
is no `tests` directory. Any explicitly named directory, including `tests`, must
exist after preparation and before initialization; a typo cannot be masked by a
passing root-level suite. The same discovery and existence rules apply to both engines.
a configured override directory must contain at least one `*_override.tf` or
`*_override.tf.json`. Overrides cannot replace existing root files. Script,
formatting, initialization, validation, and test failures are propagated. There
is no option to skip validation or tests.

## Secrets

<!-- AUTO-DOC-SECRETS:START - Do not remove or modify this section -->
No secrets.
<!-- AUTO-DOC-SECRETS:END -->

## Outputs

No caller secrets or workflow outputs.

<!-- AUTO-DOC-OUTPUT:START - Do not remove or modify this section -->
No outputs.
<!-- AUTO-DOC-OUTPUT:END -->

## Test discovery and safety

Terraform discovers `*.tftest.hcl` and `*.tftest.json` in the module root and the
configured test directory. OpenTofu also discovers `*.tofutest.hcl` and
`*.tofutest.json`; it gives its engine-specific files precedence over matching
Terraform files. Missing files fail explicitly. A successful native command must
also report at least one passing run: files without runs and entirely skipped
suites are not coverage. Test failures fail the job, even if other runs pass.

Use `mock_provider` for every cloud provider, synthetic values, and assertions
that cover module behavior. `command = plan` alone is **not** a guarantee against
cloud API calls, since unmocked data sources can still read real services.
`terraform test` and `tofu test` can create infrastructure with unmocked providers.
This workflow executes repository code, not a sandbox or proof that every
provider is mocked. Review tests and preparation scripts accordingly.

Logs use non-verbose native output: no `-verbose`, state/plan dumps, debug
logging, or uploaded artifacts. Formatting lists offending filenames without
printing diffs. Native diagnostics and caller scripts can still reveal literal
values in code, so all test data and script output must be suitable for public
logs. Backend initialization is disabled; provider and public module downloads
still need network access. Lockfiles in the source copy are used normally;
generated lockfiles and state remain in the disposable job copy.

## Private dependencies and fixtures

Provider mocking and `override_module` do not prevent initialization from
downloading module sources, including modules with `count = 0` and transitive
dependencies. Do not solve this by exposing a key to PR code.

Use a reviewed `prepare-script` to substitute narrowly scoped, synthetic
fixtures **before** initialization:

```yaml
    with:
      prepare-script: scripts/prepare-test-fixtures.sh
      test-override-directory: tests/overrides
      opentofu-version: "1.x"
```

The script runs with Bash `-euo pipefail` from the copied module directory.
It should match an exact expected module source and fail if the expected source
or occurrence count changes, then replace it with a local fixture. Fixtures
should preserve the dependency's relevant input types and output shapes, with
clearly synthetic values. Assert interactions with those outputs in the tests;
do not simply remove module blocks or output references.

For a private dependency reached through a public registry module, prepare a
reviewed local copy of the **pinned public parent module**, replace only its
private child source, and redirect the root module to that copy. Remove any
registry-only `version` argument when redirecting to a local source. If obtaining
the parent during CI, pin the download and verify its checksum. Do not edit a
downloaded `.terraform` tree after init fails, depend on global Git/SSH config,
silently fall back after failed downloads, or copy private implementation code
into a public repository. An upstream version change must require fixture review.

The workflow emits a notice and job summary whenever preparation is enabled.
**With substitution, validation checks the prepared root configuration and
fixture contracts, not the original private module's implementation,
compatibility, source accessibility, or full integration behavior.** Initialization
and validation still run and must succeed. Without preparation they check the
original dependencies and fail if these cannot be downloaded. Real private
integration coverage requires a separate trusted workflow; it is not established
by these credential-free tests.

## Test-only output overrides

Some modules need root-only overrides (for example, marking outputs sensitive
when tested as a root module). Enable `test-override-directory` explicitly for
those callers. Terraform validates **before** these overrides are copied.
OpenTofu validates **after** they are copied, because its validation can reject
otherwise usable modules whose root outputs need `sensitive = true`.
Without configured output overrides, both engines validate the pre-override
configuration. Tests always evaluate the overridden configuration when enabled.

OpenTofu's job emits a notice and summary explaining that its validation checks
the test-adjusted output metadata, **not the original root output metadata**.
This is intentional ordering, not a retry or suppression of validation errors;
the applicable validation command always runs and must succeed.
Keep overrides limited to test-only output metadata;
changing output expressions or resource behavior reduces what the tests prove.
The workflow's own fixture deliberately changes an expression to verify ordering,
not as a recommended consumer pattern.

## Engine compatibility

Both engines accept the shared `.tftest.hcl` mock-provider and assertion syntax.
Terraform mock providers require >= 1.7. OpenTofu's versioned 1.9 test
documentation describes mocking, but features used by an individual suite can
require newer versions: indexed `override_resource`/`override_data` targets
require OpenTofu >= 1.12. The smoke caller pins OpenTofu 1.13.9 and exercises
Terraform 1.7.0 plus the latest 1.x selected by setup.

Passing the smoke suite is not proof every module works on both engines.
Terraform-specific `action`/`action_trigger` syntax and module version
constraints may be unsupported by OpenTofu. Keep `engine: both` unless an actual
compatibility check establishes a limitation. In that case use
`engine: terraform` (or `opentofu`) explicitly and document the unsupported
engine and reason in the consumer's testing documentation. This is a deliberate
coverage limitation, not a passing check for the excluded engine. Do not relax
module constraints or strip unsupported resources just to produce a green run.

References:
[Terraform test mocking](https://developer.hashicorp.com/terraform/language/tests/mocking),
[OpenTofu test command](https://opentofu.org/docs/cli/commands/test/),
[OpenTofu action support tracking](https://github.com/opentofu/opentofu/issues/3309).

## Workflow regression checks

`terraform-test-checks.yaml` calls the reusable workflow directly on PRs and
main pushes. It covers a real mocked provider apply, a custom test directory,
pre-init synthetic dependency substitution, engine-specific output override ordering,
and both engines. Repository `Actionlint` checks the workflow syntax and shell
scripts. The checks workflow is excluded from workflow release tagging; the
reusable `terraform-test.yaml` receives its own versioned release.

Release detection explicitly excludes the internal checks, Actionlint and
self-tagging workflows using `generate-release-metadata`'s `exclude-files` input;
trigger path exclusions alone are insufficient. Adding this backward-compatible
input also intentionally versions the reusable release-metadata workflow.

Additional callers exercise exclusively root-level `.tftest.json` tests on both
engines and exclusively `.tofutest.hcl`/`.tofutest.json` files on OpenTofu.
The root-only JSON caller omits `test-directory`; the fixture caller names the
existing custom `checks` directory. A temporary negative Actions run configured
the JSON caller with `test-directory: missing` while retaining its passing root
test, proving both engines fail the explicit-directory guard; the caller was
restored after verification.

Permanent `Negative guards` jobs run on both engines for assertion failures,
zero-run suites, missing files and an explicit missing directory with an unchanged
passing root test. The harness reads the actual `run` scripts from
`terraform-test.yaml` and executes them with Bash `-euo pipefail` and real engine
binaries; it does not copy the guard implementation. It requires both nonzero
exit status and the expected diagnostic, so setup errors cannot masquerade as
expected rejections. The directory case first proves the root test passes.
These are guard-script regression tests, not intentionally failing workflow-call
jobs; the existing positive callers continue to verify workflow wiring and
engine-specific step conditions. The regression jobs use read-only permissions
and do not expose any failure-suppression input to consumers.

The harness also checks the actual job/step structure: native tests cannot be
conditional, failures cannot be suppressed, explicit directory validation must
map the nonempty input and precede initialization, and an explicit Actions Bash
shell must guarantee pipeline failure propagation. In-memory mutations disabling
either guard, removing the explicit shell, or breaking the directory input
mapping must be rejected by the same structural checker. These contract checks
intentionally require review when changing workflow wiring.
The sensitive-output fixture uses a mocked `random_password`, whose root output
needs a `sensitive = true` override for OpenTofu validation and both engines' tests.
