ROS 'N Roll
===========

Prototype utilities and demo scripts for rolling rosdistro releases.

## Setup

Create a python3 virtualenv and source it.
The scripts are tested on Python 3.5 but should work on Python 3.6 or 3.7.

Clone this repository with its submodules in order to get the sample rosdistro repos.

    git clone --recurse-submodules https://github.com/nuclearsandwich/rosnroll


Install the script dependencies.

    cd rosnroll
    pip install -r requirements.txt

Make sure rosdep is initialized if it isn't already.

    sudo rosdep init

Configure a GitHub access token and test organization.
These are required for demos to create release repositories.
The token only needs public repository access and to belong to a member of the target GitHub organization with repository creation permissions.


    GITHUB_TOKEN={token with public repository access}
    GITHUB_ORG={GitHub organization name. Example 'nuclearsandwich-ros'}
    export GITHUB_ORG GITHUB_TOKEN

If you are not already using a credential helper for https git remotes you will need to set one up:
https://git-scm.com/docs/gitcredentials

The shell you've just configured may be used for the following demos:

## Demo scenarios

### Creating a new rosdistro from an existing one

This demo showcases creating a new rosdistro from a sample rolling rosdistro.
To run the demo:

    cd new-rosdistro
    sh run_demo.sh

For a detailed description see new-rosdistro/README.md


### Updating the platform of an existing rosdistro

This demo showcases updating the platform of a rolling rosdistro in-place.
To run the demo:

    cd update-platform
    sh run_demo.sh

For a detailed description see update-platform/README.md


### Updating a cloned rosdistro 

The first time a new stable rosdistro is created, not all repositories may bloom succesfully.
This demo showcases re-running a clone to try failed repositories again.

To run the demo:
    cd update-rosdistro
    sh run_demo.sh

For a detailed description see update-platform/README.md

