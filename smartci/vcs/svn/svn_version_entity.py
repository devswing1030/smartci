import os.path


class SvnVersionEntity:
    def __init__(self, vcs, repo, rel_path) -> None:
        self.vcs = vcs  # Svn
        self.repo = repo
        self.rel_path = rel_path
        parts = rel_path.split("/")
        self.name = parts[-1]
        if self.name == "trunk":
            self.type = "trunk"
        elif parts[-2] == "branches":
            self.type = "branch"
        elif parts[-2] == "tags":
            self.type = "tag"
        else:
            raise Exception("invalid svn path " + rel_path)

    def GetName(self):
        return self.name

    def GetType(self):
        return self.type

    def GetPrimitiveName(self):
        return self.name

    def GetUrl(self):
        return self.vcs.util.GetAbsolutePath(self.rel_path)

    def GetRelPath(self):
        return self.rel_path

    def GetFileContent(self, file_path) :
        return self.vcs.util.GetFileContent(self.rel_path + "/" + file_path)

    def PathExists(self, path):
        return self.vcs.util.PathExists(self.rel_path + "/" + path)

    def FileExists(self, file_path):
        return self.vcs.util.PathExists(self.rel_path + "/" + file_path)

    def CheckOut(self, local_path):
        self.vcs.util.CheckOut(self.rel_path, local_path)

    def CheckOutDirectory(self, local_path, rel_path):
        self.vcs.util.CheckOutDirectory(f"{self.rel_path}/{rel_path}", local_path)

    def AddToControl(self, local_path, target_rel_path):
        self.vcs.util.AddToControl(local_path, target_rel_path)

    def Commit(self, local_path, comment):
        self.vcs.util.Commit(local_path, comment)

    def AddFile(self, local_path, file_rel_path, content, comment):
        self.vcs.util.AddFile(local_path, f"{self.rel_path}/{file_rel_path}", content, comment)

    def RemoveFile(self, file_rel_path, comment):
        self.vcs.util.Remove(f"{self.rel_path}/{file_rel_path}", comment)

    def GetLastCommitId(self):
        return self.vcs.util.GetLastRevision(self.rel_path)

    def GetLastCommitInfo(self):
        return self.vcs.util.GetLastRevisionInfo(self.rel_path)

    def GetCommitIdOfLocalPath(self, local_path):
        return self.vcs.util.GetRevisionOfLocalPath(local_path)

    def GetCommitInfoOfLocalPath(self, local_path):
        return self.vcs.util.GetRevisionInfoOfLocalPath(local_path)

    def Copy(self, branch_name, comment):
        new_branch_path = self.repo.GetBranchPath() + "/" + branch_name
        if self.vcs.util.PathExists(new_branch_path):
            raise Exception("branch " + branch_name + " already exists")
        if comment is None:
            comment = "copy branch " + branch_name + " from branch " + self.GetName()
        self.vcs.util.Copy(self.rel_path, new_branch_path, comment)

    def CopyWithCommitId(self, branch_name, revision, comment):
        new_branch_path = self.repo.GetBranchPath() + "/" + branch_name
        if self.vcs.util.PathExists(new_branch_path):
            raise Exception("branch " + branch_name + " already exists")
        if comment is None:
            comment = "copy branch " + branch_name + " from branch " + self.GetName()
        self.vcs.util.Copy(self.rel_path, new_branch_path, comment, revision)

    def CreateTag(self, tag_name, revision, comment=None):
        if revision is None:
            revision = self.GetLastCommitId()
        print(f"Create tag {tag_name} for {self.rel_path}: {revision}")
        tag_path = self.repo.GetTagPath() + "/" + tag_name
        if self.vcs.util.PathExists(tag_path):
            raise Exception("tag " + tag_name + " already exists")
        if comment is None:
            comment = "create tag " + tag_name
        self.vcs.util.Copy(self.rel_path, tag_path, comment, revision)

    def AddRef(self, work_dir, external_entity, mount_rel_path, path_to_save_ref):
        self.vcs.util.AddExternal(work_dir, self.rel_path, external_entity.rel_path, mount_rel_path, path_to_save_ref)

    def GetRefVersionEntities(self, local_path):
        re = self.vcs.util.GetExternals(self.rel_path, local_path)
        result = []
        for path_to_save_ref, externals in re.items():
            for external in externals:
                repo = self.vcs.GetRepoByRelPath(external["abs"])
                if repo is None:
                    raise Exception("repo not found: " + external["abs"])
                entity = SvnVersionEntity(self.vcs, repo, external["abs"])
                result.append({"mount_rel_path": os.path.join(path_to_save_ref, external["mount_rel_path"]), "version_entity": entity})
        return result

    def RemoveRefByMountRelPath(self, work_dir, mount_rel_path):
        self.vcs.util.RemoveExternalByMountRelPath(work_dir, self.rel_path, mount_rel_path)

    def GetRefRepos(self):
        externals = self.vcs.util.GetExternalsPath(self.rel_path)
        result = []
        for path in externals:
            repo = self.vcs.GetRepoByRelPath(path)
            if repo is None:
                raise Exception("repo not found: " + path)
            result.append(repo)
        return result

    def UpdateRefEntity(self, local_path, external_branch):
        print("Refresh Ref to " + external_branch.GetUrl() + " for " + local_path)
        external_repo = self.vcs.GetRepoByRelPath(external_branch.rel_path)
        self.vcs.util.UpdateExternal(local_path, self.rel_path, external_repo.rel_path, external_branch.rel_path)

    def SetProtected(self, allowed_merge, allowed_push):
        pass

    def GetMergeRequestStatus(self, target_branch, local_path, min_reviewers=None):
        if target_branch.ContainsEntity(self):
            return {"merged": True}

        if self.vcs.util.HasConflict(self.rel_path, target_branch.rel_path, local_path):
            return {"merged": False, "can_be_merged": False, "message": "conflict with target branch"}

        return {"merged": False, "can_be_merged": True}

    def ContainsEntity(self, entity):
        diffs = self.vcs.util.GetBranchDiffRevision(entity.rel_path, self.rel_path)
        return diffs == ""
    def IsSupportMergeRequest(self):
        return False

    def CreateMergeRequest(self, target_branch, title, reviewers, description=None):
        # svn has no merge request, do nothing
        pass

    def GetMergeRequestWebUrl(self, target_entity):
        # svn has no merge request, do nothing
        return None

    def GetMergeRequestApprovalStatus(self, target_branch):
        # svn has no merge request, do nothing
        return None

    def CheckMergeRequestApproved(self, target_branch):
        # svn has no merge request, do nothing
        return True

    def AcceptMergeRequest(self, target_branch, comment, remove_branch_after_merge, local_path):
        self.MergeTo(target_branch, comment, local_path)
        if remove_branch_after_merge:
            self.repo.DeleteBranch(self.name, "remove branch " + self.name + " after merge")

    def MergeTo(self, target_branch, comment, local_path):
        self.vcs.util.MergeTo(self.rel_path, target_branch.rel_path, comment, local_path)

    def GetDiffFiles(self, from_entity):
        tmp_diffs = self.vcs.util.GetDiffFiles(from_entity.rel_path, self.rel_path)
        diffs = []
        for tmp_diff in tmp_diffs:
            diff = {}
            diff['path'] = tmp_diff['path'][len(from_entity.rel_path)+1:]
            diff['type'] = tmp_diff['type']
            diffs.append(diff)
        return diffs

    def Rollback(self, revision, comment, local_path):
        self.vcs.util.Rollback(self.rel_path, revision, comment, local_path)

    def AddWebHook(self, url, secret_token):
        pass

    def DeleteWebHook(self, url):
        pass
