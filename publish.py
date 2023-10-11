#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
自动发布脚本，请在whuwangyong.github.io目录下运行。
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time

import requests
from algoliasearch.search_client import SearchClient

COMMIT_MSG_FILE = "commit-message"
BLOG_BR = "hugo-loveit"


def init():
    print("初始化")
    os.system("git checkout " + BLOG_BR)
    # os.system("git submodule update --init")


# 将上次编译出来的静态文件删除
def delete_last_hugo_files():
    print("将上次编译出来的静态文件删除")
    if os.path.exists("resources"):
        shutil.rmtree("resources")
    if os.path.exists("public"):
        shutil.rmtree("public")


# 处理post目录下的md文档，将相对路径的图片替换为在线url。这样做的目的是，便于md文档复制到其他平台进行发表
def replace_img_url():
    print("将相对路径的图片替换为在线url")
    post_dir = os.getcwd() + os.sep + "content" + os.sep + "posts"
    prefix = "https://cdn.jsdelivr.net/gh/whuwangyong/whuwangyong.github.io@gh-pages/"

    for root, dirs, files in os.walk(post_dir):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list

        if str(root).find("图片加载网速测试") != -1:
            continue

        # 遍历文件
        for f in files:
            if str(f).endswith(".md"):
                mdf = os.path.join(root, f)
                with open(mdf, "r+", encoding="utf-8") as md:
                    content = md.read()
                    # 查找该文章中的md图片语法
                    img_list = re.findall(r"!\[.*?\]\(.*?\)", content)
                    for i in img_list[::-1]:
                        if str(i).find("https") != -1:  # 如果已经是使用的在线地址，则不处理
                            img_list.remove(i)

                    if len(img_list) > 0:
                        # processing:  E:\blog\hugo-blog-stack\content\post\效率工具\vpn\V2Ray搭建指南\index.md
                        print("processing: ", mdf)

                        # 获取渲染为html之后文章的所在路径：md上级目录的小写
                        uplevel = str(mdf).split(os.sep)[-2].lower()

                        for img in img_list:
                            new_img = str(img).replace(
                                "](", "](" + prefix + uplevel + "/"
                            )
                            print("\treplacing " + img + " to " + new_img)
                            content = content.replace(img, new_img)
                    # 将指针移到文件头，然后写入替换后的内容
                    md.seek(0)
                    md.write(content)


# 在文末添加“本文同步发布于xxx”
def add_links():
    print("在文末添加“本文同步发布于xxx”")
    post_dir = os.getcwd() + os.sep + "content" + os.sep + "posts"
    for root, dirs, files in os.walk(post_dir):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list

        # 遍历文件
        for f in files:
            if str(f).endswith(".md"):
                mdf = os.path.join(root, f)
                with open(mdf, "a+", encoding="utf-8") as md:
                    md.seek(0)  # a+ 模式打开文件定位到末尾，需先seek到开始
                    lines = md.readlines()
                    if (
                            len(lines) > 3
                            and lines[-1].startswith("- https://whuwangyong.vercel.app/")
                            and lines[-2].startswith("- https://whuwangyong.netlify.app/")
                            and lines[-3].startswith("- https://whuwangyong.github.io/")
                    ):
                        continue
                    else:
                        if str(f) == "index.md":
                            mdf_name = str(root).split(os.sep)[-1]
                        else:
                            mdf_name = str(f)[:-3]  # 切掉 .md后缀
                        md.seek(2, 0)  # 定位到末尾
                        md.write(os.linesep + "---" + os.linesep)
                        md.write("本文同步发布于：\n")
                        md.write("- https://whuwangyong.github.io/" + mdf_name + "/\n")
                        md.write(
                            "- https://whuwangyong.netlify.app/" + mdf_name + "/\n"
                        )
                        md.write("- https://whuwangyong.vercel.app/" + mdf_name + "/")


# 删除文末的“本文同步发布于xxx”
def remove_links():
    post_dir = os.getcwd() + os.sep + "content" + os.sep + "posts"
    for root, dirs, files in os.walk(post_dir):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list

        # 遍历文件
        for f in files:
            if str(f).endswith(".md"):
                mdf = os.path.join(root, f)
                with open(mdf, "r+", encoding="utf-8") as md:
                    lines = md.readlines()
                    md.seek(0, os.SEEK_END)
                    total = md.tell()
                    if (
                            len(lines) > 3
                            and lines[-1].startswith("- https://whuwangyong.vercel.app/")
                            and lines[-2].startswith("- https://whuwangyong.netlify.app/")
                            and lines[-3].startswith("- https://whuwangyong.github.io/")
                    ):
                        # 205 + 21 = 226
                        # md.seek(total - len("".join(lines[-6:]))) # 定位到倒数第6行的行首位置
                        md.seek(total - len("".join(lines[-6:])) - 21)  # 定位到倒数第6行的行首位置
                        md.truncate()  # 截断之后的数据


# 提交 md 等源文件
def commit_md():
    print("提交md等源文件>>>>>>>>>>>>>>>>>>>>")
    os.system("git pull")
    os.system("git add .")
    os.system("git commit -F %s" % (COMMIT_MSG_FILE))
    os.system("git push")
    print("提交md等源文件完成<<<<<<<<<<<<<<<<")


