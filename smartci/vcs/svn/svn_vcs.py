# -*- coding:utf-8 -*-

from smartci.vcs.svn import svn_repo
from smartci.vcs.svn.svn_util import SvnUtil
from smartci.vcs.svn.svn_version_entity import SvnVersionEntity


class Svn:
    def __init__(self, address, username, password, root_repos) -> None:
        super().__init__()
        self.util = SvnUtil(address, username, password)
        self.root_repos = root_repos  # svn仓库的根目录列表
        self.type = "svn"
        self.address = address

    def GetAddress(self):
        return self.address

    def GetRepos(self):
        repos_path = []
        for root_repo in self.root_repos:
            self.__RecursiveGetRepos(root_repo, repos_path)
        #print(repos_path)
        repos = []
        for path in repos_path:
            repo = svn_repo.SvnRepo(self, path)
            repos.append(repo)
        return repos

    def GetRepoByRelPath(self, rel_path):
        repo_rel_path = svn_repo.SvnRepo.GetRepoRelPathFromUrl(rel_path)
        if self.util.PathExists(repo_rel_path):
            return svn_repo.SvnRepo(self, repo_rel_path)
        return None

    def GetRepoByUrl(self, repo_url):
        if not repo_url.startswith(self.address):
            return None
        rel_path = repo_url[len(self.address)+1:]
        if self.util.PathExists(rel_path):
            return svn_repo.SvnRepo(self, rel_path)

    def GetVersionEntityFromLocalPath(self, local_path):
        url = self.util.GetUrlFromLocalPath(local_path)
        if url is None:
            return None
        if not url.startswith(self.address):
            return None
        rel_path = url[len(self.address)+1:]
        primitive_repo = self.GetRepoByRelPath(rel_path)
        if not self.util.PathExists(rel_path):
            raise Exception("invalid svn url " + url)
        primitive_version_entity = SvnVersionEntity(self, primitive_repo, rel_path)
        return primitive_version_entity

    def __RecursiveGetRepos(self, rel_path, repos):
        # 遍历所有文件夹，如含trunk文件夹，则认为是一个repo
        for entry in self.util.ListEntryOfDir(rel_path):
            if not entry['is_directory']:
                continue
            if entry['name'] == "trunk":
                repos.append(rel_path)
                return

        for entry in self.util.ListEntryOfDir(rel_path):
            if not entry['is_directory']:
                continue
            self.__RecursiveGetRepos(rel_path + "/" + entry['name'], repos)
