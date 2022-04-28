---
title: "使用python爬取jar包、npm包、go包的最新版本"
date: 2022-04-28
tags: ["python", "package", "maven"]
categories: ["小工具"]
---

**场景**：公司内网有maven仓库，扫描之后发现很多组件有漏洞，主要是因为版本太老。因此需要将这些漏洞组件的最新版导入内部的maven私服。

**问题**：这么多漏洞组件，一个个去中央仓库找最新版，显然不科学。因此要整个脚本来做这件事情。

**Tips**：

1. 众所周知，jar包的中央仓库是https://mvnrepository.com/，但是这个网站有反爬虫机制，使用脚本发出的请求不会得到响应结果。替代方案是[Maven Central Repository Search](https://search.maven.org/)，这也是官方提供的，“Official search by the maintainers of Maven Central Repository”。更令人激动的是，这个网站提供了[REST API](https://central.sonatype.org/search/rest-api-guide/)！不用你费尽心机的去解析网页，人家直接给你接口。
2. npm包，访问"https://registry.npmjs.org/{npm_package}/latest"，从该页面可以抓取最新版。
3. go module，访问"https://pkg.go.dev/{go_pkg }?tab=versions"，从该页面可以抓取最新版。
4. 这就万事大吉了吗？并不！这里有个大坑：什么是最新版本？上面这些网站按照时间戳排序返回的最新版，不一定是我们需要的。比如`4.0.0-RC`、`2.3.18`、`3.2.5`3个版本，按时间排序，不稳定的4.0.0-RC和太老的2.3.18排在了前面。但我们需要的是3.2.5版本。这就涉及到版本号排序算法。关于版本号排序，python官方是支持的。但支持有限：（1）不能处理超过3位的版本号，`1.2.3.4`这种会报错；（2）不能处理字母，如`2.12.2-Final`、`2.12.RELEASE`。因此，需要做一些额外处理，将满足需求的最新版本摘出来。这个有点难，有些开发者提供的包版本号命名不规范，特别长的、带日期的、带特殊字符的、alpha、beta的等等都有。

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


def read():
    mavens = dict()
    npms = set()

    with open("zhujixiayi-vuls.txt", encoding="utf_8") as f:
        lines = f.readlines()
        for line in lines:
            arr = line.split()
            if len(arr) == 3:
                npms.add(arr[0].strip())
            elif len(arr) == 4:
                mavens[arr[0].strip()] = arr[1].strip()
            else:
                print("unexpected line:", line)

        print("lines:", len(lines))
        print("npms + goes:", len(npms))
        print("mavens:", len(mavens))
        return sorted(mavens.items()), sorted(npms)


def process_maven(mavens, result):
    print("======== java ========")
    for maven in mavens:
        try:
            artifact_id = maven[0]
            group_id = maven[1]
            url = "https://search.maven.org/solrsearch/select?q=g:{} a:{}&core=gav&rows=5&wt=json".format(
                group_id, artifact_id
            )
            response = requests.get(url)
            json = response.json()
            docs = json["response"]["docs"]
            versions = []
            for doc in docs:
                version = str(doc["v"])
                if (
                    "alpha" in version.lower()
                    or "beta" in version.lower()
                    or "dev" in version.lower()
                    or "rc" in version.lower()
                ):
                    continue
                else:
                    versions.append(version)
            if len(versions) == 0:
                print("没有找到符合要求的版本，g={}, a={}".format(group_id, artifact_id))
                continue

            print(versions)
            latest_version = get_lastest_version(versions)

            res = "implementation '{}:{}:{}'".format(
                group_id, artifact_id, latest_version
            )
            print(res)
            result.append(res + "\n")
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


# #
# def sort_versions(versions: List[str]) -> Dict:
#     d = dict()
#     for version in versions: # version=4.3.10-RELEASE
#         vs = list()
#         for sub_v in version.split("."):
#             sub_v = re.sub(r"[a-zA-Z-]","0",sub_v)
#             if int(sub_v) < 100:
#                 vs.append(int(sub_v))
#             else:
#                 vs.append(0)
#         # vs = [4,3,10]
#         d[sum_list_10000(vs)] = version
#     return sorted(d.items())

