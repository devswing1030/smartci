# -*- coding:utf-8 -*-
import base64
import os
import re
import subprocess
import time
from urllib.parse import quote
import requests


class GitUtil:
    def __init__(self, address, username, access_token) -> None:
        self.address = address
        self.username = username
        self.access_token = access_token
        self.headers = {
            'PRIVATE-TOKEN': self.access_token,
        }
        self.url = self.address + "/api/v4/projects"

    def ListProjects(self):
        per_page = 20
        page = 1
        re = []
        while True:
            url = f"{self.url}?per_page={per_page}&page={page}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(
                    f"get projects failed! url: {self.url} "
                    f"status_code: {response.status_code} reason: {response.reason}")
            projects = response.json()
            for proj in projects:
                if "default_branch" in proj: # without default_branch represents no permission
                    re.append(proj)
            if len(projects) < per_page:
                break
            page += 1
        return re

    def GetProjectUrl(self, project_id):
        url = f"{self.url}/{project_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"get project url failed! project_id: {project_id} "
                            f"status_code: {response.status_code} reason: {response.reason}")
        return response.json()["web_url"]

    def GetProjectByUrl(self, web_url):
        if web_url.endswith(".git"):
            web_url = web_url[:-4]
        projects = self.ListProjects()
        for project in projects:
            if project["web_url"] == web_url:
                return project
        return None

    def ListBranches(self, project_id, regex):
        per_page = 20
        page = 1
        result = []
        while True:
            url = f"{self.url}/{project_id}/repository/branches?regex={regex}&per_page={per_page}&page={page}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(
                    f"get branches failed! url: {url} "
                    f"status_code: {response.status_code} reason: {response.reason}")
            branches = response.json()
            result += branches
            if len(branches) < per_page:
                break
            page += 1

        # some git version not support regex query, so filter by python
        filtered_result = []
        for branch in result:
            if re.match(regex, branch["name"]) is not None:
                filtered_result.append(branch)
        return filtered_result


    def GetFileContent(self, project_id, branch_name, file_path):
        encoded_file_path = quote(file_path, safe='')
        url = f"{self.url}/{project_id}/repository/files/{encoded_file_path}/raw?ref={branch_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != requests.codes.ok:
            raise Exception(
                f"get file {file_path} failed! url: {url} "
                f"status_code: {response.status_code} reason: {response.reason}")
        return response.text


    def PathExists(self, project_id, branch_name, path):
        encoded_path = quote(path, safe='')
        url = f"{self.url}/{project_id}/repository/tree?ref={branch_name}&path={encoded_path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return len(response.json()) > 0
        if response.status_code == 404:
            return False
        raise Exception(
            f"check path {path} exists failed! url: {url} "
            f"status_code: {response.status_code} reason: {response.reason}")

    def FileExists(self, project_id, branch_name, file_path):
        encoded_path = quote(file_path, safe='')
        url = f"{self.url}/{project_id}/repository/files/{encoded_path}?ref={branch_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        if response.status_code == 404:
            return False
        raise Exception(
            f"check file {file_path} exists failed! url: {url} "
            f"status_code: {response.status_code} reason: {response.reason}")

    def AddFile(self, project_id, branch_name, file_path, content, comment):
        encoded_file_path = quote(file_path, safe='')
        url = f"{self.url}/{project_id}/repository/files/{encoded_file_path}"
        data = {
            "branch": branch_name,
            "content": content,
            "commit_message": comment
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception(
                f"add file {file_path} failed! url: {url} "
                f"status_code: {response.status_code} reason: {response.reason}")

    def RemoveFile(self, project_id, branch_name, file_path, comment):
        encoded_file_path = quote(file_path, safe='')
        url = f"{self.url}/{project_id}/repository/files/{encoded_file_path}"
        data = {
            "branch": branch_name,
            "commit_message": comment
        }
        response = requests.delete(url, headers=self.headers, json=data)
        if response.status_code != 204:
            raise Exception(
                f"remove file {file_path} failed! url: {url} "
                f"status_code: {response.status_code} reason: {response.reason}")

    def UpdateFile(self, project_id, branch_name, file_path, content, comment):
        encoded_file_path = quote(file_path, safe='')
        url = f"{self.url}/{project_id}/repository/files/{encoded_file_path}"
        data = {
            "branch": branch_name,
            "content": content,
            "commit_message": comment
        }
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(
                f"update file {file_path} failed! url: {url} "
                f"status_code: {response.status_code} reason: {response.reason}")

    '''
    .gitmodules文件内容示例：
    [submodule "lib/prod-cppf"]
        path = lib/prod-cppf
        url = http://localhost/root/prod-cppf.git
        branch = test_123
    [submodule "lib/omp"]
        path = lib/omp
        url = http://localhost/root/omp.git
    '''
    def GetSubModules(self, project_id, branch_name, local_path=None):
        if local_path is None:
            try:
                gitmodule_content = self.GetFileContent(project_id, branch_name, ".gitmodules")
            except Exception as e:
                if str(e).find("404") != -1:
                    return {}
                raise e
        else:
            if not os.path.exists(os.path.join(local_path, ".gitmodules")):
                return {}
            with open(os.path.join(local_path, ".gitmodules"), "r") as f:
                gitmodule_content = f.read()
                f.close()

        submodules = {}
        for line in gitmodule_content.split("\n"):
            if line.strip() == "":
                continue
            if line.find("[submodule") != -1:
                anchor = line.split("\"")[1]
                submodules[anchor] = {}
            else:
                key, value = line.split("=")
                submodules[anchor][key.strip()] = value.strip()
        return submodules

    def AddSubModule(self, work_dir, project_id, branch_name, ref_repo_url, ref_branch_name, mount_rel_path):
        cmd = ["git", "submodule", "add", ref_repo_url, mount_rel_path]
        self.__RunGitCmd(cmd, cwd=work_dir)
        self.Commit(work_dir, f"add submodule {mount_rel_path} from {ref_repo_url} {ref_branch_name}")
        self.UpdateSubModule(project_id, branch_name, ref_repo_url, ref_branch_name)

        """
        submodules = self.GetSubModules(project_id, branch_name)
        if mount_rel_path in submodules:
            raise Exception(f"submodule {mount_rel_path} already exists! project_id: {project_id} branch_name: {branch_name}")
        submodules[mount_rel_path] = {
            "url": ref_repo_url,
            "branch": ref_branch_name
        }
        if self.FileExists(project_id, branch_name, ".gitmodules"):
            self.UpdateFile(project_id, branch_name, ".gitmodules", self.SubModulesToString(submodules),
                            f"add submodule {mount_rel_path} from {ref_repo_url} {ref_branch_name}")
        else:
            self.AddFile(project_id, branch_name, ".gitmodules", self.SubModulesToString(submodules),
                         f"add submodule {mount_rel_path} from {ref_repo_url} {ref_branch_name}")
        """
        print(f"add submodule {mount_rel_path} from {ref_repo_url} {ref_branch_name}")

    def RemoveSubModuleByMountRelPath(self, work_dir, project_id, branch_name, mount_rel_path):
        submodules = self.GetSubModules(project_id, branch_name)
        if mount_rel_path not in submodules:
            return
        del submodules[mount_rel_path]
        with open(os.path.join(work_dir, ".gitmodules"), "w") as f:
            f.write(self.SubModulesToString(submodules))
            f.close()

        cmd = ["git", "submodule", "sync"]
        self.__RunGitCmd(cmd, cwd=work_dir)
        cmd = ["git", "submodule", "deinit", "-f", mount_rel_path]
        self.__RunGitCmd(cmd, cwd=work_dir)
        self.AddToControl(work_dir, ".gitmodules")
        cmd = ["git", "rm", "-f", mount_rel_path]
        self.__RunGitCmd(cmd, cwd=work_dir)
        cmd = ["rm", "-rf", os.path.join(work_dir, mount_rel_path)]
        self.__RunGitCmd(cmd)
        self.Commit(work_dir, f"remove submodule {mount_rel_path}")

        """
        self.UpdateFile(project_id, branch_name, ".gitmodules", self.SubModulesToString(submodules),
                        f"remove submodule {mount_rel_path}")
        """
        print(f"remove submodule {mount_rel_path}")

    def UpdateSubModule(self, project_id, branch_name, ref_repo_url, ref_branch_name):
        submodules = self.GetSubModules(project_id, branch_name)
        changed = False
        for path, submodule in submodules.items():
            if submodule["url"] == ref_repo_url:
                submodule["branch"] = ref_branch_name
                changed = True

        if not changed:
            return

        self.UpdateFile(project_id, branch_name, ".gitmodules", self.SubModulesToString(submodules),
                        f"update submodule to {ref_repo_url} {ref_branch_name}")
        print(f"update submodule to {ref_repo_url} {ref_branch_name}")

    @staticmethod
    def SubModulesToString(submodules):
        gitmodule_content = ""
        for path, submodule in submodules.items():
            gitmodule_content += f"[submodule \"{path}\"]\n"
            gitmodule_content += f"path = {path}\n"
            gitmodule_content += f"url = {submodule['url']}\n"
            if "branch" in submodule:
                gitmodule_content += f"branch = {submodule['branch']}\n"
            gitmodule_content += "\n"
        return gitmodule_content

    def AddBranch(self, project_id, branch_name, ref):
        url = f"{self.url}/{project_id}/repository/branches"
        data = {
            "branch": branch_name,
            "ref": ref
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception("add branch failed! url: " + url + " reason: " + response.reason)

        time.sleep(1)
        while not self.BranchExists(project_id, branch_name):
            time.sleep(1)

    def AddTag(self, project_id, tag_name, commit_id):
        url = f"{self.url}/{project_id}/repository/tags"
        data = {
            "tag_name": tag_name,
            "ref": commit_id
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception("add tag failed! url: " + url + " reason: " + response.reason)

        time.sleep(1)
        while not self.TagExists(project_id, tag_name):
            time.sleep(1)

    def GetLastCommitIdOfBranch(self, project_id, branch_name):
        return self.GetLastCommitInfoOfBranch(project_id, branch_name)["commit_id"]

    def GetLastCommitInfoOfBranch(self, project_id, branch_name):
        url = f"{self.url}/{project_id}/repository/commits?ref_name={branch_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("get last commit id failed! url: " + url + " reason: " + response.reason)
        info = {}
        info["commit_id"] = response.json()[0]["id"]
        info["author"] = response.json()[0]["committer_email"].split("@")[0]
        info["date"] = response.json()[0]["created_at"]
        info["message"] = response.json()[0]["message"].strip()
        return info

    def GetCommitIdOfLocalPath(self, local_path):
        return self.GetCommitInfoOfLocalPath(local_path)["commit_id"]

    def GetCommitInfoOfLocalPath(self, local_path):
        cmd = ["git", "log", "-1", "--pretty=format:%H %an %ad %ae", "--date=iso"]
        output = self.__RunGitCmd(cmd, cwd=local_path)
        parts = output.split(" ")
        info = {"commit_id": parts[0], "date": parts[2] + " " + parts[3] + " " + parts[4]}
        email = parts[5]
        info["author"] = email.split("@")[0]

        cmd = ["git", "log", "-1", "--pretty=%B"]
        output = self.__RunGitCmd(cmd, cwd=local_path)
        info["message"] = output.strip()
        return info




    def BranchExists(self, project_id, branch_name):
        url = f"{self.url}/{project_id}/repository/branches/{branch_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False

    def TagExists(self, project_id, tag_name):
        url = f"{self.url}/{project_id}/repository/tags/{tag_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True
        return False

    def GetBranchUrl(self, project_id, branch_name):
        url = f"{self.url}/{project_id}/repository/branches/{branch_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("get branch url failed! url: " + url + " reason: " + response.reason)
        return response.json()["web_url"]

    def GetTagUrl(self, project_id, tag_name):
        url = f"{self.url}/{project_id}/repository/tags/{tag_name}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("get tag url failed! url: " + url + " reason: " + response.reason)
        return response.json()["web_url"]

    def CheckOut(self, local_path, clone_url, branch_name):
        tmp_path = os.path.join(local_path, ".git")
        if os.path.exists(tmp_path):
            cmd = ["git", "status"]
            output = self.__RunGitCmd(cmd, cwd=local_path)
            if output.find(branch_name) != -1:
                cmd = ["git", "pull"]
                self.__RunGitCmd(cmd, cwd=local_path)
                cmd = ["git", "submodule", "update", "--init", "--recursive"]
                self.__RunGitCmd(cmd, cwd=local_path)
                return
            else:
                raise Exception(f"local path {local_path} is not empty!")

        tmp_clone_url = clone_url.replace("://", f"://{self.username}:{self.access_token}@")

        cmd = ["git", "clone", "--single-branch", "-b", branch_name, tmp_clone_url, local_path]
        self.__RunGitCmd(cmd)
        cmd = ["git", "submodule", "update", "--init", "--recursive"]
        self.__RunGitCmd(cmd, cwd=local_path)
        cmd = ["git", "submodule", "update", "--init", "--remote"]
        self.__RunGitCmd(cmd, cwd=local_path)

    def CheckOutDirectory(self, local_path, clone_url, branch_name, rel_path):
        tmp_clone_url = clone_url.replace("://", f"://{self.username}:{self.access_token}@")
        cmd = ["git", "clone", "--no-checkout", tmp_clone_url, local_path]
        self.__RunGitCmd(cmd)
        cmd = ["git", "config", "core.sparseCheckout", "true"]
        self.__RunGitCmd(cmd, cwd=local_path)
        with open(os.path.join(local_path, ".git/info/sparse-checkout"), "w") as f:
            f.write(f"{rel_path}/*")
            f.close()
        cmd = ["git", "checkout", branch_name]
        self.__RunGitCmd(cmd, cwd=local_path)

    def CheckOutFile(self, local_path, clone_url, branch_name, file_rel_path):
        tmp_clone_url = clone_url.replace("://", f"://{self.username}:{self.access_token}@")
        cmd = ["git", "clone", "--no-checkout", tmp_clone_url, local_path]
        self.__RunGitCmd(cmd)
        cmd = ["git", "config", "core.sparseCheckout", "true"]
        self.__RunGitCmd(cmd, cwd=local_path)
        with open(os.path.join(local_path, ".git/info/sparse-checkout"), "w") as f:
            f.write(f"{file_rel_path}")
            f.close()
        cmd = ["git", "checkout", branch_name]
        self.__RunGitCmd(cmd, cwd=local_path)

    @staticmethod
    def AddToControl(local_path, target_path):
        cmd = ["git", "add", target_path]
        subprocess.check_output(cmd, cwd=local_path)

    @staticmethod
    def Commit(local_path, comment):
        cmd = ["git", "commit", "-a", "-m", comment]
        subprocess.check_output(cmd, cwd=local_path)
        cmd = ["git", "push"]
        subprocess.check_output(cmd, cwd=local_path)

    def GetBranchProtectedInfo(self, project_id, branch_name):
        per_page = 20
        page = 1
        while True:
            url = f"{self.url}/{project_id}/protected_branches?per_page={per_page}&page={page}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception("get protected branch failed! url: " + url + " reason: " + response.reason)
            for item in response.json():
                if item["name"] == branch_name:
                    return {"allowed_merge": item["merge_access_levels"][0]["access_level"] == 30,
                            "allowed_push": item["push_access_levels"][0]["access_level"] == 30
                            }
            if len(response.json()) < per_page:
                break
            page += 1
        return None

    def SetBranchProtected(self, project_id, branch_name, allowed_merge, allowed_push):
        url = f"{self.url}/{project_id}/protected_branches"

        # 40 表示 Maintainer 角色
        # 30 表示 Developer 角色
        push_access_level = 30 if allowed_push else 40
        merge_access_level = 30 if allowed_merge else 40

        if self.GetBranchProtectedInfo(project_id, branch_name) is not None:
            response = requests.delete(url + "/" + branch_name, headers=self.headers)
            if response.status_code != 204:
                raise Exception("delete protected branch failed! url: " + url + " reason: " + response.reason)
        data = {
            "name": branch_name,
            "push_access_level": push_access_level,
            "merge_access_level": merge_access_level
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception("add protected branch failed! url: " + url + " reason: " + response.reason)

    def DeleteBranch(self, project_id, branch_name):
        url = f"{self.url}/{project_id}/repository/branches/{branch_name}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code != 204 and response.status_code != 404:
            raise Exception("delete branch failed! url: " + url + " reason: " + response.reason)

    def DeleteTag(self, project_id, tag_name):
        url = f"{self.url}/{project_id}/repository/tags/{tag_name}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code != 204 and response.status_code != 404:
            raise Exception("delete tag failed! url: " + url + " reason: " + response.reason)

    def GetDiffFiles(self, project_id, from_branch, to_branch):
        files = []
        url = f"{self.url}/{project_id}/repository/compare?from={from_branch}&to={to_branch}&straight=true"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("compare branch failed! url: " + url + " reason: " + response.reason)
        return response.json()["diffs"]

    def GetUrlAndBranchOfLocalPath(self, local_path):
        if not os.path.exists(os.path.join(local_path, ".git")):
            return None
        cmd = ["git", "remote", "get-url", "origin"]
        remote_url = self.__RunGitCmd(cmd, cwd=local_path).strip()
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        remote_url = remote_url.replace(f"{self.username}:{self.access_token}@", "")
        cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        branch_name = self.__RunGitCmd(cmd, cwd=local_path)
        return {"url": remote_url, "branch": branch_name.strip()}

    def GetBranchDiffCommit(self, project_id, from_branch, to_branch):
        url = f"{self.url}/{project_id}/repository/compare?from={from_branch}&to={to_branch}&straight=true"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("compare branch failed! url: " + url + " reason: " + response.reason)
        return response.json()["diffs"]

    def GetMergeRequest(self, project_id, source_branch, target_branch):
        url = f"{self.url}/{project_id}/merge_requests?source_branch={source_branch}&target_branch={target_branch}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == requests.codes.not_found:
            return None
        if response.status_code != requests.codes.ok:
            raise Exception("get merge request failed! url: " + url + " reason: " + response.reason)

        if len(response.json()) == 0:
            return None

        mrs = response.json()
        found_mr = None
        for mr in mrs:
            if mr["state"] == "opened":
                found_mr = mr
                break
        if found_mr is None:
            return None

        re = {"mr": found_mr}

        iid = found_mr["iid"]
        url = f"{self.url}/{project_id}/merge_requests/{iid}/approvals"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("get merge request failed! url: " + url + " reason: " + response.reason)
        re["approvals"] = response.json()

        return re

    def GetMergeRequestWebUrl(self, project_id, source_branch, target_branch):
        mr_info = self.GetMergeRequest(project_id, source_branch, target_branch)
        if mr_info is None:
            return None
        return mr_info["mr"]["web_url"]


    def AcceptMergeRequest(self, project_id, source_branch, target_branch, comment, remove_source_branch=False):
        mr_info = self.GetMergeRequest(project_id, source_branch, target_branch)
        iid = mr_info["mr"]["iid"]
        url = f"{self.url}/{project_id}/merge_requests/{iid}/merge"
        data = {
            "should_remove_source_branch": remove_source_branch,
            "merge_commit_message": comment,
            "squash": False
        }
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception("execute merge request failed! url: " + url + " reason: " + response.reason)

    def CreateMergeRequest(self, project_id, source_branch, target_branch, title, description):
        url = f"{self.url}/{project_id}/merge_requests"
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception("create merge request failed! url: " + url + " reason: " + response.reason)

    def Rollback(self,local_path, commit_id):
        cmd = ["git", "reset", "--hard", commit_id]
        self.__RunGitCmd(cmd, cwd=local_path)
        cmd = ["git", "push", "-f"]
        self.__RunGitCmd(cmd, cwd=local_path)

    def ContainsEntity(self, project_id, target_entity, source_entity):
        source_last_commit_info = self.GetLastCommitInfoOfBranch(project_id, source_entity)
        source_last_commit_id = source_last_commit_info["commit_id"]
        target_last_commit_id = self.GetLastCommitIdOfBranch(project_id, target_entity)
        print(f"source_last_commit_id: {source_last_commit_id}, target_last_commit_id: {target_last_commit_id}")
        url = f"{self.url}/{project_id}/repository/commits"
        params = {
            'ref_name': target_entity,
            'since': source_last_commit_info['date']
        }
        per_page = 100
        page = 1
        while True:
            response = requests.get(f"{url}?per_page={per_page}&page={page}", headers=self.headers, params=params)
            #print(response.json())
            #GitUtil.__PrintJson(response.json())
            if response.status_code != requests.codes.ok:
                raise Exception("check contains entity failed! url: " + url + " reason: " + response.reason)
            commits = response.json()
            for commit in commits:
                if commit["id"] == source_last_commit_id:
                    return True
            if len(commits) < per_page:
                break
            page = page + 1
        return False

    def AddWebHook(self, project_id, branch_name, webhook_url, secret_token):
        url = f"{self.url}/{project_id}/hooks"
        data = {
            "url": webhook_url,
            "push_events": True,
            "push_events_branch_filter": branch_name,
            "token": secret_token,
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            raise Exception("add web hook failed! url: " + url + "reason: " + response.reason)

    def GetWebHook(self, project_id, webhook_url):
        url = f"{self.url}/{project_id}/hooks"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("get web hook failed! url: " + url + "reason: " + response.reason)
        hooks = response.json()
        for hook in hooks:
            if hook["url"] == webhook_url:
                return hook
        return None

    def DeleteWebHook(self, project_id, webhook_url):
        hook = self.GetWebHook(project_id, webhook_url)
        if hook is None:
            return
        webhook_id = hook["id"]
        url = f"{self.url}/{project_id}/hooks/{webhook_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code != 204:
            raise Exception("delete web hook failed! url: " + url + "reason: " + response.reason)

    def RevertWorkspace(self, local_path):
        cmd = ["git", "clean", "-fd"]
        self.__RunGitCmd(cmd, cwd=local_path)
        cmd = ["git", "reset", "--hard"]
        self.__RunGitCmd(cmd, cwd=local_path)
        cmd = ["git", "pull"]
        self.__RunGitCmd(cmd, cwd=local_path)

    def SwitchWorkspace(self, local_path, branch_name, type):
        self.RevertWorkspace(local_path)
        cmd = ["git", "branch", '--format=%(refname:short)']
        output = self.__RunGitCmd(cmd, cwd=local_path)
        local_branches = output.split("\n")
        if branch_name in local_branches:
            cmd = ["git", "checkout", branch_name]
            self.__RunGitCmd(cmd, cwd=local_path)
        else:
            cmd = ["git", "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"]
            self.__RunGitCmd(cmd, cwd=local_path)
            if type == "tag":
                cmd = ["git", "fetch", "--tag"]
                self.__RunGitCmd(cmd, cwd=local_path)
                cmd = ["git", "checkout", branch_name]
                self.__RunGitCmd(cmd, cwd=local_path)
            else:
                cmd = ["git", "fetch", "origin"]
                self.__RunGitCmd(cmd, cwd=local_path)
                cmd = ["git", "checkout", "-b", branch_name, f"origin/{branch_name}"]
                self.__RunGitCmd(cmd, cwd=local_path)

    @staticmethod
    def __PrintJson(json_str):
        import json
        print(json.dumps(json_str, indent=4, ensure_ascii=False))

    def __RunGitCmd(self, cmd, **kwargs):
        tmp_args = {}
        tmp_args["stderr"] = subprocess.STDOUT
        if "disable_stderr" in kwargs and kwargs["disable_stderr"]:
            tmp_args["stderr"] = subprocess.DEVNULL
        if "cwd" in kwargs:
            tmp_args["cwd"] = kwargs["cwd"]
        err_info = None
        try:
            output = subprocess.check_output(cmd, **tmp_args).decode("utf-8")
            return output
        except subprocess.CalledProcessError as e:
            err_info = e.output.decode("utf-8")
            if self.access_token is not None:
                err_info = err_info.replace(self.access_token, "******")
        if err_info is not None:
            raise Exception(err_info)
