#!/bin/sh


echo "Resetting rosdistro repository."
cd rosdistro
git fetch origin
git checkout -t origin/demos/update-platform || git checkout demos/update-platform
git reset --hard origin/demos/update-platform

echo "Running clone-rosdistro.py command from rosdistro directory."
CMD="python3 ../../clone-rosdistro.py \
  --source-ref demos/update-platform~1 \
  --source eloquent \
  --dest eloquent \
  --release-org $GITHUB_ORG"
echo $CMD
exec $CMD
