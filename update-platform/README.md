# Updating a rosdistro's platforms

This demo showcases the migration of a rosdistro from one platform to another using eloquent as a stand in for the rolling rosdistro.

## Prerequisites

All of these are pre-configured for this demo but will be required to use the script on other rosdistro repositories.

* A local clone of a rosdistro repository must be available.
* A git commit id or ref name which has the previous platform and desired repositories in the source distribution.
* The HEAD distribution.yaml should specify the desired target platforms and should have an empty `repositories` field.
  For an example see the `rosdistro/eloquent/distribution.yaml` file relative to this directory.
  If you look at the same file one commit previously, you'll see it contains a different platform and the full complement of repositories.

## Limitations and known issues

When bootstrapping a new platform many dependencies will be missing in the rosdep database.
The script currently blocks indefinitely when a rosdep failure occurs and requires the operator to clear it by answering 'no'.
For the purposes of the demo repositories with known issues are currently skipped with an error preventing their release.

