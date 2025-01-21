
# SmartCI

This is a tool library designed to support Continuous Integration (CI). Currently, it supports the following functionalities:

- Accessing version control systems (VCS).

## Installation

1. After downloading the source code, navigate to the root directory and execute the following command to install:

    ```bash
    python setup.py install
    ```

2. Create a working directory for the tool library and set the environment variable `CI_WORKSPACE` to point to this directory. The working directory is used to store configuration files required for various functions and temporary files generated during continuous integration.

## Version Control System (VCS) Access

The tool library abstracts operations on version control systems, providing a unified interface. Users can access VCS by calling the interface. Currently, supported VCS include GitLab and SVN.

To enable VCS access, create a configuration file `ci_vcs_cfg.yml` in the working directory and include VCS configuration details in the file. The configuration file format is as follows:

```yml
vcs:
    - type: svn
      url: svn://localhost
      username: test   # optional
      password: abc    # optional
      repository:
          - Test
          - product_source
    - type: git
      url: http://127.0.0.1:8890
      access_token: test-token
```

The tool library primarily provides access to application repositories. An application repository refers to a repository that stores application source code. For GitLab, this corresponds to a project; for SVN, this is a path configured with branch management strategies. The tool treats paths on SVN servers containing a "trunk" subdirectory as application repositories. All application repositories configured on VCS can be managed uniformly, allowing users to access them via a unified interface without needing to concern themselves with the specifics of the underlying VCS.

To enable access via the tool library, each application repository must create a `.ci` folder in the root directory of its main branch and include a `settings.yml` file in that folder. This file contains the application repository's configuration details. Only repositories with this configuration file can be accessed via the tool library; those without will be automatically ignored. The configuration file format is as follows:

```yml
name : Core Business
group : Subsystem
```

The `name` represents the name of the application repository, and `group` represents the repository's grouping. Users can group repositories as needed, for example, by business modules. `name` and `group` serve as unique identifiers for application repositories, and users can access repositories using these identifiers. If `name` and `group` are not specified, they default to the repository's path. For example, if the repository path is `svn://localhost/Test/product_source/biz`, the default `name` is `biz`, and the default `group` is `Test/product_source`.

Example 1: Retrieve a list of application repositories

```python
from smartci.ci_vcs import CiVcs
ci_vcs = CiVcs.Create()
for repo in ci_vcs.GetAllRepo():
    print(repo.GetName())
    print(repo.GetGroup())
    print(repo.GetUrl())
```

Example 2: Create a project branch for a specific application repository

```python
from smartci.ci_vcs import CiVcs
ci_vcs = CiVcs.Create()
repo = ci_vcs.GetRepo("Subsystem", "Core Business")
repo.AddBranch("2401_1_helloworld")
```
