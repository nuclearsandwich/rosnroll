#!/bin/sh


echo "Resetting rosdistro repository."
cd rosdistro
git fetch origin
git reset --hard origin/demos/new-rosdistro

echo "Running clone-rosdistro.py command from rosdistro directory."
CMD="python3 ../../clone-rosdistro.py \
  --source-ref demos/new-rosdistro \
  --source eloquent \
  --dest verystable \
  --release-org $GITHUB_ORG"
echo $CMD
exec $CMD
