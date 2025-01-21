import json
import os

import yaml

from smartci.ci_branch import CiBranch, CiVersionEntity, CiTag, CiTrunk
from smartci.ci_repo import CiRepo

class CiVcs:
    """
    This class represents a Continuous Integration (CI) version control system (VCS).
    """

    def __init__(self, vcs_list):
        """
        Initializes a new instance of the CiVcs class.

        :param vcs_list: The list of version control systems this CI VCS belongs to.
        """
        self.vcs_list = vcs_list

    def GetAllRepo(self):
        """
        Retrieves all application repositories.

        :return: A list of all application repositories.
        """
        return self.GetAllRepoWithBranch(None)

    def GetAllRepoWithBranch(self, branch_name):
        """
        Retrieves all application repositories which has branch with the given branch name.

        :param branch_name: The name of the branch to retrieve the repositories for, or None to retrieve all application repositories.
        :return: A list of all application repositories which has branch with the given branch name.
        """
        result = []
        for vcs in self.vcs_list:
            re = self.GetAllRepoWithBranchInSingleVcs(vcs, branch_name)
            result.extend(re)
        return result

    def GetAllRepoInSingleVcs(self, primitive_vcs):
        """
        Retrieves all application repositories in a single VCS.

        :param primitive_vcs: The primitive VCS to retrieve the repositories from.
        :return: A list of all application repositories in the given VCS.
        """
        return self.GetAllRepoWithBranchInSingleVcs(primitive_vcs, None)

    def GetAllRepoWithBranchInSingleVcs(self, primitive_vcs, branch_name):
        """
        Retrieves all application repositories in a single VCS which has branch with the given branch name.

        :param primitive_vcs: The primitive VCS to retrieve the repositories from.
        :param branch_name: The name of the branch to retrieve the repositories for, or None to retrieve all application repositories.
        :return: A list of all application repositories in the given VCS which has branch with the given branch name.
        """
        result = []
        primitive_repos = primitive_vcs.GetRepos()
        for primitive_repo in primitive_repos:
            if not CiRepo.SupportCi(primitive_repo):
                continue
            ci_repo = CiRepo(self, primitive_repo)
            if branch_name is not None:
                if ci_repo.GetBranch(branch_name) is not None:
                    result.append(ci_repo)
            else:
                result.append(ci_repo)
        return result

    def GetRepo(self, group, name):
        """
        Retrieves the application repository with the given group and name.

        :param group: The group of the repository to retrieve.
        :param name: The name of the repository to retrieve.
        :return: The application repository with the given group and name, or None if no such repository exists.
        """
        cache_file = os.path.join(os.getenv("CI_WORKSPACE"), "ci_repo_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf8") as f:
                cache = json.load(f)
                if group in cache and name in cache[group]:
                    try:
                        url = cache[group][name]
                        return self.GetCiRepoByUrl(url)
                    except:
                        pass
            f.close()

        ci_repos = self.GetAllRepo()
        cache = {}
        re = None
        for ci_repo in ci_repos:
            if ci_repo.GetGroup() not in cache:
                cache[ci_repo.GetGroup()] = {}
            cache[ci_repo.GetGroup()][ci_repo.GetName()] = ci_repo.GetUrl()

            if ci_repo.GetGroup() == group and ci_repo.GetName() == name:
                re = ci_repo
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        return re

    def GetCiRepoByUrl(self, url):
        for vcs in self.vcs_list:
            primitive_repo = vcs.GetRepoByUrl(url)
            if primitive_repo is not None:
                return CiRepo(self, primitive_repo)
        return None

    def GetCiRepoById(self, id):
        """
        Retrieves the application repository with the given id.

        :param id: The id of the repository to retrieve.
        :return: The application repository with the given id, or None if no such repository exists.
        """
        group = CiRepo.GetGroupFromId(id)
        name = CiRepo.GetNameFromId(id)
        return self.GetRepo(group, name)


    def CreateCiRepo(self, primitive_repo):
        """
        Creates a new CiRepo object.

        :param primitive_repo: The primitive repository to base the new CiRepo object on.
        :return: The new CiRepo object.
        """
        return CiRepo(self, primitive_repo)

    def GetVersionEntityFromLocalPath(self, local_path):
        """
        Returns the version entity of the given local path.

        :param local_path: The local path to get the version entity from.
        :return: The version entity of the given local path.
        """
        for vcs in self.vcs_list:
            primitive_entity = vcs.GetVersionEntityFromLocalPath(local_path)
            if primitive_entity is not None:
                ci_repo = CiRepo(self, primitive_entity.repo)
                if primitive_entity.GetType() == "branch":
                    ci_entity = CiBranch(ci_repo, primitive_entity)
                elif primitive_entity.GetType() == "tag":
                    ci_entity = CiTag(ci_repo, primitive_entity)
                elif primitive_entity.GetType() == "trunk":
                    ci_entity = CiTrunk(ci_repo, primitive_entity)
                else:
                    raise Exception("invalid version entity type " + primitive_entity.GetType())
                return ci_entity
        return None

    @staticmethod
    def Create(cfg_str=None):
        """
        Creates a new CiVcs object based on the configuration in the "ci_vcs_cfg.yml" file.

        :return: The new CiVcs object.
        """
        if cfg_str is None:
            yaml_cfg_file = os.path.join(os.getenv("CI_WORKSPACE"), "ci_vcs_cfg.yml")
            f = open(yaml_cfg_file, "r")
            cfgs = yaml.safe_load(f)
            f.close()
        else:
            cfgs = yaml.safe_load(cfg_str)

        vcs_list = []
        from smartci.util import encrypt
        for cfg in cfgs["vcs"]:
            if cfg["type"] == "svn":
                from smartci.vcs.svn.svn_vcs import Svn
                username = None
                if "username" in cfg:
                    username = cfg["username"]
                password = None
                if "password" in cfg:
                    password = cfg["password"]
                    if "secret" in cfg:
                        password = encrypt.XorDecrypt(password, cfg["secret"])
                vcs = Svn(cfg["url"], username, password, cfg["repository"])
                vcs_list.append(vcs)
            elif cfg["type"] == "git":
                from smartci.vcs.git.git_vcs import Git
                access_token = cfg["access_token"]
                if "secret" in cfg:
                    access_token = encrypt.XorDecrypt(access_token, cfg["secret"])
                vcs = Git(cfg["url"], cfg["username"], access_token)
                vcs_list.append(vcs)
            else:
                pass
        return CiVcs(vcs_list)
