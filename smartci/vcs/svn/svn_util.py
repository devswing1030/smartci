import os.path
import shutil
import subprocess

import xml.etree.ElementTree as ET


class SvnUtil:
    def __init__(self, address, username, password):
        self.address = address
        self.username = username
        self.password = password

    def GetAbsolutePath(self, rel_path):
        return self.address + "/" + rel_path

    def GetFileContent(self, file_path):
        cmd = ["svn", "cat", self.address + "/" + file_path]
        return self.__RunSvnCmd(cmd)

    def ListEntryOfDir(self, rel_path):
        entrys = []
        cmd = ["svn", "list", self.address + "/" + rel_path]
        output = self.__RunSvnCmd(cmd)
        for line in output.split("\n"):
            if line.strip() == "":
                continue
            entry = {}
            entry["name"] = line[:-1]
            entry["is_directory"] = line[-1] == "/"
            entrys.append(entry)

        return entrys

    def PathExists(self, path):
        try:
            cmd = ["svn", "info", self.address + "/" + path]
            self.__RunSvnCmd(cmd, disable_stderr=True)
            return True
        except:
            return False

    def _GetCommitMessage(self, path, revision):
        cmd = ["svn", "log", path, "-r", revision, "--xml"]
        output = self.__RunSvnCmd(cmd)
        root = ET.fromstring(output)
        message = root.find('logentry').find('msg').text
        # 删除首尾的引号和换行符
        message = message.strip()
        if message[0] == '"' and message[-1] == '"':
            message = message[1:-1]
        return message

    def _GetRevisionInfoFromXml(self, xml):
        root = ET.fromstring(xml)
        info = {}
        info["commit_id"] = root.find('entry').find('commit').get('revision')
        info["author"] = root.find('entry').find('commit').find('author').text
        info["date"] = root.find('entry').find('commit').find('date').text
        return info

    def GetLastRevision(self, rel_path):
        return self.GetLastRevisionInfo(rel_path)["commit_id"]

    def GetLastRevisionInfo(self, rel_path):
        cmd = ["svn", "info", self.address + "/" + rel_path, "--xml"]
        output = self.__RunSvnCmd(cmd)
        info = self._GetRevisionInfoFromXml(output)
        info["message"] = self._GetCommitMessage(self.address + "/" + rel_path, info["commit_id"])
        return info

    def GetRevisionOfLocalPath(self, local_path):
        return self.GetRevisionInfoOfLocalPath(local_path)["commit_id"]

    def GetRevisionInfoOfLocalPath(self, local_path):
        cmd = ["svn", "up"]
        self.__RunSvnCmd(cmd, cwd=local_path)
        cmd = ["svn", "info", "--xml"]
        output = self.__RunSvnCmd(cmd, cwd=local_path)
        info = self._GetRevisionInfoFromXml(output)
        info["message"] = self._GetCommitMessage(local_path, info["commit_id"])
        return info

    def GetUrlFromLocalPath(self, local_path):
        if not os.path.exists(os.path.join(local_path, ".svn")):
            return None
        cmd = ["svn", "info", "--xml"]
        output = self.__RunSvnCmd(cmd, cwd=local_path)
        root = ET.fromstring(output)
        url = root.find('entry').find('url').text
        return url

    def Copy(self, src, dest, comment, revision=None):
        cmd = ["svn", "copy", self.address + "/" + src, self.address + "/" + dest, "-m", f'"{comment}"']
        if revision is not None:
            cmd.append("-r")
            cmd.append(revision)
        self.__RunSvnCmd(cmd)

    def CheckOut(self, rel_path, local_path):
        try:
            if os.path.exists(os.path.join(local_path, ".svn")):
                cmd = ["svn", "info"]
                output = self.__RunSvnCmd(cmd, cwd=local_path)
                if output.find(self.address + "/" + rel_path) >= 0:
                    cmd = ["svn", "up", local_path]
                    self.__RunSvnCmd(cmd)
                    return
        except:
            pass
        cmd = ["svn", "co", self.address + "/" + rel_path, local_path]
        self.__RunSvnCmd(cmd)

    def CheckOutDirectory(self, rel_path, local_path):
        cmd = ["svn", "co", self.address + "/" + rel_path]
        self.__RunSvnCmd(cmd, cwd=local_path)

    def AddToControl(self, local_path, target_rel_path):
        path = os.path.join(local_path, target_rel_path)
        cmd = ["svn", "add", "--force", "--parents", path]
        self.__RunSvnCmd(cmd)

    def Commit(self, local_path, comment):
        cmd = ["svn", "commit", local_path, "-m", f'"{comment}"']
        self.__RunSvnCmd(cmd)
        print("commit " + local_path + " done")

    def AddFile(self, local_path, file_rel_path, content, comment):
        # Get the file rel dir
        file_rel_dir = os.path.dirname(file_rel_path)
        filename = os.path.basename(file_rel_path)

        tmp_rel_dir = file_rel_dir
        while not self.PathExists(tmp_rel_dir):
            tmp_rel_dir = os.path.dirname(tmp_rel_dir)
            if tmp_rel_dir == "":
                break

        cmd = ["svn", "checkout", self.address + "/" + tmp_rel_dir, "--depth", "empty", local_path]
        self.__RunSvnCmd(cmd)

        file_rel_dir = file_rel_dir[len(tmp_rel_dir) + 1:]
        os.makedirs(os.path.join(local_path, file_rel_dir), exist_ok=True)

        file_path = os.path.join(local_path, file_rel_dir, filename)
        with open(file_path, "w") as f:
            f.write(content)
            f.close()

        print(f"add file {file_path} to svn")

        self.AddToControl(local_path, file_path)
        self.Commit(local_path, comment)

    def Remove(self, file_rel_path, comment):
        cmd = ["svn", "delete", self.address + "/" + file_rel_path, "-m", f'"{comment}"']
        self.__RunSvnCmd(cmd)


    def GetExternalsPath(self, rel_path):
        externals = []
        re = self.GetExternals(rel_path)
        for anchor, rel_paths in re.items():
            for rel_path in rel_paths:
                externals.append(rel_path["abs"])
        return externals

    def GetExternals(self, rel_path, local_path=None):
        try:
            if local_path is not None:
                cmd = ["svn", "propget", "svn:externals", "-R", "--xml"]
                output = self.__RunSvnCmd(cmd, cwd=local_path)
            else:
                cmd = ["svn", "propget", "svn:externals", self.address + "/" + rel_path, "-R", "--xml"]
                output = self.__RunSvnCmd(cmd)
            re = self.__ParseExternalsXml(output, rel_path, local_path)
            return re
        except subprocess.CalledProcessError as e:
            return {}

    def SaveExternals(self, local_path, rel_path, path_to_save_ref, externals):
        shutil.rmtree(local_path)
        os.makedirs(local_path)
        external_info = []
        for external in externals:
            external_info.append("/" + external["abs"] + " " + external["mount_rel_path"])
        external_str = "\n".join(external_info)

        if self.PathExists(f"{rel_path}/{path_to_save_ref}"):
            cmd = ["svn", "checkout", "-N", "--ignore-externals", self.address + "/" + rel_path + "/" + path_to_save_ref, local_path]
            self.__RunSvnCmd(cmd)
            cmd = ["svn", "propset", "svn:externals", external_str, local_path]
            self.__RunSvnCmd(cmd)
        else:
            cmd = ["svn", "checkout", "-N", "--ignore-externals", self.address + "/" + rel_path, local_path]
            self.__RunSvnCmd(cmd)
            os.makedirs(os.path.join(local_path, path_to_save_ref))
            self.AddToControl(local_path, path_to_save_ref)
            cmd = ["svn", "propset", "svn:externals", external_str, local_path]
            self.__RunSvnCmd(cmd)
        self.Commit(local_path, f"add external  to {path_to_save_ref}")

    def AddExternal(self, local_path, rel_path, external_rel_path, mount_rel_path, path_to_save_ref):
        re = self.GetExternals(rel_path)
        if path_to_save_ref is None:
            path_to_save_ref = ""  # 默认保存在根目录
        externals = None
        if path_to_save_ref in re:
            externals = re[path_to_save_ref]
            externals.append({"abs": external_rel_path, "mount_rel_path": mount_rel_path})
        else:
            externals = [{"abs": external_rel_path, "mount_rel_path": mount_rel_path}]

        self.SaveExternals(local_path, rel_path, path_to_save_ref, externals)

    def RemoveExternalByMountRelPath(self, local_path, rel_path, mount_rel_path):
        re = self.GetExternals(rel_path)
        for path_to_save_ref, externals in re.items():
            i = 0
            for external in externals:
                if external["mount_rel_path"] == mount_rel_path:
                    del externals[i]
                    self.SaveExternals(local_path, rel_path, path_to_save_ref, externals)
                    break
                i += 1

    def UpdateExternal(self, local_path, rel_path, external_repo_rel_path, external_entity_rel_path):
        re = self.GetExternals(rel_path)
        for path_to_save_ref, externals in re.items():
            changed = False
            for external in externals:
                if external["abs"].find(external_repo_rel_path) == 0 and external["abs"] != external_entity_rel_path:
                    external["abs"] = external_entity_rel_path
                    changed = True
            if changed:
                self.SaveExternals(local_path, rel_path, path_to_save_ref, externals)

    def GetBranchDiffRevision(self, branch1_rel_path, branch2_rel_path):
        cmd = ["svn", "mergeinfo", "--show-revs", "eligible", self.address + "/" + branch1_rel_path, self.address + "/" + branch2_rel_path]
        output = self.__RunSvnCmd(cmd)
        return output.strip()

    def MergeTo(self, src_rel_path, dest_rel_path, comment, local_path):
        self.CheckOut(dest_rel_path, local_path)
        cmd = ["svn", "merge", self.address + "/" + src_rel_path]
        self.__RunSvnCmd(cmd, cwd=local_path)
        self.Commit(local_path, comment)

    def HasConflict(self, src_rel_path, dest_rel_path, local_path):
        self.CheckOut(dest_rel_path, local_path)
        cmd = ["svn", "merge", "--dry-run", self.address + "/" + src_rel_path]
        output = self.__RunSvnCmd(cmd, cwd=local_path)
        print(output)
        if output.find("conflict") >= 0:
            return True
        else:
            return False

    '''
    <?xml version="1.0" encoding="UTF-8"?>
    <diff>
    <paths>
    <path
       item="added"
       props="none"
       kind="file">http://10.211.55.2:8199/svn/Test/stsv5/biz/trunk/20240624212719030122/test.txt</path>
    <path
       item="added"
       props="none"
       kind="dir">http://10.211.55.2:8199/svn/Test/stsv5/biz/trunk/20240624212719030122</path>
    </paths>
    </diff>
    '''
    def GetDiffFiles(self, from_rel_path, to_rel_path):
        cmd = ["svn", "diff", self.address + "/" + from_rel_path, self.address + "/" + to_rel_path,
               "--summarize", "--xml", "--ignore-properties"]
        diffs = []
        output = self.__RunSvnCmd(cmd)
        root = ET.fromstring(output)
        for path in root.find('paths'):
            diff = {}
            kind = path.get('kind')
            if kind != "file":
                continue
            item = path.get('item')
            if item == "added":
                diff['type'] = "A"
            elif item == "deleted":
                diff['type'] = "D"
            elif item == "modified":
                diff['type'] = "M"
            else:
                raise Exception(f"invalid diff item {item}")
            diff['path'] = path.text[len(self.address)+1:]
            diffs.append(diff)
        return diffs

    def Rollback(self, rel_path, revision, comment, local_path):
        self.CheckOut(rel_path, local_path)
        cmd = ["svn", "merge", "-r", "HEAD:" + revision, "."]
        self.__RunSvnCmd(cmd, cwd=local_path)
        self.Commit(local_path, comment)

    def RevertWorkspace(self, local_path):
        try:
            cmd = ["svn", "revert", "-R", local_path]
            self.__RunSvnCmd(cmd)
            cmd = ["svn", "update", "--force", local_path]
            self.__RunSvnCmd(cmd)
        except:
            pass  # ignore the exception, because the workspace may not exist in server
        cmd = ["svn", "cleanup", local_path]
        self.__RunSvnCmd(cmd)
        cmd = "svn status | grep '?' | awk '{print $2}' | xargs rm -rf"
        subprocess.run(cmd, shell=True, cwd=local_path)

    def SwitchWorkspace(self, local_path, branch_rel_path):
        self.RevertWorkspace(local_path)
        cmd = ["svn", "switch", self.address + "/" + branch_rel_path, local_path]
        self.__RunSvnCmd(cmd)

    '''
    <?xml version="1.0" encoding="UTF-8"?>
    <properties>
    <target
       path="svn://localhost/Test/stsv5/biz/trunk">
    <property
       name="svn:externals">/Test/stsv5/cppf/trunk lib/cppf
    /Test/stsv5/comm/trunk lib/comm
    </property>
    </target>
    </properties>
    '''

    def __ParseExternalsXml(self, xml, branch_rel_path, local_path=None):
        externals = {}

        branch_root = branch_rel_path.split("/")[0]
        if local_path is None:
            branch_abs_path = self.address + '/' + branch_rel_path
        else:
            branch_abs_path = local_path

        root = ET.fromstring(xml)
        for target in root.findall('target'):
            path = target.get('path')
            anchor_dir = path[len(branch_abs_path)+1: ]
            externals[anchor_dir] = []
            for property in target.findall('property'):
                name = property.get('name')
                if name == "svn:externals":
                    value = property.text
                    for line in value.split("\n"):
                        if line.strip() == "":
                            continue
                        external = line.split(" ")[0]
                        abs_external = None
                        if external[0] == "^":
                            abs_external = branch_root + external[1:]
                        elif external[0] == "/":
                            abs_external = external[1:]
                        else:
                            raise Exception(f"invalid external {external}")
                        data = {"origin": external, "abs": abs_external, "mount_rel_path": line.split(" ")[1]}
                        externals[anchor_dir].append(data)
        return externals

    def __RunSvnCmd(self, cmd, **kwargs):
        if self.username is not None and self.password is not None:
            cmd += ["--username", self.username, "--password", self.password, "--no-auth-cache"]
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
            if self.password is not None:
                err_info = err_info.replace(self.password, "******")
        if err_info is not None:
            raise Exception(err_info)
