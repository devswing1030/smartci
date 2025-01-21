# -*- coding:utf-8 -*-
import re
import time


class GitVersionEntity:
    def __init__(self, vcs, repo, name) -> None:
        self.vcs = vcs  # Git
        self.repo = repo
        self.name = name
        self.type = repo.GetVersionEntityType(name)

    def GetName(self):
        if self.type == "trunk":
            return "trunk"
        return self.name

    def GetType(self):
        return self.type

    def GetPrimitiveName(self):
        return self.name

    def GetUrl(self):
        if self.type == "branch":
            return self.vcs.util.GetBranchUrl(self.repo.GetProjectID(), self.name)
        elif self.type == "tag":
            return self.vcs.util.GetTagUrl(self.repo.GetProjectID(), self.name)

    def GetFileContent(self, file_path):
        return self.vcs.util.GetFileContent(self.repo.GetProjectID(), self.name, file_path)

    def PathExists(self, path):
        return self.vcs.util.PathExists(self.repo.GetProjectID(), self.name, path)

    def FileExists(self, file_path):
        return self.vcs.util.FileExists(self.repo.GetProjectID(), self.name, file_path)

    def CheckOut(self, local_path):
        self.vcs.util.CheckOut(local_path, self.repo.GetHttpCloneUrl(), self.name)

    def CheckOutDirectory(self, local_path, rel_path):
        self.vcs.util.CheckOutDirectory(local_path, self.repo.GetHttpCloneUrl(), self.name, rel_path)

    def CheckOutFile(self, local_path, file_rel_path):
        self.vcs.util.CheckOutFile(local_path, self.repo.GetHttpCloneUrl(), self.name, file_rel_path)

    def AddToControl(self, local_path, target_path):
        self.vcs.util.AddToControl(local_path, target_path)

    def Commit(self, local_path, comment):
        self.vcs.util.Commit(local_path, comment)

    def AddFile(self, local_path, file_rel_path, content, comment):
        self.vcs.util.AddFile(self.repo.GetProjectID(), self.name, file_rel_path, content, comment)

    def RemoveFile(self, file_rel_path, comment):
        self.vcs.util.RemoveFile(self.repo.GetProjectID(), self.name, file_rel_path, comment)

    def GetLastCommitId(self):
        return self.vcs.util.GetLastCommitIdOfBranch(self.repo.GetProjectID(), self.name)

    def GetLastCommitInfo(self):
        return self.vcs.util.GetLastCommitInfoOfBranch(self.repo.GetProjectID(), self.name)

    def GetCommitIdOfLocalPath(self, local_path):
        return self.vcs.util.GetCommitIdOfLocalPath(local_path)

    def GetCommitInfoOfLocalPath(self, local_path):
        return self.vcs.util.GetCommitInfoOfLocalPath(local_path)

    def Copy(self, branch_name, comment):
        self.vcs.util.AddBranch(self.repo.GetProjectID(), branch_name, self.name)

    def CopyWithCommitId(self, branch_name, commit_id, comment):
        self.vcs.util.AddBranch(self.repo.GetProjectID(), branch_name, commit_id)

    def CreateTag(self, tag_name, commit_id, comment=None):
        if commit_id is None:
            commit_id = self.GetLastCommitId()
        print(f"Create tag {tag_name} for {self.repo.GetProjectName()}: {commit_id}")
        self.vcs.util.AddTag(self.repo.GetProjectID(), tag_name, commit_id)

    def GetRefRepos(self):
        submodules = self.vcs.util.GetSubModules(self.repo.GetProjectID(), self.name)
        result = []
        for anchor, submodule in submodules.items():
            repo = self.vcs.GetRepoByUrl(submodule['url'])
            if repo is None:
                raise Exception("repo not found: " + submodule['url'])
            result.append(repo)
        return result

    def GetRefVersionEntities(self, loal_path):
        submodules = self.vcs.util.GetSubModules(self.repo.GetProjectID(), self.name, loal_path)
        result = []
        for mount_rel_path, submodule in submodules.items():
            repo = self.vcs.GetRepoByUrl(submodule['url'])
            if repo is None:
                raise Exception("repo not found: " + submodule['url'])
            entity = GitVersionEntity(self.vcs, repo, submodule['branch'])
            result.append({"mount_rel_path": mount_rel_path, "version_entity": entity})
        return result

    def AddRef(self, work_dir, ref_entity, mount_rel_path, placeholder2):
        self.CheckOut(work_dir)
        self.vcs.util.AddSubModule(work_dir, self.repo.GetProjectID(), self.name,
                                   ref_entity.repo.GetHttpCloneUrl(), ref_entity.GetPrimitiveName(), mount_rel_path)

    def RemoveRefByMountRelPath(self, work_dir, mount_rel_path):
        self.CheckOut(work_dir)
        self.vcs.util.RemoveSubModuleByMountRelPath(work_dir, self.repo.GetProjectID(), self.name, mount_rel_path)

    def UpdateRefEntity(self, local_path, ref_entity):
        ref_repo_url = ref_entity.repo.GetHttpCloneUrl()
        self.vcs.util.UpdateSubModule(self.repo.GetProjectID(), self.name, ref_repo_url, ref_entity.name)

    def SetProtected(self, allowed_merge, allowed_push):
        self.vcs.util.SetBranchProtected(self.repo.GetProjectID(), self.name, allowed_merge, allowed_push)

    def GetProtectedInfo(self):
        return self.vcs.util.GetBranchProtectedInfo(self.repo.GetProjectID(), self.name)

    def GetMergeRequestStatus(self, target_branch, local_path, min_reviewers=1):
        mr_info = self.vcs.util.GetMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName())
        if mr_info is None:
            return {"merged": False, "can_be_merged": False, "message": "no merge request"}
        if mr_info['mr']['state'] == "merged":
            return {"merged": True}

        approved_detail = self.GetMergeRequestApprovalStatus(target_branch, min_reviewers)
        if not approved_detail["approved"]:
            if len(approved_detail["reviewers"]) < min_reviewers:
                return {"merged": False, "can_be_merged": False, "message": "not enough reviewers"}
            else:
                return {"merged": False, "can_be_merged": False, "message": "not approved"}

        has_conflict = mr_info['mr']['has_conflicts']
        if has_conflict:
            return {"merged": False, "can_be_merged": False, "message": "conflict with target branch"}
        can_be_merged = mr_info['mr']['merge_status'] == "can_be_merged"
        if not can_be_merged:
            return {"merged": False, "can_be_merged": False, "message": "There has been a problem with the merge request, please check the merge request status."}
        work_in_progress = mr_info['mr']['work_in_progress']
        if work_in_progress:
            return {"merged": False, "can_be_merged": False, "message": "work in progress"}

        return {"merged": False, "can_be_merged": True}

    def IsSupportMergeRequest(self):
        return True

    def CreateMergeRequest(self, target_branch, title, reviewers, description=None):
        if description is None:
            description = ""
        for reviewer in reviewers:
            description = description + f"\n@{reviewer}"
        self.vcs.util.CreateMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName(), title, description)

    def GetMergeRequestWebUrl(self, target_branch):
        return self.vcs.util.GetMergeRequestWebUrl(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName())

    def GetMergeRequestApprovalStatus(self, target_branch, min_reviewers=1):
        mr_info = self.vcs.util.GetMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName())
        if mr_info is None:
            return None
        description = mr_info['mr']['description']

        # get @user in description
        reviewers = re.findall(r'@([\w\.]+)', description)
        if "reviewers" in mr_info['mr']:
            for reviewer in  mr_info['mr']['reviewers']:
                reviewers.append(reviewer['username'])


        approvals = []
        for user in mr_info["approvals"]["approved_by"]:
            approvals.append(user["user"]["username"])

        if len(approvals) < min_reviewers:
            approved = False
        else:
            if len(reviewers) == 0:
                approved = True
            else:
                approved = set(reviewers).issubset(approvals)

        return {"approved": approved, "approvals": approvals, "reviewers": reviewers}

    def AcceptMergeRequest(self, target_branch, comment, remove_branch_after_merge, local_path=None):
        self.vcs.util.AcceptMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName(),
                                         comment, remove_branch_after_merge)

    def MergeTo(self, target_branch, comment, local_path=None):
        """
        self.CreateMergeRequest(target_branch, "merge by smartci", [])
        while self.vcs.util.GetMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName()) is None:
            time.sleep(1)
        while True:
            mr_info = self.vcs.util.GetMergeRequest(self.repo.GetProjectID(), self.GetPrimitiveName(), target_branch.GetPrimitiveName())
            if mr_info['mr']['state'] == "opened" \
                and mr_info['mr']['merge_status'] == "can_be_merged":
                break
            time.sleep(1)

        """
        self.AcceptMergeRequest(target_branch, comment, False)

    def GetDiffFiles(self, from_entity):
        tmp_diffs = self.vcs.util.GetDiffFiles(self.repo.GetProjectID(), from_entity.GetPrimitiveName(), self.GetPrimitiveName())
        diffs = []
        for tmp_diff in tmp_diffs:
            diff = {}
            diff['path'] = tmp_diff['old_path']
            if tmp_diff['new_file']:
                diff['type'] = "A"
            elif tmp_diff['deleted_file']:
                diff['type'] = "D"
            elif tmp_diff['renamed_file']:
                diffs.append({"path": tmp_diff['new_path'], "type": "A"})
                diffs.append({"path": tmp_diff['old_path'], "type": "D"})
                continue
            else:
                diff['type'] = "M"
            diffs.append(diff)
        return diffs

    def Rollback(self, commit_id, comment, local_path):
        self.CheckOut(local_path)
        self.vcs.util.Rollback(local_path, commit_id)

    def ContainsEntity(self, entity):
        return self.vcs.util.ContainsEntity(self.repo.GetProjectID(), self.GetPrimitiveName(), entity.GetPrimitiveName())

    def AddWebHook(self, url, secret_token):
        self.vcs.util.AddWebHook(self.repo.GetProjectID(), self.GetPrimitiveName(), url, secret_token)

    def DeleteWebHook(self, url):
        self.vcs.util.DeleteWebHook(self.repo.GetProjectID(), url)



