import argparse
import copy
import os
import os.path
import subprocess
import sys
import tempfile

from bloom.commands.git.patch.common import get_patch_config, set_patch_config
from bloom.git import inbranch, show

import github
import yaml

from rosdistro import DistributionFile, get_distribution_cache, get_distribution_file, get_index
from rosdistro.writer import yaml_from_distribution_file

def read_tracks_file():
    return yaml.safe_load(show('master', 'tracks.yaml'))

@inbranch('master')
def write_tracks_file(tracks, commit_msg=None):
    if commit_msg is None:
        commit_msg = 'Update tracks.yaml from {}.'.format(sys.argv[0])
    with open('tracks.yaml', 'w') as f:
        f.write(yaml.safe_dump(tracks, indent=2, default_flow_style=False))
    with open('.git/rosdistroclonecommitmsg', 'w') as f:
        f.write(commit_msg)
    subprocess.check_call(['git', 'add', 'tracks.yaml'])
    subprocess.check_call(['git', 'commit', '-F', '.git/rosdistroclonecommitmsg'])


parser = argparse.ArgumentParser(
    description='Import packages from one rosdistro into another one.'
)
parser.add_argument('--source', required=True, help='The source rosdistro name')
parser.add_argument('--source-ref', required=True, help='The git version for the source. Used to retry failed imports without bumping versions.')
parser.add_argument('--dest', required=True, help='The destination rosdistro name')
parser.add_argument('--release-org', required=True, help='The organization containing release repositories')

args = parser.parse_args()

gclient = github.Github(os.environ['GITHUB_TOKEN'])
release_org = gclient.get_organization(args.release_org)
org_release_repos = [r.name for r in release_org.get_repos() if r.name]

# TODO Remove and replace with standard get_index_url
rosdistro_dir = os.path.abspath(os.getcwd())
rosdistro_index_url = 'file://{}/index-v4.yaml'.format(rosdistro_dir)

# Get source rosdistro distributionfile
index = get_index(rosdistro_index_url)
index_yaml = yaml.safe_load(open('index-v4.yaml', 'r'))
# TODO check that these match
source_distribution_file = get_distribution_file(index, args.source)

# TODO check index at source_ref for singleton distribution.yaml file
if len(index_yaml['distributions'][args.source]['distribution']) != 1 or \
        len(index_yaml['distributions'][args.dest]['distribution']) != 1:
            raise RuntimeError('Both source and destination distributions must have a single distribution file.')


source_distfile_at_ref = subprocess.check_output(['git', 'show', '{}:{}/distribution.yaml'.format(args.source_ref, args.source)], universal_newlines=True)
source_distfile_data = yaml.safe_load(source_distfile_at_ref)
source_distribution = DistributionFile(args.source, source_distfile_data)

destpath = index_yaml['distributions'][args.dest]['distribution'][0]
dest_distribution = get_distribution_file(index, args.dest)
new_repositories = []
repositories_to_retry = []
for repo_name, repo_data in sorted(source_distribution.repositories.items()):
    if repo_name not in dest_distribution.repositories:
        new_repositories.append(repo_name)
        dest_distribution.repositories[repo_name] = copy.deepcopy(repo_data)
    elif dest_distribution.repositories[repo_name].release_repository.version is None:
        dest_distribution.repositories[repo_name].release_repository.version = repo_data.release_repository.version
        repositories_to_retry.append(repo_name)
    else:
        # Nothing to do if the release is there.
        pass

print("Found {} new repositories to release:".format(len(new_repositories)), new_repositories)
print("Found {} repositories to retry:".format(len(repositories_to_retry)), repositories_to_retry)

# Copy out an optimistic destination distribution file to bloom everything against.
with open(destpath, 'w') as f:
    f.write(yaml_from_distribution_file(dest_distribution))

repositories_bloomed = []
repositories_with_errors = []

workdir = tempfile.mkdtemp()
os.chdir(workdir)
os.environ['ROSDISTRO_INDEX_URL'] = rosdistro_index_url

