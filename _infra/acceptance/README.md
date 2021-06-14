# Acceptance Environment and Terraform Workspace

The acceptance environment is used to verify that everything looks good when
using a recent copy of the production data.

Use the helper script for running the normal terraform commands. These should
be ran from the `_infra/` directory since that is where the `.tf` files are
located.

```bash
# Show the terraform plan
./acceptance/terra.sh plan

# Apply the plan after confirmation
./acceptance/terra.sh apply
```

```bash
# Destroy the project when it is no longer needed
./acceptance/terra.sh destroy
```
