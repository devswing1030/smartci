# -*- coding:utf-8 -*-
import hashlib
import json
import os.path
import shutil
import time
#import unittest
from datetime import datetime
import pytest
from smartci.ci_vcs import CiVcs

"""
Requirements:
   1. Prepare a VCS server, such as SVN or Git.
   2. Prepare at least 3 application repositories in the VCS server, and each repository contains .ci/settings.yml file.
   3. Configure the VCS server in the ci_vcs.cfg.yml file.
   4. Configure the CI_WORKSPACE environment variable to the directory where the ci_vcs.cfg.yml file is located.
"""

ci_vcs = CiVcs.Create()

svn_repo_list = []
git_repo_list = []

for vcs in ci_vcs.vcs_list:
    if vcs.type == "svn":
        svn_repo_list = ci_vcs.GetAllRepoInSingleVcs(vcs)
        break

for vcs in ci_vcs.vcs_list:
    if vcs.type == "git":
        git_repo_list = ci_vcs.GetAllRepoInSingleVcs(vcs)
        break


def test_get_all_repo():
    ci_vcs = CiVcs.Create()
    ci_repos = ci_vcs.GetAllRepo()
    assert len(ci_repos) > 0
    for ci_repo in ci_repos:
        print(ci_repo.GetUrl())
        print(ci_repo.GetGroup())
        print(ci_repo.GetName())


def get_unique_name():
    now = datetime.now()
    branch_name = now.strftime("%Y%m%d%H%M%S%f")
    return branch_name


def get_default_checkout_path(ci_branch):
    ci_work_space = os.getenv("CI_WORKSPACE")
    md5 = hashlib.md5(str(ci_branch).encode('utf-8')).hexdigest()
    return os.path.join(ci_work_space, "tmp", md5)


def get_repo(ci_repo):
    group = ci_repo.GetGroup()
    name = ci_repo.GetName()
    ci_vcs = CiVcs.Create()
    tmp_ci_repo = ci_vcs.GetRepo(group, name)
    assert tmp_ci_repo.GetUrl() == ci_repo.GetUrl()


def add_branch(ci_repo):
    branch_name = get_unique_name()
    ci_repo.AddBranch(branch_name)
    ci_branch = ci_repo.GetBranch(branch_name)
    assert ci_branch is not None
    assert ci_branch.GetName() == branch_name
    ci_repo.DeleteBranch(branch_name)


def add_tag_for_trunk(ci_repo):
    ci_trunk = ci_repo.GetTrunk()
    tag_name = "tag_" + get_unique_name()
    ci_trunk.CreateTag(tag_name, None)
    ci_tag = ci_repo.GetTag(tag_name)
    assert ci_tag is not None
    assert ci_tag.GetName() == tag_name
    ci_repo.DeleteTag(tag_name)


def add_tag_for_branch(ci_repo):
    branch_name = get_unique_name()
    ci_repo.AddBranch(branch_name)
    ci_branch = ci_repo.GetBranch(branch_name)
    assert ci_branch is not None
    tag_name = "tag_" + branch_name
    ci_branch.CreateTag(tag_name, None)
    ci_tag = ci_repo.GetTag(tag_name)
    assert ci_tag is not None
    assert ci_tag.GetName() == tag_name
    ci_repo.DeleteTag(tag_name)
    ci_repo.DeleteBranch(branch_name)


def add_tag_for_special_commit_id(ci_repo):
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    checkout_path = get_default_checkout_path(ci_branch)
    ci_branch.CheckOut(checkout_path)

    test_file_path = os.path.join(checkout_path, "test.txt")
    with open(test_file_path, "w") as f:
        f.write("hello world")
    f.close()
    ci_branch.AddToControl(checkout_path, "test.txt")
    ci_branch.Commit(checkout_path, "add test.txt")
    commit_id = ci_branch.GetLastCommitId()

    test_file_path = os.path.join(checkout_path, "test1.txt")
    with open(test_file_path, "w") as f:
        f.write("hello world")
    f.close()
    ci_branch.AddToControl(checkout_path, "test1.txt")
    ci_branch.Commit(checkout_path, "add test1.txt")

    tag_name = "tag_" + branch_name
    ci_branch.CreateTag(tag_name, commit_id)
    ci_tag = ci_repo.GetTag(tag_name)
    assert ci_tag is not None
    assert ci_tag.GetName() == tag_name
    assert ci_tag.FileExists("test.txt")
    assert not ci_tag.FileExists("test1.txt")

    ci_repo.DeleteTag(tag_name)
    ci_repo.DeleteBranch(branch_name)
    shutil.rmtree(checkout_path)


