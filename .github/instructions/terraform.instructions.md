---
name: "Instructions for creating reusable Github Actions Workflows"
description: "Create or modify reusable Github Actions workflow templates."
applyTo: ".github/workflows/*.yaml,.github/actions/**/*.yaml"
excludeAgent: []
---

## Specific to this repository

- This repository creates reusable GitHub Actions Workflows for various tasks. The workflows used in other repositories within the Github Enterprise.
  - Read [this doc](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows) for general guidelines 
- `${{secrets.}}` and `${{vars.}}` are not defined in this repository. They are expected to be defined in the repository where the reusable workflow is called from, or at the organization level.
- Each workflow is defined in a separate YAML file under the `workflows` directory.
  - More details about each workflow can be found in the [doc/workflows](/doc/workflows) directory.
- A reusable workflow may or may not use one ore more actions defined in the [`actions`](/.github/actions) directory.
  - Each action has its own subfolder
  - Create actions where suitable to avoid excessive code duplication within or across multiple workflows.