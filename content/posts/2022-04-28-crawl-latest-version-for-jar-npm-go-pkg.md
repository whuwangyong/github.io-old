---
title: "使用python爬取jar包、npm包、go包的最新版本"
date: 2022-04-28
tags: ["python", "package", "maven"]
categories: ["小工具"]
---

## 场景
公司内网有maven仓库，扫描之后发现很多组件有漏洞，主要是因为版本太老。因此需要将这些漏洞组件的最新版导入内部的maven私服。

## 问题
这么多漏洞组件，一个个去中央仓库找最新版，显然不科学。因此要整个脚本来做这件事情。

## 方案

1. 众所周知，jar包的中央仓库是https://mvnrepository.com/，但是这个网站有反爬虫机制，使用脚本发出的请求不会得到响应结果。替代方案是[Maven Central Repository Search](https://search.maven.org/)，这也是官方提供的，“Official search by the maintainers of Maven Central Repository”。更令人激动的是，这个网站提供了[REST API](https://central.sonatype.org/search/rest-api-guide/)！不用你费尽心机的去解析网页，人家直接给你接口。
2. npm包，访问"https://registry.npmjs.org/{npm_package}/latest"，从该页面可以抓取最新版。
3. go module，访问"https://pkg.go.dev/{go_pkg }?tab=versions"，从该页面可以抓取最新版。
4. 这就万事大吉了吗？并不！这里有个大坑：什么是最新版本？上面这些网站按照时间戳排序返回的最新版，不一定是我们需要的。比如`4.0.0-RC`、`2.3.18`、`3.2.5`3个版本，按时间排序，不稳定的4.0.0-RC和太老的2.3.18排在了前面。但我们需要的是3.2.5版本。这就涉及到版本号排序算法。关于版本号排序，python官方是支持的。但支持有限：（1）不能处理超过3位的版本号，`1.2.3.4`这种会报错；（2）不能处理字母，如`2.12.2-Final`、`2.12.RELEASE`。因此，需要做一些额外处理，将满足需求的最新版本摘出来。这个有点难，有些开发者提供的包版本号命名不规范，特别长的、带日期的、带特殊字符的、alpha、beta的等等都有。

## 代码

可能需要的一些包：
```python
import math
import re
import traceback
from typing import Dict, List
import requests
from bs4 import BeautifulSoup

from distutils.version import StrictVersion
from natsort import natsorted
from soupsieve import match
```


获取jar包的最新版本：
```python
def process_maven(group_id, artifact_id):
    try:
        url = "https://search.maven.org/solrsearch/select?q=g:{} a:{}&core=gav&rows=5&wt=json".format(group_id, artifact_id)
        response = requests.get(url)
        json = response.json()
        docs = json["response"]["docs"]
        versions = []
        for doc in docs:
            version = str(doc["v"])
            if ("alpha" in version.lower() or "beta" in version.lower() or "dev" in version.lower() or "rc" in version.lower() ):
                continue
            else:
                versions.append(version)
        if len(versions) == 0:
            print("没有找到符合要求的版本，g={}, a={}".format(group_id, artifact_id))
            continue
        latest_version = get_lastest_version(versions)

        return latest_version
    except Exception as e:
        traceback.print_exc()
        print("error: %s. artifact_id=%s." % (e, artifact_id))
        print("response:", response)


def get_lastest_version(versions: List[str]) -> str:
    d = dict()
    for version in versions:  # version=4.3.10-RELEASE
        # 这种做法有问题  1.1.73.android: invalid version number '1.1.73.0000000'
        # fix_version = re.sub(r"[a-zA-Z-]", "0", version)

        # 最多只取前三位 1.2.3.4 -> 1.2.3
        fix_version = version
        if version.count(".") > 2:
            i = version.rfind(".")
            fix_version = version[:i]

        # 1.2.Final -> 1.2.
        a = re.findall(r"[0-9.]", fix_version)
        # 1.2. -> 1.2
        if a[-1] == ".":
            a.pop()
        fix_version = "".join(a)

        # 排除掉以日期命名的版本号，这种版本号不正式，如 20030418.083655
        if len(fix_version.split(".")[0]) >= 8:
            continue

        # 31.1-jre 31.1-android
        if fix_version not in d:
            d[fix_version] = version

    l = sorted(d, key=StrictVersion)
    return d[l[-1]]
```


获取npm包的最新版本：
```python
def process_npm(npm):
    try:
        response = requests.get(url="https://registry.npmjs.org/" + npm + "/latest").json()
        version = response["version"]
        return version
    except Exception as e:
        print("error: %s. npm=%s." % (e, npm))
        print("response:", response)
```

获取go module的最新版本：
```python
def process_go(go_pkg):
    try:
        response = requests.get(url="https://pkg.go.dev/" + go_pkg + "?tab=versions").content
        soup = BeautifulSoup(response, "html.parser")
        version_str = soup.find("a", class_="js-versionLink")
        version = version_str.contents[0]
        return version
    except Exception as e:
        print("error: %s. go_pkg=%s." % (e, go_pkg))
        print("response:", response)
```


