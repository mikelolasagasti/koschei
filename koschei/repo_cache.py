# Copyright (C) 2014-2015 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Author: Mikolaj Izdebski <mizdebsk@redhat.com>
# Author: Michael Simacek <msimacek@redhat.com>

import os
import librepo
import shutil
import logging

from koschei.cache_manager import CacheManager

from koschei import util

log = logging.getLogger('koschei.repo_cache')

REPO_404 = 19


class RepoManager(object):
    def __init__(self, build_tag, arches, remote_repo, repo_dir):
        self._build_tag = build_tag
        self._arches = arches
        self._remote_repo = remote_repo
        self._repo_dir = repo_dir

    def _get_repo_dir(self, repo_id):
        return os.path.join(self._repo_dir, str(repo_id))

    def _clean_repo_dir(self, repo_id):
        repo_dir = self._get_repo_dir(repo_id)
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)

    # Download given repo_id from Koji to disk
    def create(self, repo_id, ignored):
        self._clean_repo_dir(repo_id)
        repo_dir = self._get_repo_dir(repo_id)
        try:
            for arch in self._arches:
                h = librepo.Handle()
                arch_repo_dir = os.path.join(repo_dir, arch)
                os.makedirs(arch_repo_dir)
                h.destdir = arch_repo_dir
                h.repotype = librepo.LR_YUMREPO
                url = self._remote_repo.format(repo_id=repo_id, arch=arch,
                                               build_tag=self._build_tag)
                h.urls = [url]
                h.yumdlist = ['primary', 'filelists', 'group']
                h.perform(librepo.Result())
            return repo_dir
        except librepo.LibrepoException as e:
            if e.args[0] == REPO_404:
                return None
            raise

    # Remove repo from disk
    def destroy(self, repo_id, repo):
        self._clean_repo_dir(repo_id)

    # Read list of repo_id's cached on disk
    def populate_cache(self):
        repos = []
        for repo in os.listdir(self._repo_dir):
            if repo.isdigit():
                repo_id = int(repo)
                repo_path = self._get_repo_dir(repo_dir)
                repos.append((repo_id, repo_path))
        return repos


class SackManager(object):
    def __init__(self, arches, for_arch):
        self._arches = arches
        self._for_arch = for_arch

    # Load repo from disk into memory as sack
    def create(self, repo_id, repo_dir):
        try:
            sack = hawkey.Sack(arch=self._for_arch)
            for arch in self._arches:
                arch_repo_dir = os.path.join(repo_dir, arch)
                h = librepo.Handle()
                h.local = True
                h.repotype = librepo.LR_YUMREPO
                h.urls = [arch_repo_dir]
                h.yumdlist = ['primary', 'filelists', 'group']
                repodata = h.perform(librepo.Result()).yum_repo
                repo = hawkey.Repo('{}-{}'.format(repo_id, arch))
                repo.repomd_fn = repodata['repomd']
                repo.primary_fn = repodata['primary']
                repo.filelists_fn = repodata['filelists']
                sack.load_yum_repo(repo, load_filelists=True)
            return sack
        except (librepo.LibrepoException, IOError):
            return None

    # Release sack
    def destroy(self, repo_id, sack):
        # Nothing to do - sack will be garbage-collected automatically.
        pass

    # Initially there are no sacks cached
    def populate_cache(self):
        return None


class RepoCache(object):
    def __init__(self, koji_session,
                 repo_dir=util.config['directories']['repodata'],
                 max_repos=util.config['dependency']['repo_cache_items'],
                 remote_repo=util.config['dependency']['remote_repo'],
                 arches=util.config['dependency']['arches'],
                 for_arch=util.config['dependency']['for_arch'],
                 cache_l1_capacity=util.config['dependency']['cache_l1_capacity'],
                 cache_l2_capacity=util.config['dependency']['cache_l2_capacity'],
                 cache_l1_threads=util.config['dependency']['cache_l1_threads'],
                 cache_l2_threads=util.config['dependency']['cache_l2_threads'],
                 cache_threads_max=util.config['dependency']['cache_threads_max']):

        build_tag = None
        if '{build_tag}' in remote_repo:
            build_tag = koji_session.repoInfo(repo_id)['tag_name']

        sack_manager = SackManager(arches, for_arch)
        repo_manager = RepoManager(build_tag, arches, remote_repo, repo_dir)

        self.mgr = CacheManager(cache_threads_max)
        self.mgr.add_bank(sack_manager, cache_l1_capacity, cache_l1_threads)
        self.mgr.add_bank(repo_manager, cache_l2_capacity, cache_l2_threads)

    def prefetch_repo(self, repo_id):
        self.mgr.prefetch(repo_id)

    def get_sack(self, repo_id):
        sack = self.mgr.acquire(repo_id)
        return sack

    def release_sack(self, repo_id):
        return self.mgr.release(repo_id)

    def cleanup(self):
        return self.mgr.terminate()