# 开始渲染md为html
def start_hugo():
    print("开始渲染md为html")
    result = os.system("hugo")
    print("++ hugo completed! result=", result)


# 切换到gh-pages分支，删除旧文件，提交新文件
def commit_html():
    print("切换到 gh-pages 分支<<<<<<<<<<<<<<<<<<")
    os.system("git checkout gh-pages")

    # 删除旧文件，保留 .git/ 和 public/
    print("删除全部旧的静态文件，保留 commit-message，.gitignore，.git/，public/ 和子模块 themes/")
    for f in os.listdir():
        if os.path.isfile(f) and f not in ["commit-message", ".gitignore"]:
            os.remove(f)
            # print("remove:", f)
        if os.path.isdir(f) and f not in [".git", "public", "themes", ".idea"]:
            shutil.rmtree(f)
            # print("remove:", f)

    # 将 public/ 下面的文件移出来，然后删除空的public/文件夹
    print("将 public/ 下面的文件移出来，然后删除空的public/文件夹")
    if os.path.exists("public"):
        for f in os.listdir("public"):
            # print("++ move:", f)
            shutil.move(os.getcwd() + os.sep + "public" + os.sep + f, os.getcwd())
        os.rmdir("public")

    os.system("git add . > git_add.log 2>&1")
    os.system("git rm -f git_add.log")
    os.system("git commit -q -F " + COMMIT_MSG_FILE)
    os.system("git push -f")
    print("提交gh-pages完成>>>>>>>>>>>>>>>>>>")


# 将最新的url提交到百度和bing
# 需在 gh-pages 上操作，因为涉及到检测html文件
def commit_urls():
    print("将最新的url提交到百度和bing")
    os.system("git checkout gh-pages")
    urls = []

    ret = subprocess.run(
        "git rev-parse --short HEAD", stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if ret.returncode == 0:
        commit_id = str(ret.stdout, "utf_8").strip()
        print("最近一次的commitId:", commit_id)
        ret = subprocess.run(
            "git show --pretty=" " --name-only " + commit_id,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if ret.returncode == 0:
            changes = str(ret.stdout, "utf-8").split("\n")
            for change in changes:
                # 以20开始，表示年份，所有posts下面的博客命名都是年月日开始的
                if change.endswith(".html") and change.startswith("20"):
                    urls.append("https://whuwangyong.github.io/{}".format(change[:-10]))
        else:
            print("========================")
            print("subprocess run error:{}".format(ret.stderr))
    else:
        print("========================")
        print("subprocess run error:{}".format(ret.stderr))

    # 按时间排序
    urls.sort()
    # 取最新的5个文件
    urls = urls[-5:]

    print("本次提交的urls:", urls)

    if len(urls) > 0:
        # 提交到bing
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Host": "ssl.bing.com",
        }
        data = {"siteUrl": "https://whuwangyong.github.io/", "urlList": urls}
        response = requests.post(
            url="https://www.bing.com/webmaster/api.svc/json/SubmitUrlbatch?apikey=c8e29ae3ee2c4465a596a0ac7973b8f3",
            headers=headers,
            data=json.dumps(data),
        )
        print("bing的响应: ", response.content)

        # 提交到百度
        # headers = {
        #     "User-Agent": "curl/7.12.1",
        #     "Host": "data.zz.baidu.com",
        #     "Content-Type": "text/plain",
        # }
        # response = requests.post(
        #     url="http://data.zz.baidu.com/urls?site=https://whuwangyong.github.io&token=5os4wCK5ct7kBZRN",
        #     headers=headers,
        #     data="\n".join(urls),
        # )
        # print("百度的响应: ", response.content)


# 需要在gh-pages分支操作，因为要读index.json文件
def upload_index_2_algolia():
    print("上传索引文件到algolia...")
    # Connect and authenticate with your Algolia app
    client = SearchClient.create("YMLBEBNFHL", "4962bf8c8b0c034ee6ef247a9c162304")

    # Create a new index and add a record
    index = client.init_index("new-index-1649076215")
    with open('./index.json', 'r', encoding='utf8') as fp:
        json_data = json.load(fp)

    index.save_objects(json_data).wait()

    print("上传索引文件到algolia完成")


# 清除日志信息
def clear_commit_msg():
    print("清除日志信息")
    os.system("git checkout " + BLOG_BR)
    with open("commit-message", "r+", encoding="utf-8") as f:
        f.truncate(0)


def main():
    print("+++++++++++++++++++")
    print("++ publish start...")
    print("++ current dir is:", os.getcwd())
    hugo_dir = os.path.abspath(sys.path[0])  # 当前脚本所在的路径
    print("++ python script dir is:", hugo_dir)

    init()

    delete_last_hugo_files()

    # replace_img_url()

    # add_links()

    commit_md()

    start_hugo()

    commit_html()

    commit_urls()

    upload_index_2_algolia()

    clear_commit_msg()

    print("+++++++++++++++++++")
    print("done!")
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


if __name__ == "__main__":
    main()