def add_ref_for_trunk(ci_repo, ref_ci_repo):
    ci_trunk = ci_repo.GetTrunk()
    print(ci_trunk.GetName())
    ref_ci_trunk = ref_ci_repo.GetTrunk()

    try:
        test_file = get_unique_name() + ".txt"
        ref_ci_trunk.AddFile(test_file, "hello world", "add test.txt")

        mount_rel_path = get_unique_name() + "/lib"
        ci_trunk.AddRef(ref_ci_trunk, mount_rel_path)

        assert ci_trunk.ExistEntityRef(ref_ci_trunk, mount_rel_path)
        assert ci_trunk.ExistRepoRef(ref_ci_repo)

        checkout_path = get_default_checkout_path(ci_trunk)
        ci_trunk.CheckOut(checkout_path)
        assert os.path.exists(os.path.join(checkout_path, mount_rel_path, test_file))
    finally:
        shutil.rmtree(checkout_path, ignore_errors=True)
        ref_ci_trunk.RemoveFile(test_file, "remove test.txt")
        ci_trunk.RemoveRefByMountRelPath(mount_rel_path)
        assert not ci_trunk.ExistEntityRef(ref_ci_trunk, mount_rel_path)


def update_ref_for_branch(ci_repo, ref_ci_repo):
    ci_trunk = ci_repo.GetTrunk()
    ref_ci_trunk = ref_ci_repo.GetTrunk()
    try:
        mount_rel_path = get_unique_name() + "/lib"
        ci_trunk.AddRef(ref_ci_trunk, mount_rel_path)

        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        ref_ci_branch = ref_ci_repo.AddBranch(branch_name)

        test_file = get_unique_name() + ".txt"
        ref_ci_branch.AddFile(test_file, "hello world", "add test.txt")

        ci_branch.UpdateRefEntity(ref_ci_branch)
        assert ci_branch.ExistEntityRef(ref_ci_branch, mount_rel_path)

        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        assert os.path.exists(os.path.join(checkout_path, mount_rel_path, test_file))

    finally:
        shutil.rmtree(checkout_path, ignore_errors=True)
        ci_trunk.RemoveRefByMountRelPath(mount_rel_path)
        ci_repo.DeleteBranch(branch_name)
        ref_ci_repo.DeleteBranch(branch_name)


def refresh_ref(ci_repo_list):
    ci_repo = ci_repo_list[0]
    ci_trunk = ci_repo.GetTrunk()

    ci_ref_repo1 = ci_repo_list[1]
    ci_ref_trunk1 = ci_ref_repo1.GetTrunk()

    ci_ref_repo2 = ci_repo_list[2]
    ci_ref_trunk2 = ci_ref_repo2.GetTrunk()

    mount_rel_path1 = get_unique_name() + "/lib1"
    ci_trunk.AddRef(ci_ref_trunk1, mount_rel_path1)
    mount_rel_path2 = get_unique_name() + "/lib2"
    ci_trunk.AddRef(ci_ref_trunk2, mount_rel_path2)

    branch_name = get_unique_name()
    ci_ref_branch1 = ci_ref_repo1.AddBranch(branch_name)
    ci_ref_branch1.RefreshRef()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.RefreshRef()

    assert ci_branch.ExistEntityRef(ci_ref_branch1, mount_rel_path1)
    assert ci_branch.ExistEntityRef(ci_ref_trunk2, mount_rel_path2)

    ci_repo.DeleteBranch(branch_name)
    ci_ref_repo1.DeleteBranch(branch_name)

    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.RefreshRef()

    ci_feature_branch = ci_branch.Copy(branch_name + "_feature", "for test")

    time.sleep(30)
    ci_ref_branch2 = ci_ref_repo2.AddBranch(branch_name)
    ci_ref_branch2.RefreshRef()

    assert ci_branch.ExistEntityRef(ci_ref_trunk1, mount_rel_path1)
    assert ci_branch.ExistEntityRef(ci_ref_branch2, mount_rel_path2)
    assert ci_feature_branch.ExistEntityRef(ci_ref_trunk1, mount_rel_path1)
    assert ci_feature_branch.ExistEntityRef(ci_ref_branch2, mount_rel_path2)

    ci_repo.DeleteBranch(branch_name)
    ci_repo.DeleteBranch(ci_feature_branch.GetName())
    ci_ref_repo2.DeleteBranch(branch_name)

    ci_trunk.RemoveRefByMountRelPath(mount_rel_path1)
    ci_trunk.RemoveRefByMountRelPath(mount_rel_path2)


