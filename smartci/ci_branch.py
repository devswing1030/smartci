import hashlib
import os
import shutil
import subprocess
from datetime import datetime


class CiVersionEntity:
    def __init__(self, ci_repo, primitive_entity):
        """
        Initializes a new instance of the CiBranch class.

        :param ci_repo: The CI repository this branch belongs to.
        :param type: The type of the branch, "branch" or "tag" or "trunk".
        :param primitive_entity: The primitive branch this CI branch is based on.
        """
        self.primitive_entity = primitive_entity
        self.ci_repo = ci_repo

    def __str__(self):
        pass

    def GetName(self):
        return self.primitive_entity.GetName()

    def GetType(self):
        """
        Returns the type of the branch.

        :return: The type of the branch. "branch" or "tag" or "trunk".
        """
        return self.primitive_entity.GetType()

    def GetPrimitiveName(self):
        """
        Returns the name of the primitive branch.

        :return: The name of the primitive branch.
        """
        return self.primitive_entity.GetPrimitiveName()

    def GetUrl(self):
        """
        Returns the URL of the primitive branch.

        :return: The URL of the primitive branch.
        """
        return self.primitive_entity.GetUrl()

    def GetPrimitiveEntity(self):
        """
        Returns the primitive branch.

        :return: The primitive branch.
        """
        return self.primitive_entity

    def GetLastCommitId(self):
        """
        Returns the last commit id of the primitive branch.

        :return: The last commit id of the primitive branch.
        """
        return self.primitive_entity.GetLastCommitId()

    def GetLastCommitInfo(self):
        """
        Returns the last commit info of the primitive branch.

        :return: The last commit info of the primitive branch. The info is a dictionary with the following keys:
            - 'commit_id': The commit id of the last commit.
            - 'author': The author of the last commit.
            - 'date': The date of the last commit.
            - 'message': The message of the last commit.
        """
        return self.primitive_entity.GetLastCommitInfo()

    def GetCommitIdOfLocalPath(self, local_path):
        """
        Returns the commit id of the local path.

        :return: The commit id of the local path.
        """
        return self.primitive_entity.GetCommitIdOfLocalPath(local_path)

    def GetCommitInfoOfLocalPath(self, local_path):
        """
        Returns the commit info of the local path.

        :return: The commit info of the local path. The info is a dictionary with the following keys:
            - 'commit_id': The commit id of the commit.
            - 'author': The author of the commit.
            - 'date': The date of the commit.
            - 'message': The message of the last commit.
        """
        return self.primitive_entity.GetCommitInfoOfLocalPath(local_path)

    def CheckOut(self, local_path):
        """
        Checks out the primitive branch to the local path.
        :param local_path: The local path to check out the primitive branch to.
        """
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        self.primitive_entity.CheckOut(local_path)
        print("checkout " + str(self) + " to " + local_path + " done")

    def CheckOutDirectory(self, local_path, rel_path):
        """
        Checks out a directory from the primitive branch to the local path.
        :param local_path: The local path to check out the primitive branch to.
        :param rel_path: The relative path of the directory to check out.
        """
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        self.primitive_entity.CheckOutDirectory(local_path, rel_path)

    def GetFile(self, file_rel_path, local_path):
        """
        Gets a file from the primitive branch and saves it to the local path.
        :param file_rel_path:
        :param local_path:
        :return:
        """
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        content = self.primitive_entity.GetFileContent(file_rel_path)
        filename = file_rel_path[file_rel_path.rfind("/") + 1:]
        local_path = os.path.join(local_path, filename)

        with open(local_path, "w") as f:
            f.write(content)
        f.close()

    def GetFileContent(self, file_rel_path):
        content = self.primitive_entity.GetFileContent(file_rel_path)
        return content

    def PathExists(self, file_path):
        """
        Checks if the given path exists in the primitive branch.

        :param file_path: The path to check.
        :return: True if the path exists, False otherwise.
        """
        return self.primitive_entity.PathExists(file_path)

    def FileExists(self, file_path):
        """
        Checks if the given file exists in the primitive branch.

        :param file_path: The file to check.
        :return: True if the file exists, False otherwise.
        """
        return self.primitive_entity.FileExists(file_path)

    def AddToControl(self, checkout_path, target_rel_path):
        """
        Adds the file or directory represented by the target_rel_path to the control of the primitive branch.

        :param checkout_path: The path of the branch checked out.
        :param target_rel_path: The relative path of the file or directory to add.
        """
        self.primitive_entity.AddToControl(checkout_path, target_rel_path)

    def Commit(self, checkout_path, comment):
        """
        Commits the changes in the checkout_path with the given comment.

        :param comment: The comment for the commit.
        :param checkout_path: The path of the branch checked out.
        """
        self.primitive_entity.Commit(checkout_path, comment)
        print("commit " + str(self) + " done")

    def AddFile(self, file_rel_path, content, comment):
        """
        Adds a file to the primitive branch.

        :param file_rel_path: The relative path of the file to add.
        :param content: The content of the file to add.
        :param comment: The comment for the add.
        """
        tmp_path = self._PrepareTmpWorkDirectory()
        self.primitive_entity.AddFile(tmp_path, file_rel_path, content, comment)
        self._RemoveTmpWorkDirectory(tmp_path)

    def RemoveFile(self, file_rel_path, comment):
        """
        Removes a file from the primitive branch.

        :param file_rel_path: The relative path of the file to remove.
        :param comment: The comment for the remove.
        """
        self.primitive_entity.RemoveFile(file_rel_path, comment)

    def Copy(self, branch_name, comment=None):
        """
        Copies the primitive branch to a new branch with the given name and comment.

        :param branch_name: The name of the new branch.
        :param comment: The comment for the copy.
        :return: The new branch.
        """
        self.primitive_entity.Copy(branch_name, comment)
        return self.ci_repo.GetBranch(branch_name)

    def CopyWithCommitId(self, branch_name, commit_id, comment=None):
        """
        Copies the primitive branch to a new branch with the given name and comment.

        :param branch_name: The name of the new branch.
        :param commit_id: The commit id to copy.
        :param comment: The comment for the copy.
        :return: The new branch.
        """
        self.primitive_entity.CopyWithCommitId(branch_name, commit_id, comment)
        return self.ci_repo.GetBranch(branch_name)

    def CreateTag(self, tag_name, revision, comment=None):
        """
        Creates a tag with the given name and revision.

        :param tag_name: The name of the tag.
        :param revision: The revision for the tag. If None, the latest revision of the current branch is used.
        :param comment: comment, only be valid for svn
        """
        self.primitive_entity.CreateTag(tag_name, revision, comment)

    def AddRef(self, ref_ci_version_entity, mount_rel_path, path_to_save_ref_for_svn=None):
        """
        Adds a reference to the given CI branch to the primitive branch.

        :param ref_ci_version_entity: The CI branch to add a reference to.
        :param mount_rel_path: The path to add the reference to.
        :param path_to_save_ref_for_svn: The path for save the ref info in SVN. If None, the ref info will be
            saved in the root path.
        """
        tmp_path = self._PrepareTmpWorkDirectory()
        self.primitive_entity.AddRef(tmp_path, ref_ci_version_entity.primitive_entity, mount_rel_path,
                                     path_to_save_ref_for_svn)
        self._RemoveTmpWorkDirectory(tmp_path)

    def RemoveRefByMountRelPath(self, mount_rel_path):
        """
        Removes the reference by the given mount_rel_path.

        :param mount_rel_path: The path to remove the reference.
        """
        tmp_path = self._PrepareTmpWorkDirectory()
        self.primitive_entity.RemoveRefByMountRelPath(tmp_path, mount_rel_path)
        self._RemoveTmpWorkDirectory(tmp_path)

    def _GetWorkDirectory(self):
        """
        Returns the work directory of the CI branch.

        :return: The work directory of the CI branch.
        """
        ci_workspace = os.environ.get('CI_WORKSPACE')
        if ci_workspace is None:
            exception = "env CI_WORKSPACE not set"
            raise Exception(exception)
        md5 = hashlib.md5(str(self).encode('utf-8')).hexdigest()
        now = datetime.now()
        unique_name = now.strftime("%Y%m%d%H%M%S%f")

        path = os.path.join(ci_workspace, "tmp", f"{unique_name}{md5}")
        return path

    def _PrepareTmpWorkDirectory(self):
        """
        Prepares a temporary work directory for the CI branch.
        """

        tmp_path = self._GetWorkDirectory()
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)
        os.makedirs(tmp_path)
        return tmp_path

    @staticmethod
    def _RemoveTmpWorkDirectory(tmp_path):
        """
        Removes the temporary work directory for the CI branch.

        :param tmp_path: The temporary work directory to remove.
        """
        shutil.rmtree(tmp_path)

    def GetRefCiRepos(self):
        """
        Returns a list of CI repositories that are referenced by the primitive branch.

        :return: A list of CI repositories that are referenced by the primitive branch.
        """
        result = []
        primitive_external_repos = self.primitive_entity.GetRefRepos()
        for primitive_external_repo in primitive_external_repos:
            ci_repo = self.ci_repo.ci_vcs.CreateCiRepo(primitive_external_repo)
            result.append(ci_repo)
        return result

    def GetRefCiVersionEntities(self, local_path=None):
        """
        Returns a list of CI branches that are referenced by the primitive branch.

        :param local_path: The local path of the primitive branch. If not None, the reference will be checked in the local path.

        :return: A list of CI branches that are referenced by the primitive branch.
                Item in list is {"mount_rel_path": str, "version_entity": CiVersionEntity}
        """
        result = []
        refs = self.primitive_entity.GetRefVersionEntities(local_path)
        for ref in refs:
            mount_rel_path = ref["mount_rel_path"]
            primitive_entity = ref["version_entity"]
            ci_repo = self.ci_repo.ci_vcs.CreateCiRepo(primitive_entity.repo)
            version_entity = CiVersionEntity.Create(ci_repo, primitive_entity)
            result.append({"mount_rel_path": mount_rel_path, "version_entity": version_entity})

        return result

    def UpdateRefEntity(self, ref_ci_branch):
        """
        Refreshes the reference to the given CI branch in the primitive branch.

        :param ref_ci_branch: The CI branch to refresh the reference to.
        """
        tmp_path = self._PrepareTmpWorkDirectory()
        self.primitive_entity.UpdateRefEntity(tmp_path, ref_ci_branch.primitive_entity)
        self._RemoveTmpWorkDirectory(tmp_path)

    def ExistRepoRef(self, ref_ci_repo):
        """
        Checks if the primitive branch has a reference to the given CI repository.

        :param ref_ci_repo: The CI repository to check for a reference to.
        :return: True if the primitive branch has a reference to the CI repository, False otherwise.
        """
        refs = self.GetRefCiRepos()
        for ref in refs:
            if ref.GetUrl() == ref_ci_repo.GetUrl():
                return True
        return False


    def ExistEntityRef(self, ci_version_entity, mount_rel_path=None):
        """
        Checks if the primitive branch has a reference to the given CI branch.

        :param ci_version_entity: The CI branch to check for a reference to.
        :param mount_rel_path: The mount path of the reference.

        :return: True if the primitive branch has a reference to the CI branch, False otherwise.
        """
        refs = self.GetRefCiVersionEntities()
        for ref in refs:
            entity = ref["version_entity"]
            tmp_mount_rel_path = ref["mount_rel_path"]
            if entity.GetUrl() == ci_version_entity.GetUrl():
                if mount_rel_path is None or mount_rel_path == tmp_mount_rel_path:
                    return True
        return False

    def EnablePush(self):
        """
        Enables the primitive branch to be pushed by developer.
        """
        self._SetProtected(True, True)

    def DisablePush(self):
        """
        Disables the primitive branch to be pushed by developer.
        """
        self._SetProtected(False, False)

    def IsAllowedPush(self):
        """
        Returns True if the primitive branch is allowed to be pushed by developer, False otherwise.
        """
        re = self.primitive_entity.GetProtectedInfo()
        if re["allowed_push"]:
            return True
        return False

    def _SetProtected(self, allowed_merge, allowed_push):
        """
        Sets the primitive branch as protected. Only for git.

        :param allowed_merge: The allowed merge type. "merge" or "rebase" or "merge,rebase".
        :param allowed_push: The allowed push type. "push" or "push,delete".
        """
        self.primitive_entity.SetProtected(allowed_merge, allowed_push)


    def IsSupportMergeRequest(self):
        """
        Returns True if the primitive branch supports merge request, False otherwise.
        """
        return self.primitive_entity.IsSupportMergeRequest()

    def GetMergeRequestStatus(self, target_entity, min_reviewers=1):
        """
        Returns the merge request status of the primitive branch to the target branch.

        :param target_entity: The target branch to check the merge request status.
        :param min_reviewers: The minimum number of reviewers required for the merge request.
        :return: The merge request status of the primitive branch to the target branch.
                {"merged": bool, "can_be_merged": bool, "message": str}
        """
        tmp_path = self._PrepareTmpWorkDirectory()  # svn need a work directory
        status = self.primitive_entity.GetMergeRequestStatus(target_entity.primitive_entity, tmp_path, min_reviewers)
        self._RemoveTmpWorkDirectory(tmp_path)
        return status

    def CreateMergeRequest(self, target_entity, title, reviewers, description=None):
        """
        Creates a merge request from the primitive branch to the target branch.
        :param target_entity:
        :param title:
        :param reviewers:
        :param description:
        """
        self.primitive_entity.CreateMergeRequest(target_entity.primitive_entity, title, reviewers, description)

    def GetMergeRequestWebUrl(self, target_entity):
        """
        Returns the web URL of the merge request to the target branch.
        :param target_entity:
        :return: The web URL of the merge request.
        """
        return self.primitive_entity.GetMergeRequestWebUrl(target_entity.primitive_entity)

    def GetMergeRequestApprovalStatus(self, target_entity):
        """
        Returns the approval status of the merge request to the target branch.
        :param target_entity:
        :return: The approval status of the merge request. {"approved": bool, "approvals": [str], "reviewers": [str]}
        """
        return self.primitive_entity.GetMergeRequestApprovalStatus(target_entity.primitive_entity)

    def CheckMergeRequestApproved(self, target_entity):
        """
        Checks if the merge request to the target branch is approved.
        :param target_entity:
        :return: true if the merge request is approved, false otherwise.
        """
        return self.primitive_entity.CheckMergeRequestApproved(target_entity.primitive_entity)

    def AcceptMergeRequest(self, target_entity, comment, remove_branch_after_merge=False):
        """
        Executes the merge request to the target branch.
        :param target_entity:
        """
        if comment is None or comment == "":
            comment = "merge by smartci"
        tmp_path = self._PrepareTmpWorkDirectory()  # svn need a work directory
        self.primitive_entity.AcceptMergeRequest(target_entity.primitive_entity, comment, remove_branch_after_merge, tmp_path)
        self._RemoveTmpWorkDirectory(tmp_path)

    def MergeTo(self, target_entity, comment):
        """
        Merges the current branch to the target branch.
        :param target_entity:
        """
        if comment is None or comment == "":
            comment = "merge by smartci"
        tmp_path = self._PrepareTmpWorkDirectory()  # svn need a work directory
        self.primitive_entity.MergeTo(target_entity.primitive_entity, comment, tmp_path)
        self._RemoveTmpWorkDirectory(tmp_path)

    @staticmethod
    def Create(ci_repo, primitive_entity):
        """
        Creates a new CiVersionEntity object.

        :param ci_repo: The CI repository this branch belongs to.
        :param primitive_entity: The primitive branch this CI branch is based on.
        :return: The new CiVersionEntity object.
        """
        if primitive_entity.GetType() == "branch":
            return CiBranch(ci_repo, primitive_entity)
        elif primitive_entity.GetType() == "tag":
            return CiTag(ci_repo, primitive_entity)
        elif primitive_entity.GetType() == "trunk":
            return CiTrunk(ci_repo, primitive_entity)
        else:
            raise Exception("unknown type: " + primitive_entity.GetType())

    def GetDiffFiles(self, from_entity):
        """
        Returns the differences between the from entity and the current entity.

        :param from_entity: The entity to compare with.
        :return: A list of dictionaries, each dictionary contains the following keys:
           - 'path': The path of the file.
           - 'type': The type of the change. It can be 'A' for added, 'D' for deleted, 'M' for modified.
        """
        return self.primitive_entity.GetDiffFiles(from_entity.primitive_entity)

    def Rollback(self, commit_id, comment):
        """
        Rollback the current branch to the given commit id.

        :param commit_id: The commit id to rollback to.
        :param comment: The comment for the rollback.
        """
        tmp_path = self._PrepareTmpWorkDirectory()  # svn need a work directory
        self.primitive_entity.Rollback(commit_id, comment, tmp_path)
        self._RemoveTmpWorkDirectory(tmp_path)

    def ContainsEntity(self, entity):
        """
        Checks if the current entity has merged the given entity.

        :param entity: The entity to check.
        :return: True if the current entity has merged the given entity, False otherwise.
        """
        return self.primitive_entity.ContainsEntity(entity.primitive_entity)

    def AddWebHook(self, webhook_url, secret_token):
        """
        Adds a webhook to the current entity.

        :param webhook_url: The webhook URL to add.
        """
        return self.primitive_entity.AddWebHook(webhook_url, secret_token)

    def DeleteWebHook(self, webhook_url):
        """
        Deletes a webhook from the current entity.

        :param webhook_url: The webhook URL to delete.
        """
        self.primitive_entity.DeleteWebHook(webhook_url)