# # 10000进制数组求和
# def sum_list_10000(l:List[int]) -> int:
#     sum = 0
#     j=0
#     for i in l[::-1]:
#         sum += i * int(math.pow(10000,j))
#         j += 1
#     return sum

# 网站有反爬机制
# def process_maven2(mavens, result):
#     print("======== java ========")
#     headers = {
#         "cookie": "_ga=GA1.2.772653431.1617776653; _gid=GA1.2.898033206.1650589145; cf_clearance=ngnmCAOeSr2_haa.egGzxNttz1aO4nSPn_LAtJg6u5E-1650609943-0-150; __cf_bm=HyYCP4WWmEsqeMEfL9.5Hi1GmBrtfHOR9TBNp2sJgs0-1650611165-0-Aa2FOfnC7GYCFkWpfqv0+rgDMc6kvpxeW5/z/mUc/9GfoGY4Fh8TgAnRQ1kPA7AxQIUAKXNaVx8KDEUM5IUKniRBJ+9AOLf+3vkKCEiT/pmz+5cJUnYBB3aRcuZhxgXZmg==; _gat=1; MVN_SESSION=eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InVpZCI6ImRkY2MzNTAxLTk3NjktMTFlYi1hMDI3LWVkN2FhNjY0MjAyOSJ9LCJleHAiOjE2ODIxNDc3MzQsIm5iZiI6MTY1MDYxMTczNCwiaWF0IjoxNjUwNjExNzM0fQ.Tg5TnSl3szI3j3Nr3ksJ4lze1uIYk6sI_NvGUEWeuUo"
#     }
#     for maven in mavens:
#         try:
#             artifact_id = maven[0]
#             group_id = maven[1]
#             response = requests.get(url="https://mvnrepository.com/artifact/{}/{}".format(group_id,artifact_id), headers=headers).content


#         except Exception as e:
#             print("error: %s. artifact_id=%s." % (e, artifact_id))
#             print("response:", response)

# 网站有反爬机制
# def process_npm(npms):
#     print("======== js ========")
#     for npm in npms:
#         try:
#             response = requests.get(url="https://www.npmjs.com/package/" + npm).content
#             soup = BeautifulSoup(response, 'html.parser')
#             version_str = soup.find("span", class_="_76473bea f6 dib ph0 pv2 mb2-ns black-80 nowrap f5 fw4 lh-copy")
#             version = version_str.contents[0]
#             print(npm, version)
#         except Exception as e:
#             print("error: %s. npm=%s." % (e, npm))
#             print("response:", response)


def process_npm2(npms, result):
    print("======== js ========")
    goes = set()
    for npm in npms:
        try:
            response = requests.get(
                url="https://registry.npmjs.org/" + npm + "/latest"
            ).json()

            # 如果这玩意不是一个npm的包，那就是go
            if response == "Not Found":
                goes.add(npm)
            else:
                version = response["version"]
                print(npm, version)
                result.append('"{}": "{}",\n'.format(npm, version))
        except Exception as e:
            print("error: %s. npm=%s." % (e, npm))
            print("response:", response)
    return goes


def process_go(go_pkgs, result):
    print("======== go ========")
    for go_pkg in go_pkgs:
        try:
            response = requests.get(
                url="https://pkg.go.dev/" + go_pkg + "?tab=versions"
            ).content
            soup = BeautifulSoup(response, "html.parser")
            version_str = soup.find("a", class_="js-versionLink")
            version = version_str.contents[0]
            print(go_pkg, version)
            result.append("{} {}\n".format(go_pkg, version))
        except Exception as e:
            print("error: %s. go_pkg=%s." % (e, go_pkg))
            print("response:", response)


def write(result):
    with open("new_version.txt", "w+") as f:
        f.writelines(result)


if __name__ == "__main__":
    mavens, npms = read()

    result = []
    process_maven(mavens, result)

    goes = process_npm2(npms, result)
    process_go(goes, result)

    write(result)
```

---
本文同步发布于：
- https://whuwangyong.github.io/2022-04-28-crawl-latest-version-for-jar-npm-go-pkg/
- https://whuwangyong.netlify.app/2022-04-28-crawl-latest-version-for-jar-npm-go-pkg/
- https://whuwangyong.vercel.app/2022-04-28-crawl-latest-version-for-jar-npm-go-pkg/