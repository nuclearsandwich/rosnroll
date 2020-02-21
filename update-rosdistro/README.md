# Updating a released rosdistro

This demo showcases updating a recently-released "verystable" rosdistro using eloquent as a stand in for the rolling rosdistro.
The variants and xacro releases are missing and will be retried.
Other missing releases are due to existing issues with bloom interactivity and while they will be retried they are not expected to succeed.

## Prerequisites

All of these are pre-configured for this demo but will be required to use the script on other rosdistro repositories.

* A local clone of a rosdistro repository must be available.
* The local rosdistro index must already have an entry for the target distribution.
* The distribution.yaml must exist and will have some repositories already but repositories which failed to release will have no release version.
  For an example see the `rosdistro/verystable/distribution.yaml` file relative to this directory.

## Limitations and known issues

Bloom has unsuppressable interactivity during some release commands used by the clone script.
Repositories that use this interactivity will block the script until the operator enters the necessary data.
For the demo, repositories with known interactivity are guarded for and have an error raised preventing them from being released.
Including:

* fmi_adapter_ros2: Requests version and tag interactively
* behaviortree_cpp_v3: Requests tag interactively
* system_modes: Requests version interactively
* urdfdom_headers: Requests version interactively

Although an attempt is made to move bloom refs from the source release track to the destination, patches applied during bloom releases aren't being honored.
The result is that bloom will succeed but the released package may ultimately fail to build or function incorrectly because of missing patches.
There are a number of repostories this is known to affect include ament_cmake, ros_workspace, and rmw_implementation among others. 

If a release has been tagged and is part of the devel branch for the source distribution but is not yet released in that distribution then this script will release that unreleased version rather than the currently released version.

