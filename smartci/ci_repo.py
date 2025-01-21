import os

import yaml

from smartci.ci_branch import CiBranch, CiTag


class CiRepo:
    """
    This class represents a Continuous Integration (CI) repository.
    """

    def __init__(self, ci_vcs, primitive_repo):
        """
        Initializes a new instance of the CiRepo class.

        :param ci_vcs: The CI version control system this repository belongs to.
        :param primitive_repo: The primitive repository this CI repository is based on.
        """
        self.ci_vcs = ci_vcs
        self.primitive_repo = primitive_repo
        self.__Init()

    def __str__(self):
        return f"{self.GetGroup()}.{self.GetName()}"

    def Id(self):
        return f"{self}"

    @staticmethod
    def GetGroupFromId(repo_id):
        return repo_id.split(".")[0]

    @staticmethod
    def GetNameFromId(repo_id):
        return repo_id.split(".")[1]

    def __Init(self):
        """
        Initializes the CiRepo instance.

        This method retrieves the trunk branch from the primitive repository, reads the CI settings from the ".ci/settings.yml" file in the trunk branch, and sets the group and name of the CI repository based on these settings.
        """
        branch = self.primitive_repo.GetTrunk()
        setting_str = branch.GetFileContent(".ci/settings.yml")
        setting = yaml.safe_load(setting_str)
        relative_path = self.GetUrl()[len(self.primitive_repo.vcs.GetAddress())+1:]
        if setting is not None and 'group' in setting and setting['group'] != "":
            self.group = setting['group']
        else:
            self.group = relative_path[:relative_path.rfind('/')]
        if setting is not None and 'name' in setting and setting['name'] != "":
            self.name = setting['name']
        else:
            self.name = relative_path[relative_path.rfind('/') + 1:]
        self.group = self.group.replace('/', '_')
        self.name = self.name.replace('/', '_')

    @staticmethod
    def SupportCi(primitive_repo):
        """
        Checks if the primitive repository supports CI.

        :param primitive_repo: The primitive repository to check.
        :return: True if the primitive repository supports CI, False otherwise.
        """
        branch = primitive_repo.GetTrunk()
        if branch.FileExists(".ci/settings.yml"):
            return True
        return False

    def GetName(self):
        """
        Returns the name of the CI repository.

        :return: The name of the CI repository.
        """
        return self.name

    def GetGroup(self):
        """
        Returns the group of the CI repository.

        :return: The group of the CI repository.
        """
        return self.group

    def GetUrl(self):
        """
        Returns the URL of the primitive repository.

        :return: The URL of the primitive repository.
        """
        return self.primitive_repo.GetUrl()

    def GetPrimitiveVcs(self):
        """
        Returns the version control system of the primitive repository.

        :return: The version control system of the primitive repository.
        """
        return self.primitive_repo.vcs

    def GetTrunk(self):
        """
        Returns the trunk branch of the CI repository.

        :return: The trunk branch of the CI repository.
        """
        primitive_trunk = self.primitive_repo.GetTrunk()
        ci_trunk = CiBranch(self, primitive_trunk)
        return ci_trunk

    def GetBranch(self, branch_name):
        """
        Returns the CI branch with the given branch name.

        :param branch_name: The name of the branch to get.
        :return: The CI branch with the given branch name, or None if no such branch exists.
        """
        primitive_branch = self.primitive_repo.GetBranch(branch_name)
        if primitive_branch is not None:
            ci_branch = CiBranch(self, primitive_branch)
            return ci_branch
        return None

    def GetBranches(self, branch_name_pattern):
        """
        Returns the CI branches with the given branch name pattern.

        :param branch_name_pattern: The pattern of the branch name to get.
        :return: The CI branches with the given branch name pattern.
        """
        primitive_branches = self.primitive_repo.GetBranches(branch_name_pattern)
        ci_branches = []
        for primitive_branch in primitive_branches:
            ci_branch = CiBranch(self, primitive_branch)
            ci_branches.append(ci_branch)
        return ci_branches

    def GetAllBranches(self):
        """
        Returns all branches in the CI repository.

        :return: All branches in the CI repository.
        """
        return self.GetBranches(".*")

    def DeleteBranch(self, branch_name, comment=None):
        """
        Deletes the branch with the given branch name from the CI repository.

        :param branch_name: The name of the branch to delete.
        :param comment: The comment of the deletion.
        """
        if comment is None:
            comment = "delete branch " + branch_name + " by smartci"
        self.primitive_repo.DeleteBranch(branch_name, comment)

    def GetTag(self, tag_name):
        """
        Returns the CI tag with the given name.

        :param tag_name: The name of the tag to get.
        :return: The CI tag with the given name, or None if no such tag exists.
        """
        primitive_tag = self.primitive_repo.GetTag(tag_name)
        if primitive_tag is not None:
            ci_tag = CiTag(self, primitive_tag)
            return ci_tag
        return None

    def DeleteTag(self, tag_name, comment=None):
        """
        Deletes the tag with the given tag name from the CI repository.

        :param tag_name: The name of the tag to delete.
        :param comment: The comment of the deletion.
        """
        if comment is None:
            comment = "delete tag " + tag_name + "by smartci"
        self.primitive_repo.DeleteTag(tag_name, comment)

    def AddBranch(self, branch_name, comment=None):
        """
        Adds a new branch with the given branch name to the CI repository.

        :param branch_name: The name of the branch to add.
        :return: The new CI branch.
        """
        if comment is None:
            comment = "create branch " + branch_name
        branch = self.primitive_repo.CreateBranch(branch_name, comment)
        ci_branch = CiBranch(self, branch)
        return ci_branch

    def RevertWorkspace(self, workspace):
        """
        Reverts the workspace to the last commit.

        :param workspace: The workspace to revert.
        """
        self.primitive_repo.RevertWorkspace(workspace)

    def SwitchWorkspace(self, workspace, ci_entity):
        """
        Switches the workspace to the branch with the given branch name.

        :param workspace: The workspace to switch.
        :param ci_entity: The CI entity to switch to.
        """
        self.primitive_repo.SwitchWorkspace(workspace, ci_entity.GetPrimitiveEntity())