for repo_name in sorted(new_repositories + repositories_to_retry):
    try:
        release_spec = dest_distribution.repositories[repo_name].release_repository
        print("Adding repo:", repo_name)
        if release_spec.type != 'git':
            raise ValueError("This script can only handle git repositories.")
        # HACK Skipping repos that are missing deps in focal
        if repo_name in ['cartographer_ros', 'demos', 'gazebo_ros_pkgs', 'geographic_info', 'perception_pcl', 'rmw_connext', 'rmw_opensplice', 'rosidl_typesupport_connext', 'rosidl_typesupport_opensplice', 'teleop_tools', 'vision_opencv']:
            raise ValueError("Dependencies missing for focal")
        remote_url = release_spec.url
        release_repo = remote_url.split('/')[-1][:-4]
        subprocess.call(['git', 'clone', remote_url])
        os.chdir(release_repo)
        tracks = read_tracks_file()

        if release_repo not in org_release_repos:
            release_org.create_repo(release_repo)
        new_release_repo_url = 'https://github.com/{}/{}.git'.format(args.release_org, release_repo)
        subprocess.check_call(['git', 'remote', 'rename', 'origin', 'oldorigin'])
        subprocess.check_call(['git', 'remote', 'set-url', '--push', 'oldorigin', 'no_push'])
        subprocess.check_call(['git', 'remote', 'add', 'origin', new_release_repo_url])

        if args.source != args.dest:
            # Copy the source track to the new destination.
            dest_track = copy.deepcopy(tracks['tracks'][args.source])
            dest_track['ros_distro'] = args.dest
            tracks['tracks'][args.dest] = dest_track
            ls_remote = subprocess.check_output(['git', 'ls-remote', '--heads', 'oldorigin', '*{}*'.format(args.source)], universal_newlines=True)
            for line in ls_remote.split('\n'):
                if line == '':
                    continue
                obj, ref = line.split('\t')
                ref = ref[11:] # strip 'refs/heads/'
                newref = ref.replace(args.source, args.dest)
                subprocess.check_call(['git', 'branch', newref, obj])
                if newref.startswith('patches/'):
                    # Update parent in patch configs. Without this update the
                    # patches will be rebased out when git-bloom-release is
                    # called because the configured parent won't match the
                    # expected source branch.
                    config = get_patch_config(newref)
                    config['parent'] = config['parent'].replace(args.source, args.dest)
                    set_patch_config(newref, config)
            write_tracks_file(tracks, 'Copy {} track to {} with clone.py.'.format(args.source, args.dest))
        else:
            dest_track = tracks['tracks'][args.dest]

        # Configure next release to re-release previous version into the
        # destination.  A version value of :{ask} will fail due to
        # interactivity and :{auto} may result in a previously unreleased tag
        # on the development branch being released for the first time.
        if dest_track['version'] in [':{ask}', ':{auto}']:
            # Override the version for this release to guarantee the same version is released.
            dest_track['version_saved'] = dest_track['version']
            dest_track['version'] = dest_track['last_version']
            write_tracks_file(tracks, "Update {} track to release exactly last-released version.".format(args.dest))

        if dest_track['release_tag'] == ':{ask}' and 'last_release' in dest_track:
            # Override the version for this release to guarantee the same version is released.
            dest_track['release_tag_saved'] = dest_track['release_tag']
            dest_track['release_tag'] = dest_track['last_release']
            write_tracks_file(tracks, "Update {} track to release exactly last-released tag.".format(args.dest))

        # Bloom will not run with multiple remotes.
        subprocess.check_call(['git', 'remote', 'remove', 'oldorigin'])
        subprocess.check_call(['git', 'bloom-release', '--non-interactive', '--unsafe', args.dest], env=os.environ)
        subprocess.check_call(['git', 'push', 'origin', '--all', '--force'])
        subprocess.check_call(['git', 'push', 'origin', '--tags', '--force'])
        subprocess.check_call(['git', 'checkout', 'master'])

        # Re-read tracks.yaml after release.
        tracks = read_tracks_file()
        dest_track = tracks['tracks'][args.dest]
        if 'version_saved' in dest_track:
            dest_track['version'] = dest_track['version_saved']
            del dest_track['version_saved']
            write_tracks_file(tracks, "Restore saved version for {} track.".format(args.dest))
        if 'release_tag_saved' in dest_track:
            dest_track['release_tag'] = dest_track['release_tag_saved']
            del dest_track['release_tag_saved']
            write_tracks_file(tracks, "Restore saved version and tag for {} track.".format(args.dest))
        new_release_track_inc = str(int(tracks['tracks'][args.dest]['release_inc']))
        release_spec.url = new_release_repo_url

        ver, _inc = release_spec.version.split('-')
        release_spec.version = '-'.join([ver, new_release_track_inc])
        repositories_bloomed.append(repo_name)
    except (subprocess.CalledProcessError, ValueError) as e:
        repositories_with_errors.append((repo_name, e))
    os.chdir(workdir)

os.chdir(rosdistro_dir)

for dest_repo in sorted(new_repositories + repositories_to_retry):
    if dest_repo not in repositories_bloomed:
        print('{} was not bloomed! Removing the release version,'.format(dest_repo))
        dest_distribution.repositories[dest_repo].release_repository.version = None

with open(destpath, 'w') as f:
    f.write(yaml_from_distribution_file(dest_distribution))

print('Had {} repositories with errors:'.format(len(repositories_with_errors)), repositories_with_errors)
