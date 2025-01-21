# -*- coding:utf-8 -*-

from smartci.vcs.svn.svn_version_entity import SvnVersionEntity
import re


class SvnRepo:
    def __init__(self, vcs, rel_path) -> None:
        self.vcs = vcs
        self.rel_path = rel_path

    def GetUrl(self):
        return self.vcs.util.GetAbsolutePath(self.rel_path)

    def CreateBranch(self, branch_name, comment):
        print(f"Create branch {branch_name} for {self.rel_path}")
        trunk_path = self.rel_path + "/trunk"
        branch_path = self.rel_path + "/branches/" + branch_name
        if self.vcs.util.PathExists(branch_path):
            raise Exception("branch " + branch_name + " already exists")
        self.vcs.util.Copy(trunk_path, branch_path, comment)
        return self.GetBranch(branch_name)

    def GetBranch(self, branch_name):
        path = self.rel_path + "/branches/" + branch_name
        if self.vcs.util.PathExists(path):
            branch = SvnVersionEntity(self.vcs, self, path)
            return branch
        return None

    def GetBranches(self, branch_name_pattern):
        branches = []
        for entry in self.vcs.util.ListEntryOfDir(self.rel_path + "/branches"):
            if not entry['is_directory']:
                continue
            if not re.match(branch_name_pattern, entry['name']):
                continue
            branch = SvnVersionEntity(self.vcs, self, self.rel_path + "/branches/" + entry['name'])
            branches.append(branch)
        return branches

    def GetAllBranches(self):
        return self.GetBranches(".*")

    def DeleteBranch(self, branch_name, comment):
        path = self.rel_path + "/branches/" + branch_name
        if self.vcs.util.PathExists(path):
            self.vcs.util.Remove(path, comment)

    def GetBranchPath(self):
        return self.rel_path + "/branches"

    def GetTagPath(self):
        return self.rel_path + "/tags"

    def GetTrunk(self):
        return SvnVersionEntity(self.vcs, self, self.rel_path + "/trunk")

    def GetTag(self, tag_name):
        path = self.rel_path + "/tags/" + tag_name
        if self.vcs.util.PathExists(path):
            tag = SvnVersionEntity(self.vcs, self, path)
            return tag
        return None

    def DeleteTag(self, tag_name, comment):
        path = self.rel_path + "/tags/" + tag_name
        if self.vcs.util.PathExists(path):
            self.vcs.util.Remove(path, comment)

    def RevertWorkspace(self, workspace):
        self.vcs.util.Revert(workspace)

    def SwitchWorkspace(self, workspace, primitive_entity):
        self.vcs.util.SwitchWorkspace(workspace, primitive_entity.GetRelPath())

    @staticmethod
    def GetRepoRelPathFromUrl(url):
        if url.find("/trunk") > 0:
            return url[0:url.find("trunk") - 1]
        if url.find("/branches") > 0:
            return url[0:url.find("branches") - 1]
        if url.find("/tags") > 0:
            return url[0:url.find("tags") - 1]
        raise Exception("invalid svn url " + url)

