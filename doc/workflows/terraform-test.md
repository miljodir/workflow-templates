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
    uses: miljodir/workflow-templates/.github/workflows/terraform-test.yaml@<full-commit-sha>
    with:
      terraform-version: "1.x"
      opentofu-version: "1.13.9"
```

Use the PR's full commit SHA before merge. Releases follow this repository's
workflow-specific tags: `terraform-test/<version>` and the floating
`terraform-test/v<major>` tag. A full SHA or version tag is preferable for
reproducibility; do not use a version tag until it actually exists.

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

| Input | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `engine` | string | false | `both` | `both`, `terraform`, or `opentofu`; other values fail. |
| `terraform-version` | string | false | `1.x` | Terraform setup version constraint; mock tests require >= 1.7. |
| `opentofu-version` | string | false | `latest` | OpenTofu setup version; pin a version supporting the module's features. |
| `working-directory` | string | false | `.` | Module directory relative to the caller checkout. |
| `test-directory` | string | false | `tests` | Test directory relative to the module; root tests are also discovered. |
| `prepare-script` | string | false | empty | Bash script relative to the module, run before init in the disposable copy. |
| `test-override-directory` | string | false | empty | Directory relative to the module, copied after validate. |

<!-- AUTO-DOC-INPUT:END -->

Paths must be relative, without `..` components. A configured script must exist;
a configured override directory must contain at least one `*_override.tf` or
`*_override.tf.json`. Overrides cannot replace existing root files. Script,
formatting, initialization, validation, and test failures are propagated. There
is no option to skip validation or tests.

## Secrets and outputs

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
      opentofu-version: "1.13.9"
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
those callers. Files are copied **after** validation and before tests, so
validation still checks the pre-override configuration. Tests evaluate the
overridden configuration. Keep overrides limited to test-only output metadata;
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
pre-init synthetic dependency substitution, post-validation output overrides,
and both engines. Repository `Actionlint` checks the workflow syntax and shell
scripts. The checks workflow is excluded from workflow release tagging; the
reusable `terraform-test.yaml` receives its own versioned release.
