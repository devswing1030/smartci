# -*- coding:utf-8 -*-
from smartci.vcs.git.git_version_entity import GitVersionEntity


class GitRepo:
    def __init__(self, vcs, project) -> None:
        self.vcs = vcs  # Git
        self.project = project # 通过api接口获得的项目信息，json格式

    def GetUrl(self):
        return self.project['web_url']

    def GetBranch(self, branch_name):
        if self.vcs.util.BranchExists(self.project['id'], branch_name):
            return GitVersionEntity(self.vcs, self, branch_name)
        return None

    def GetBranches(self, branch_name_pattern):
        branches = []

        for branch in self.vcs.util.ListBranches(self.project['id'], branch_name_pattern):
            if branch['name'] == self.project['default_branch']:
                continue
            branches.append(GitVersionEntity(self.vcs, self, branch['name']))
        return branches

    def GetAllBranches(self):
        return self.GetBranches(".*")

    def DeleteBranch(self, branch_name, comment):
        self.vcs.util.DeleteBranch(self.project['id'], branch_name)

    def GetTrunk(self):
        git_branch = GitVersionEntity(self.vcs, self, self.project['default_branch'])
        return git_branch

    def GetTag(self, tag_name):
        if self.vcs.util.TagExists(self.project['id'], tag_name):
            return GitVersionEntity(self.vcs, self, tag_name)
        return None

    def DeleteTag(self, tag_name, comment):
        self.vcs.util.DeleteTag(self.project['id'], tag_name)

    def CreateBranch(self, branch_name, comment):
        print(f"Create branch {branch_name} for {self.project['name']}")
        self.vcs.util.AddBranch(self.project['id'], branch_name, self.project['default_branch'])
        return self.GetBranch(branch_name)

    def GetProjectID(self):
        return self.project['id']

    def GetProjectName(self):
        return self.project['name']

    def GetHttpCloneUrl(self):
        url = self.project['http_url_to_repo']
        return url

    def GetVersionEntityType(self, entity_name):
        if entity_name == self.project['default_branch']:
            return "trunk"
        if self.vcs.util.BranchExists(self.project['id'], entity_name):
            return "branch"
        if self.vcs.util.TagExists(self.project['id'], entity_name):
            return "tag"

    def RevertWorkspace(self, workspace):
        self.vcs.util.RevertWorkspace(workspace)

    def SwitchWorkspace(self, workspace, primitive_entity):
        self.vcs.util.SwitchWorkspace(workspace, primitive_entity.GetPrimitiveName(), primitive_entity.GetType())