def refresh_ref_when_deleted(ci_repo_list):
    ci_repo = ci_repo_list[0]
    ci_trunk = ci_repo.GetTrunk()

    ci_ref_repo1 = ci_repo_list[1]
    ci_ref_trunk1 = ci_ref_repo1.GetTrunk()

    ci_ref_repo2 = ci_repo_list[2]
    ci_ref_trunk2 = ci_ref_repo2.GetTrunk()

    mount_rel_path1 = get_unique_name() + "/lib1"
    ci_trunk.AddRef(ci_ref_trunk1, mount_rel_path1)
    mount_rel_path2 = get_unique_name() + "/lib2"
    ci_trunk.AddRef(ci_ref_trunk2, mount_rel_path2)

    branch_name = get_unique_name()
    ci_ref_branch1 = ci_ref_repo1.AddBranch(branch_name)
    ci_ref_branch1.RefreshRef()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.RefreshRef()
    ci_feature_branch = ci_branch.Copy(branch_name + "_feature", "for test")

    assert ci_branch.ExistEntityRef(ci_ref_branch1, mount_rel_path1)
    assert ci_branch.ExistEntityRef(ci_ref_trunk2, mount_rel_path2)
    assert ci_feature_branch.ExistEntityRef(ci_ref_branch1, mount_rel_path1)
    assert ci_feature_branch.ExistEntityRef(ci_ref_trunk2, mount_rel_path2)

    time.sleep(15)
    ci_ref_branch1.RefreshRefWhenDeleted()
    ci_ref_repo1.DeleteBranch(branch_name)

    assert ci_branch.ExistEntityRef(ci_ref_trunk1, mount_rel_path1)
    assert ci_branch.ExistEntityRef(ci_ref_trunk2, mount_rel_path2)
    assert ci_feature_branch.ExistEntityRef(ci_ref_trunk1, mount_rel_path1)
    assert ci_feature_branch.ExistEntityRef(ci_ref_trunk2, mount_rel_path2)

    ci_repo.DeleteBranch(branch_name)
    ci_ref_repo2.DeleteBranch(branch_name)

    ci_trunk.RemoveRefByMountRelPath(mount_rel_path1)
    ci_trunk.RemoveRefByMountRelPath(mount_rel_path2)


def get_file(ci_repo):
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    checkout_path = get_default_checkout_path(ci_branch)
    ci_branch.CheckOut(checkout_path)
    content = "hello world"
    test_file_name = "test.txt"
    test_file_path = os.path.join(checkout_path, test_file_name)
    with open(test_file_path, "w") as f:
        f.write(content)
        f.close()
    ci_branch.AddToControl(checkout_path, test_file_name)
    ci_branch.Commit(checkout_path, "add %s" % test_file_name)
    ci_branch.FileExists(test_file_name)
    shutil.rmtree(checkout_path)

    ci_work_space = os.getenv("CI_WORKSPACE")
    tmp_path = os.path.join(ci_work_space, "tmp", branch_name)
    ci_branch.GetFile(test_file_name, tmp_path)
    with open(os.path.join(tmp_path, test_file_name), "r") as f:
        assert f.read() == content
        f.close()

    shutil.rmtree(tmp_path)

    ci_repo.DeleteBranch(branch_name)


def checkout(ci_repo):
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    checkout_path = get_default_checkout_path(ci_branch)
    ci_branch.CheckOut(checkout_path)
    assert os.path.exists(checkout_path)
    test_file_name = "test.txt"
    test_file_path = os.path.join(checkout_path, test_file_name)
    with open(test_file_path, "w") as f:
        f.write("hello world")
        f.close()
    ci_branch.AddToControl(checkout_path, test_file_name)
    ci_branch.Commit(checkout_path, "add %s" % test_file_name)
    shutil.rmtree(checkout_path)

    ci_repo.DeleteBranch(branch_name)


def copy(ci_repo):
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    branch_copy_name = branch_name + "_copy"
    ci_copy_branch = ci_branch.Copy(branch_copy_name)
    assert ci_copy_branch is not None
    assert ci_copy_branch.GetName() == branch_copy_name

    ci_repo.DeleteBranch(branch_name)
    ci_repo.DeleteBranch(branch_copy_name)


def get_branches(ci_repo):
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.Copy(branch_name + "_copy1")
    ci_branch.Copy(branch_name + "_copy2")

    ci_branch_list = ci_repo.GetBranches(branch_name + ".*")
    assert len(ci_branch_list) == 3
    assert ci_branch_list[0].GetName() == branch_name
    assert ci_branch_list[1].GetName() == branch_name + "_copy1"
    assert ci_branch_list[2].GetName() == branch_name + "_copy2"

    ci_repo.DeleteBranch(branch_name)
    ci_repo.DeleteBranch(branch_name + "_copy1")
    ci_repo.DeleteBranch(branch_name + "_copy2")


