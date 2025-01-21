# -*- coding:utf-8 -*-

import requests

from smartci.vcs.git.git_repo import GitRepo
from smartci.vcs.git.git_util import GitUtil


class Git:
    def __init__(self, address, username, access_token) -> None:
        super().__init__()
        self.util = GitUtil(address, username, access_token)
        self.type = "git"
        self.address = address

    def GetAddress(self):
        return self.address

    def GetRepos(self):
        projects = self.util.ListProjects()
        repos = []
        for project in projects:
            repo = GitRepo(self, project)
            repos.append(repo)
        return repos

    def GetRepoByUrl(self, web_url):
        if not web_url.startswith(self.address):
            raise Exception(f"Invalid repo url: {web_url}")
        project = self.util.GetProjectByUrl(web_url)
        if project is None:
            return None
        return GitRepo(self, project)

    def GetVersionEntityFromLocalPath(self, local_path):
        re = self.util.GetUrlAndBranchOfLocalPath(local_path)
        if re is None:
            return None
        if re['url'].startswith(self.address):
            web_url = re['url']

            project = self.util.GetProjectByUrl(web_url)
            if project is None:
                return None
            return GitRepo(self, project).GetBranch(re['branch'])
