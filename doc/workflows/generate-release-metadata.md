## Inputs

`exclude-files` optionally supplies a JSON array of exact repository-relative
changed-file paths that must not create releases. It defaults to `[]`, preserving
existing callers. Invalid JSON or non-string array entries fail detection.
Trigger path filters alone do not exclude files from a release plan when another
changed file triggers the workflow. This repository excludes its internal CI
workflows using this input in `self-tagging.yaml`.

<!-- AUTO-DOC-INPUT:START - Do not remove or modify this section -->

|                                  INPUT                                  |  TYPE  | REQUIRED |    DEFAULT    |                                        DESCRIPTION                                        |
|-------------------------------------------------------------------------|--------|----------|---------------|-------------------------------------------------------------------------------------------|
| <a name="input_exclude-files"></a>[exclude-files](#input_exclude-files) | string |  false   |    `"[]"`     | JSON array of exact repository-relative <br>paths to exclude from release <br>detection.  |
|    <a name="input_index-split"></a>[index-split](#input_index-split)    | number |  false   |      `1`      |            '1' for reporoot/folder1, '2' for <br>reporoot/folder1/subfolder1              |
|     <a name="input_rootFolder"></a>[rootFolder](#input_rootFolder)      | string |  false   |  `"modules"`  |    Folder location relative to root <br>of repository to create release <br>tags for      |
|              <a name="input_type"></a>[type](#input_type)               | string |  false   | `"terraform"` |                                 'actions' or 'terraform'                                  |
|  <a name="input_wiki-enabled"></a>[wiki-enabled](#input_wiki-enabled)   | string |  false   |   `"false"`   |                         Write Terraform docs to wiki <br>or not                           |

<!-- AUTO-DOC-INPUT:END -->


## Outputs

<!-- AUTO-DOC-OUTPUT:START - Do not remove or modify this section -->
No outputs.
<!-- AUTO-DOC-OUTPUT:END -->