def get_all_branches(ci_repo):
    ci_branch_list = ci_repo.GetAllBranches()
    count = len(ci_branch_list)

    added_count = 10
    prefix = get_unique_name()
    for i in range(added_count):
        branch_name = prefix + str(i)
        ci_repo.AddBranch(branch_name)

    time.sleep(15)

    ci_branch_list = ci_repo.GetAllBranches()
    assert len(ci_branch_list) == count + added_count

    for i in range(added_count):
        branch_name = prefix + str(i)
        ci_repo.DeleteBranch(branch_name)


def test_set_protected():
    ci_repo = git_repo_list[0]
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.DisablePush()
    assert not ci_branch.IsAllowedPush()
    ci_branch.EnablePush()
    assert ci_branch.IsAllowedPush()

    ci_repo.DeleteBranch(branch_name)


def delete_branch(ci_repo):
    branch_name = get_unique_name()
    ci_repo.AddBranch(branch_name)
    assert ci_repo.GetBranch(branch_name) is not None
    ci_repo.DeleteBranch(branch_name)
    assert ci_repo.GetBranch(branch_name) is None


def delete_tag(ci_repo):
    tag_name = "tag_" + get_unique_name()
    ci_repo.GetTrunk().CreateTag(tag_name, None)
    assert ci_repo.GetTag(tag_name) is not None
    ci_repo.DeleteTag(tag_name)
    assert ci_repo.GetTag(tag_name) is None


def get_repo_by_url(ci_repo):
    url = ci_repo.GetUrl()
    ci_vcs = CiVcs.Create()
    tmp_ci_repo = ci_vcs.GetCiRepoByUrl(url)
    assert tmp_ci_repo.GetUrl() == ci_repo.GetUrl()



def test_checkout_git_file():
    ci_repo = git_repo_list[0]
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    checkout_path = get_default_checkout_path(ci_branch)

    test_file_name = ".ci"

    ci_branch.primitive_entity.CheckOutFile(checkout_path, test_file_name)
    assert os.path.exists(os.path.join(checkout_path, test_file_name))

    ci_repo.DeleteBranch(branch_name)



def test_get_merge_request_status_git():
    ci_repo = git_repo_list[0]

    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    file_name = f"{get_unique_name()}.txt"
    ci_branch.AddFile(file_name, "hello world", "add test.txt")

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False


    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), f"for mr test {branch_name}", [])
    time.sleep(10)

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == True

    ci_branch.AcceptMergeRequest(ci_repo.GetTrunk(), "test merge request")
    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)
    assert status["merged"] == True

    ci_repo.DeleteBranch(branch_name)
    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)

def test_get_merge_request_status_git_wip():
    ci_repo = git_repo_list[0]

    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    file_name = f"{get_unique_name()}.txt"
    ci_branch.AddFile(file_name, "hello world", "add test.txt")

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False


    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), f"Draft:for mr test {branch_name}", [])
    time.sleep(10)

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 0)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False

def test_get_merge_request_status_git_approve():
    ci_repo = git_repo_list[0]

    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    file_name = f"{get_unique_name()}.txt"
    ci_branch.AddFile(file_name, "hello world", "add test.txt")

    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), f"for mr test {branch_name}", [])
    time.sleep(10)

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 1)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False

    ci_repo.DeleteBranch(branch_name)

def test_get_merge_request_status_git_approve1():
    ci_repo = git_repo_list[0]

    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    file_name = f"{get_unique_name()}.txt"
    ci_branch.AddFile(file_name, "hello world", "add test.txt")

    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), f"for mr test {branch_name}", ["tom.oth", "jerry"])
    time.sleep(10)

    approve_status = ci_branch.GetMergeRequestApprovalStatus(ci_repo.GetTrunk())
    print(approve_status)

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 3)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False

    status = ci_branch.GetMergeRequestStatus(ci_repo.GetTrunk(), 2)
    print(status)
    assert status["merged"] == False
    assert status["can_be_merged"] == False

    ci_repo.DeleteBranch(branch_name)



def test_get_merge_request_web_url():
    ci_repo = git_repo_list[0]
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), "for mr test", [])
    print(ci_branch.GetMergeRequestWebUrl(ci_repo.GetTrunk()))
    assert ci_branch.GetMergeRequestWebUrl(ci_repo.GetTrunk()) is not None
    ci_repo.DeleteBranch(branch_name)


