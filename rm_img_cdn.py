# 将md文件里使用cdn.jsdelivr.net加速的图片全部改为相对路径引用。cdn.jsdelivr.net最近不可用。

import os

post_dir = os.getcwd() + os.sep + "content" + os.sep + "posts"
prefix = "](https://cdn.jsdelivr.net/gh/whuwangyong/whuwangyong.github.io@gh-pages/"

for root, dirs, files in os.walk(post_dir):
    if str(root).find("图片加载网速测试") != -1:
        continue
    for f in files:
        if str(f).endswith(".md"):
            mdf = os.path.join(root, f)
            with open(mdf, "r+", encoding="utf-8") as md:
                res = list()
                for line in md.readlines():
                    i = line.find(prefix)
                    if i != -1:
                        j = line.find("/assets/")
                        line = line[: i + 2] + line[j + 1 :]
                    res.append(line)
                md.seek(0)
                md.truncate()
                for s in res:
                    md.write(s)
