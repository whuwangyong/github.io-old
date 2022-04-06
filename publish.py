#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
自动发布脚本，请在whuwangyong.github.io目录下运行。
"""

import os
import re
import shutil
import sys
import time

from numpy import add


# 该全局变量用于保存从commit-message文件读取的提交信息。
# 因为commit-message文件在hugo-loveit分支，切换到gh-pages分支后读不到了
global COMMIT_MSG

BLOG_BR = "hugo-loveit"


def init():
    print("初始化")
    os.system("git checkout " + BLOG_BR)
    os.system("git submodule update")


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
                        and lines[-1].startswith("https://whuwangyong.vercel.app/")
                        and lines[-2].startswith("https://whuwangyong.netlify.app/")
                        and lines[-3].startswith("https://whuwangyong.github.io/")
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
                        md.write("- https://whuwangyong.netlify.app/" + mdf_name + "/\n")
                        md.write("- https://whuwangyong.vercel.app/" + mdf_name + "/")


# 提交 md 等源文件
def commit_md():
    print("提交md等源文件")
    os.system("git add .")
    os.system("git commit -m " + get_commit_msg())
    os.system("git push")


# 开始渲染md为html
def start_hugo():
    print("开始渲染md为html")
    result = os.system("hugo")
    print("++ hugo completed! result=", result)


# 切换到gh-pages分支，删除旧文件，提交新文件
def commit_html():
    print("切换到gh-pages分支")
    os.system("git checkout gh-pages")

    # 删除旧文件，保留 .git/ 和 public/
    print("删除全部旧的静态文件，保留 .git/，themes 和 public/")
    for f in os.listdir():
        if os.path.isfile(f):
            os.remove(f)
        else:
            if f in [".git", "themes", "public"]:
                continue
            else:
                shutil.rmtree(f)
                print("++ remove dir:", f)

    # 将 public/ 下面的文件移出来，然后删除空的public/文件夹
    print("将 public/ 下面的文件移出来，然后删除空的public/文件夹")
    for f in os.listdir("public"):
        print("++ move:", f)
        shutil.move(os.getcwd() + os.sep + "public" + os.sep + f, os.getcwd())
    os.rmdir("public")

    os.system("git add .")
    os.system("git commit -m " + COMMIT_MSG)
    os.system("git push")


# 从 commit-message 文件读取提交信息
# （执行脚本前，需手动将commit信息写入commit-message文件）
def get_commit_msg():
    print("从 commit-message 文件读取提交信息")
    with open("commit-message", "r+", encoding="utf-8") as f:
        commit_msg = f.read()
        if len(commit_msg) == 0:
            raise Exception("commit message is empty")
        else:
            print("commit message: ", commit_msg)
            global COMMIT_MSG
            COMMIT_MSG = commit_msg
            return commit_msg


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

    replace_img_url()

    add_links()

    commit_md()

    start_hugo()

    commit_html()

    clear_commit_msg()

    print("+++++++++++++++++++")
    print("done!")
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


if __name__ == "__main__":
    main()
