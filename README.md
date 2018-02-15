error-number-fixer
==========

Some out-of-the-box hook for pre-commit.

See also: https://github.com/pre-commit/pre-commit


### Using pre-commit-hooks with pre-commit

Add this to your `.pre-commit-config.yaml`

    -   repo: git@github.com:vikramarsid/code_fixers.git
        sha: v1.2.0  # Use the ref you want to point at
        hooks:
        -   id: error_number_fixer


### Hooks available

- `error_number_fixer` - Fixes error numbers in plugin source files.


### As a standalone package

If you'd like to use these hooks, they're also available as a standalone
package.

Simply `pip install pre-commit-hooks`