class CiTrunk(CiVersionEntity):
    """
    This class represents a Continuous Integration (CI) trunk in a CI repository.
    """

    def __init__(self, ci_repo, primitive_trunk):
        """
        Initializes a new instance of the CiTrunk class.

        :param ci_repo: The CI repository this trunk belongs to.
        :param primitive_trunk: The primitive trunk this CI trunk is based on.
        """
        super().__init__(ci_repo, primitive_trunk)

    def __str__(self):
        return f"{self.ci_repo.GetGroup()}@{self.ci_repo.GetName()}@trunk"


class CiBranch(CiVersionEntity):
    """
    This class represents a Continuous Integration (CI) branch in a CI repository.
    """

    def __init__(self, ci_repo, primitive_branch):
        """
        Initializes a new instance of the CiBranch class.

        :param ci_repo: The CI repository this branch belongs to.
        :param primitive_branch: The primitive branch this CI branch is based on.
        """
        super().__init__(ci_repo, primitive_branch)

    def __str__(self):
        return f"{self.ci_repo.GetGroup()}@{self.ci_repo.GetName()}@branch@{self.primitive_entity.GetName()}"

    def RefreshRef(self):
        """
        1.Updating External References for the Current CI Branch:
        If the repository of the current CI branch references another repository that contains a branch with the same
        name, then the external reference of the current CI branch should be updated to reflect the latest state of
        that same-named branch.
        2.Updating External References Pointing to the Current CI Branch from Other Branches:
        If there are branches in other repositories that refer to the repository of the current CI branch, and those
        repositories contain branches with the same name as the current CI branch, then the external references of
        those same-named branches should be refreshed to point to the latest state of the current CI branch.

        This procedure ensures that all relevant branches across different repositories are synchronized with the most
        current changes.
        """
        # 更新外部引用
        print("refresh external ref for current new branch")
        ref_ci_repos = super().GetRefCiRepos()
        for ref_ci_repo in ref_ci_repos:
            ref_ci_branch = ref_ci_repo.GetBranch(self.primitive_entity.GetName())
            if ref_ci_branch is not None:
                super().UpdateRefEntity(ref_ci_branch)

        # 如本项目有项目分支引用到本分支，也需要刷新外部引用
        print("refresh external ref for project branch which refer to current new branch")
        ci_vcs = self.ci_repo.ci_vcs
        # ref can only be in the same vcs
        ci_repos = ci_vcs.GetAllRepoWithBranchInSingleVcs(self.ci_repo.GetPrimitiveVcs(), self.GetName())
        for ci_repo in ci_repos:
            tmp_feature_branches = ci_repo.GetBranches(f"{self.GetName()}.*")
            print(f"tmp_feature_branche count: {len(tmp_feature_branches)}")
            for tmp_feature_branch in tmp_feature_branches:
                print(f"tmp_feature_branch: {tmp_feature_branch.GetName()}")
                if tmp_feature_branch.ExistRepoRef(self.ci_repo):
                    tmp_feature_branch.UpdateRefEntity(self)

    def RefreshRefWhenDeleted(self):
        """
        Refreshes the external references of other branches when the current CI branch is deleted.
        """
        ci_vcs = self.ci_repo.ci_vcs
        # ref can only be in the same vcs
        ci_repos = ci_vcs.GetAllRepoWithBranchInSingleVcs(self.ci_repo.GetPrimitiveVcs(), self.primitive_entity.GetName())

        ci_trunk = self.ci_repo.GetTrunk()

        for ci_repo in ci_repos:
            tmp_feature_branches = ci_repo.GetBranches(f"{self.GetName()}.*")
            for tmp_feature_branch in tmp_feature_branches:
                if tmp_feature_branch.ExistRepoRef(self.ci_repo):
                    tmp_feature_branch.UpdateRefEntity(ci_trunk)


class CiTag(CiVersionEntity):
    """
    This class represents a Continuous Integration (CI) tag in a CI repository.
    """

    def __init__(self, ci_repo, primitive_tag):
        """
        Initializes a new instance of the CiTag class.

        :param ci_repo: The CI repository this tag belongs to.
        :param primitive_tag: The primitive tag this CI tag is based on.
        """
        super().__init__(ci_repo, primitive_tag)

    def __str__(self):
        return f"{self.ci_repo.GetGroup()}@{self.ci_repo.GetName()}@tag@{self.primitive_entity.GetName()}"

    def UpdateRefEntity(self, ref_ci_branch):
        raise Exception("tag can not be updated")

    def Commit(self, comment):
        raise Exception("tag can not be committed")

    def AddRef(self, ref_ci_version_entity, mount_rel_path, path_to_save_ref_for_svn=None):
        raise Exception("tag can not add ref")

    def RemoveRefByMountRelPath(self, mount_rel_path):
        raise Exception("tag can not remove ref")