def test_get_merge_request_approval_status():
    ci_repo = git_repo_list[0]
    branch_name = get_unique_name()
    ci_branch = ci_repo.AddBranch(branch_name)
    ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), "for mr test", ["tom", "jerry"])
    status = ci_branch.GetMergeRequestApprovalStatus(ci_repo.GetTrunk())
    print(status)
    assert not status["approved"]
    assert status["reviewers"] == ["tom", "jerry"]
    assert status["approvals"] == []
    ci_repo.DeleteBranch(branch_name)



parameters = [
    pytest.param(svn_repo_list, marks=pytest.mark.skipif(len(svn_repo_list) == 0, reason="no svn repo")),
    pytest.param(git_repo_list, marks=pytest.mark.skipif(len(git_repo_list) == 0, reason="no git repo")),
]


@pytest.mark.parametrize('repo_list', parameters)
class TestVcs:
    def test_get_repo(self, repo_list):
        get_repo(repo_list[0])

    def test_add_branch(self, repo_list):
        add_branch(repo_list[0])

    def test_add_tag(self, repo_list):
        add_tag_for_trunk(repo_list[0])

    def test_add_tag_for_branch(self, repo_list):
        add_tag_for_branch(repo_list[0])

    def test_add_tag_for_special_commit_id(self, repo_list):
        add_tag_for_special_commit_id(repo_list[0])

    def test_add_ref_for_trunk(self, repo_list):
        add_ref_for_trunk(repo_list[0], repo_list[1])

    def test_update_ref_for_branch(self, repo_list):
        update_ref_for_branch(repo_list[0], repo_list[1])

    def test_refresh_ref(self, repo_list):
        refresh_ref(repo_list)

    def test_refresh_ref_when_deleted(self, repo_list):
        refresh_ref_when_deleted(repo_list)

    def test_get_file(self, repo_list):
        get_file(repo_list[0])

    def test_checkout(self, repo_list):
        checkout(repo_list[0])

    def test_copy(self, repo_list):
        copy(repo_list[0])

    def test_get_branches(self, repo_list):
        get_branches(repo_list[0])

    def test_get_all_branches(self, repo_list):
        get_all_branches(repo_list[0])

    def test_delete_branch(self, repo_list):
        delete_branch(repo_list[0])

    def test_delete_tag(self, repo_list):
        delete_tag(repo_list[0])

    def test_get_repo_by_url(self, repo_list):
        get_repo_by_url(repo_list[0])

    def test_checkout_directory(self, repo_list):
        ci_repo = repo_list[0]
        ci_trunk = ci_repo.GetTrunk()
        checkout_path = get_default_checkout_path(ci_trunk)
        ci_trunk.CheckOutDirectory(checkout_path, ".ci")

        assert os.path.exists(os.path.join(checkout_path, ".ci"))

        shutil.rmtree(checkout_path)

    def test_add_file(self, repo_list):
        ci_repo = repo_list[0]
        ci_trunk = ci_repo.GetTrunk()
        tmp_file_name = f"{get_unique_name()}_test.txt"
        ci_trunk.AddFile(tmp_file_name, "hello world", "add test.txt")
        assert ci_trunk.FileExists(tmp_file_name)

        ci_trunk.RemoveFile(tmp_file_name, "remove test.txt")
        assert not ci_trunk.FileExists(tmp_file_name)

    def test_get_version_entity_from_local_path(self, repo_list):
        ci_repo = repo_list[0]
        ci_trunk = ci_repo.GetTrunk()
        checkout_path = get_default_checkout_path(ci_trunk)
        ci_trunk.CheckOut(checkout_path)
        ci_vcs = CiVcs.Create()
        assert ci_trunk.GetUrl() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).GetUrl()
        assert ci_trunk.ci_repo.GetGroup() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).ci_repo.GetGroup()
        assert ci_trunk.ci_repo.GetName() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).ci_repo.GetName()
        shutil.rmtree(checkout_path)

        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)

        print(f"ci_branch: {ci_branch}")

        ci_local_branch = ci_vcs.GetVersionEntityFromLocalPath(checkout_path)
        print(f"ci_local_branch: {ci_local_branch}")

        assert ci_branch.GetUrl() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).GetUrl()
        assert ci_branch.ci_repo.GetGroup() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).ci_repo.GetGroup()
        assert ci_branch.ci_repo.GetName() == ci_vcs.GetVersionEntityFromLocalPath(checkout_path).ci_repo.GetName()

        shutil.rmtree(checkout_path)
        ci_repo.DeleteBranch(branch_name)

    def test_get_commit_id_of_local_path(self, repo_list):
        ci_repo = repo_list[0]
        ci_trunk = ci_repo.GetTrunk()
        checkout_path = get_default_checkout_path(ci_trunk)
        ci_trunk.CheckOut(checkout_path)
        assert ci_trunk.GetLastCommitId() == ci_trunk.GetCommitIdOfLocalPath(checkout_path)
        shutil.rmtree(checkout_path)


    def test_accept_merge_request(self, repo_list):
        ci_repo = repo_list[0]

        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        ci_branch.CreateMergeRequest(ci_repo.GetTrunk(), f"for mr test {branch_name}", [])
        file_name = f"{get_unique_name()}.txt"
        ci_branch.AddFile(file_name, "hello world", "add test.txt")

        time.sleep(10)

        ci_branch.AcceptMergeRequest(ci_repo.GetTrunk(), "test merge request", True)

        assert ci_repo.GetTrunk().FileExists(file_name)
        ci_repo.GetTrunk().RemoveFile(file_name, "remove test.txt")

        assert ci_repo.GetBranch(branch_name) is None


    def test_get_merge_request_status_confict(self, repo_list):
        ci_repo = repo_list[0]

        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        file_name = f"{get_unique_name()}.txt"
        ci_branch.AddFile(file_name, "hello world", "add test.txt")
        ci_feature_branch = ci_branch.Copy(branch_name + "_feature", "for test")

        checkout_path = get_default_checkout_path(ci_feature_branch)
        ci_feature_branch.CheckOut(checkout_path)
        test_file_path = os.path.join(checkout_path, file_name)
        with open(test_file_path, "w") as f:
            f.write("hello world2")
            f.close()
        ci_feature_branch.Commit(checkout_path, "modify test.txt")
        shutil.rmtree(checkout_path)

        ci_feature_branch.CreateMergeRequest(ci_branch, f"for mr test {branch_name}", [])
        time.sleep(10)

        status = ci_feature_branch.GetMergeRequestStatus(ci_branch, 0)
        print(status)
        assert status["merged"] == False
        assert status["can_be_merged"] == True


        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        test_file_path = os.path.join(checkout_path, file_name)
        with open(test_file_path, "w") as f:
            f.write("hello world1")
            f.close()
        ci_branch.Commit(checkout_path, "modify test.txt")
        shutil.rmtree(checkout_path)

        time.sleep(10)

        status = ci_feature_branch.GetMergeRequestStatus(ci_branch, 0)
        print(status)
        assert status["merged"] == False
        assert status["can_be_merged"] == False

        ci_repo.DeleteBranch(branch_name)
        ci_repo.DeleteBranch(ci_feature_branch.GetName())

    def test_get_ref_from_local_path(self, repo_list):
        ci_repo = repo_list[0]
        ci_trunk = ci_repo.GetTrunk()

        ci_ref_repo1 = repo_list[1]
        ci_ref_trunk1 = ci_ref_repo1.GetTrunk()

        mount_rel_path1 = get_unique_name() + "/lib1"
        ci_trunk.AddRef(ci_ref_trunk1, mount_rel_path1)

        checkout_path = get_default_checkout_path(ci_trunk)
        ci_trunk.CheckOut(checkout_path)
        refs = ci_trunk.GetRefCiVersionEntities(checkout_path)
        shutil.rmtree(checkout_path)

        found = False
        for ref in refs:
            if ref["version_entity"].GetUrl() == ci_ref_trunk1.GetUrl() and ref["mount_rel_path"] == mount_rel_path1:
                found = True
                break

        assert found


        ci_trunk.RemoveRefByMountRelPath(mount_rel_path1)

    def test_get_diff_files_add(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        test_dir = get_unique_name()
        os.makedirs(os.path.join(checkout_path, test_dir))

        test_file_name = os.path.join(test_dir, 'test.txt')
        content = "hello world"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write(content)
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)
        diff_files = ci_branch.GetDiffFiles(ci_repo.GetTrunk())
        assert len(diff_files) == 1
        assert diff_files[0]['path'] == test_file_name
        assert diff_files[0]['type'] == "A"
        ci_repo.DeleteBranch(branch_name)
        shutil.rmtree(checkout_path)

    def test_get_diff_files_delete(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)

        test_file_name = get_unique_name()
        content = "hello world"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write(content)
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)
        shutil.rmtree(checkout_path)

        ci_branch1 = ci_branch.Copy(get_unique_name())
        ci_branch1.RemoveFile(test_file_name, 'for test')

        diff_files = ci_branch1.GetDiffFiles(ci_branch)
        assert len(diff_files) == 1
        assert diff_files[0]['path'] == test_file_name
        assert diff_files[0]['type'] == "D"
        ci_repo.DeleteBranch(branch_name)
        ci_repo.DeleteBranch(ci_branch1.GetName())

    def test_get_diff_files_modify(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)

        test_file_name = get_unique_name()
        content = "hello world"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write(content)
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)
        shutil.rmtree(checkout_path)

        ci_branch1 = ci_branch.Copy(get_unique_name())
        checkout_path = get_default_checkout_path(ci_branch1)
        ci_branch1.CheckOut(checkout_path)
        test_file_path = os.path.join(checkout_path, test_file_name)
        content = "hello world!"
        with open(test_file_path, "w") as f:
            f.write(content)
            f.close()
        ci_branch1.Commit(checkout_path, "modify %s" % test_file_name)
        shutil.rmtree(checkout_path)

        diff_files = ci_branch1.GetDiffFiles(ci_branch)
        assert len(diff_files) == 1
        assert diff_files[0]['path'] == test_file_name
        assert diff_files[0]['type'] == "M"
        ci_repo.DeleteBranch(branch_name)
        ci_repo.DeleteBranch(ci_branch1.GetName())

    def test_rollback(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)

        commit_id = ci_branch.GetLastCommitId()

        test_file_name = get_unique_name()
        ci_branch.AddFile(test_file_name, "123", "for test")
        assert ci_branch.FileExists(test_file_name)

        ci_branch.Rollback(commit_id, 'for test')

        assert not ci_branch.FileExists(test_file_name)

        ci_repo.DeleteBranch(branch_name)

    def test_get_last_commit_info(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        test_file_name = "test.txt"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write("hello world")
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)
        shutil.rmtree(checkout_path)

        commit_id = ci_branch.GetLastCommitId()
        commit_info = ci_branch.GetLastCommitInfo()
        print(commit_info)
        assert commit_info["commit_id"] == commit_id
        assert commit_info["message"] == "add %s" % test_file_name
        ci_repo.DeleteBranch(branch_name)

    def test_get_commit_info_from_local_path(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        test_file_name = "test.txt"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write("hello world")
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)

        commit_id = ci_branch.GetLastCommitId()
        commit_info = ci_branch.GetCommitInfoOfLocalPath(checkout_path)
        print(commit_info)
        assert commit_info["commit_id"] == commit_id
        assert commit_info["message"] == "add %s" % test_file_name
        shutil.rmtree(checkout_path)
        ci_repo.DeleteBranch(branch_name)

    def test_add_branch_from_commitid(self, repo_list):
        ci_repo = repo_list[0]
        branch_name = get_unique_name()
        ci_branch = ci_repo.AddBranch(branch_name)
        checkout_path = get_default_checkout_path(ci_branch)
        ci_branch.CheckOut(checkout_path)
        test_file_name = "test.txt"
        test_file_path = os.path.join(checkout_path, test_file_name)
        with open(test_file_path, "w") as f:
            f.write("hello world")
            f.close()
        ci_branch.AddToControl(checkout_path, test_file_name)
        ci_branch.Commit(checkout_path, "add %s" % test_file_name)
        commit_id = ci_branch.GetLastCommitId()

        ci_branch.RemoveFile(test_file_name, "remove test.txt")

        ci_branch1 = ci_branch.CopyWithCommitId(get_unique_name(), commit_id, "for test")
        assert ci_branch1.FileExists(test_file_name)

        ci_repo.DeleteBranch(branch_name)
        ci_repo.DeleteBranch(ci_branch1.GetName())

    def test_path_exist(self, repo_list):
        ci_repo = repo_list[0]
        try:
            ci_branch = ci_repo.AddBranch(get_unique_name())
            ci_branch.AddFile("path/test.txt", "hello world", "add test.txt")

            assert ci_branch.FileExists("path/test.txt")
            assert ci_branch.PathExists("path")
            assert not ci_branch.PathExists("path1")
        finally:
            ci_repo.DeleteBranch(ci_branch.GetName())

    def test_file_exist(self, repo_list):
        ci_repo = repo_list[0]
        try:
            ci_branch = ci_repo.AddBranch(get_unique_name())
            ci_branch.AddFile("path/test.txt", "hello world", "add test.txt")

            assert ci_branch.FileExists("path/test.txt")
            assert not ci_branch.FileExists("path/test1.txt")
        finally:
            ci_repo.DeleteBranch(ci_branch.GetName())

    def test_duplicated_merge_request(self, repo_list):
        ci_repo = repo_list[0]
        ci_branch = ci_repo.AddBranch(get_unique_name())

        try:
            feature_branch_name = get_unique_name()
            ci_feature_branch = ci_branch.Copy(feature_branch_name)
            test_file_name1 = get_unique_name()
            ci_feature_branch.AddFile(test_file_name1, "hello world", "add test1.txt")
            ci_feature_branch.CreateMergeRequest(ci_branch, "for test", [])
            time.sleep(5)
            ci_feature_branch.AcceptMergeRequest(ci_branch, "for test 1->2", True)
            assert ci_branch.FileExists(test_file_name1)

            ci_feature_branch = ci_branch.Copy(feature_branch_name)
            test_file_name2 = get_unique_name()
            ci_feature_branch.AddFile(test_file_name2, "hello world", "add test1.txt")
            ci_feature_branch.CreateMergeRequest(ci_branch, "for test", [])
            time.sleep(5)
            ci_feature_branch.AcceptMergeRequest(ci_branch, "for test 1->2", True)
            assert ci_branch.FileExists(test_file_name2)
        finally:
            ci_repo.DeleteBranch(ci_branch.GetName())

    def test_contains_entity(self, repo_list):
        ci_repo = repo_list[0]
        try:
            ci_branch1 = ci_repo.AddBranch(get_unique_name())
            ci_branch2 = ci_repo.AddBranch(get_unique_name())
            ci_branch3 = ci_repo.AddBranch(get_unique_name())

            test_file_name1 = get_unique_name() + ".txt"
            ci_branch1.AddFile(test_file_name1, "hello world", "add test1.txt")
            test_file_name2 = get_unique_name() + ".txt"
            ci_branch2.AddFile(test_file_name2, "hello world", "add test2.txt")
            test_file_name3 = get_unique_name() + ".txt"
            ci_branch3.AddFile(test_file_name3, "hello world", "add test3.txt")

            ci_branch1.CreateMergeRequest(ci_branch2, "for test", [])
            assert not ci_branch2.ContainsEntity(ci_branch1)
            time.sleep(1)
            ci_branch1.AcceptMergeRequest(ci_branch2, "for test 1->2")
            time.sleep(1)
            assert ci_branch2.ContainsEntity(ci_branch1)

            ci_branch2.CreateMergeRequest(ci_branch3, "for test", [])
            assert not ci_branch3.ContainsEntity(ci_branch1)
            assert not ci_branch3.ContainsEntity(ci_branch2)

            time.sleep(1)
            ci_branch2.AcceptMergeRequest(ci_branch3, "for test 2->3")
            time.sleep(1)
            assert ci_branch3.ContainsEntity(ci_branch1)
            assert ci_branch3.ContainsEntity(ci_branch2)
            assert ci_branch3.FileExists(test_file_name1)

        finally:
            ci_repo.DeleteBranch(ci_branch1.GetName())
            ci_repo.DeleteBranch(ci_branch2.GetName())
            ci_repo.DeleteBranch(ci_branch3.GetName())

    def test_add_webhook(self, repo_list):
        ci_repo = repo_list[0]
        try:
            ci_branch = ci_repo.AddBranch(get_unique_name())
            ci_branch.AddWebHook("http://test.com", "1234")
            ci_branch.DeleteWebHook("http://test.com")
        finally:
            ci_repo.DeleteBranch(ci_branch.GetName())

    def test_switch_workspace(self, repo_list):
        ci_repo = repo_list[0]
        try:
            tmp_path = get_default_checkout_path(ci_repo.GetTrunk())
            ci_repo.GetTrunk().CheckOut(tmp_path)
            tmp_file_name = get_unique_name() + ".txt"
            with open(os.path.join(tmp_path, tmp_file_name), "w") as f:
                f.write("hello world")
                f.close()

            branch_name = get_unique_name()
            ci_branch = ci_repo.AddBranch(branch_name)
            test_file_name = get_unique_name() + ".txt"
            ci_branch.AddFile(test_file_name, "hello world", "add test.txt")

            ci_repo.SwitchWorkspace(tmp_path, ci_branch)

            assert os.path.exists(os.path.join(tmp_path, test_file_name))
            assert not os.path.exists(os.path.join(tmp_path, tmp_file_name))

            ci_repo.SwitchWorkspace(tmp_path, ci_repo.GetTrunk())
            assert not os.path.exists(os.path.join(tmp_path, tmp_file_name))
            assert not os.path.exists(os.path.join(tmp_path, test_file_name))

            tag_name = get_unique_name()
            ci_branch.CreateTag(tag_name, None)

            ci_repo.DeleteBranch(ci_branch.GetName()) # 测试远端分支被删除后，本地还能否正常切换

            ci_tag = ci_repo.GetTag(tag_name)
            ci_repo.SwitchWorkspace(tmp_path, ci_tag)
            assert os.path.exists(os.path.join(tmp_path, test_file_name))

        finally:
            ci_repo.DeleteBranch(ci_branch.GetName())
            shutil.rmtree(tmp_path)
















