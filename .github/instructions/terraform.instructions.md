---
name: "Instructions for creating reusable Github Actions Workflows"
description: "Create or modify reusable Github Actions workflow templates."
applyTo: ".github/workflows/*.yaml,.github/actions/**/*.yaml"
excludeAgent: []
---

## Important

- When creating a pull request, the description MUST include the pull_request template defined in [the pull request template](/.github/pull_request_template.md).
  - Make sure the description "TODO: Replace this inner text with a useful message
for users of the affected modules!" is replaced with a relevant description
  - The pull request MUST be labeled with one of the following labels:
    - `patch` - for backward-compatible bug fixes
    - `minor` - for backward-compatible new features
    - `major` - for changes that break backward compatibility

## Specific to this repository

- This repository creates reusable GitHub Actions Workflows for various tasks. The workflows used in other repositories within the Github Enterprise.
  - Read [this doc](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) for general guidelines 
- `${{secrets.}}` and `${{vars.}}` are not defined in this repository. They are expected to be defined in the repository where the reusable workflow is called from, or at the organization level.
- Each workflow is defined in a separate YAML file under the `workflows` directory.
  - More details about each workflow can be found in the [doc/workflows](/doc/workflows) directory.
- A reusable workflow may or may not use one ore more actions defined in the [`actions`](/.github/actions) directory.
  - Each action has its own subfolder
  - Create actions where suitable to avoid excessive code duplication within or across multiple workflows.