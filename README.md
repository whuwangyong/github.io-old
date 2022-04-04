该项目用于构建个人博客。

## 分支
- main 分支不存放具体内容
- hugo-xx、jekyll-xx 等分支分别是采用不同建站框架及主题的源文件（含框架配置、主题配置、自己写的文章）
- gh-pages 分支用于发布静态网站。不管哪个框架/主题，编译后的静态文件放在这里

## 发布
目前使用 `hugo-loveit` 分支编辑内容。编辑完毕之后commit && push 即可触发 netlify、vercel 的 deployments：netlify、vercel 会从该分支拉取代码到他们自己环境，然后执行 build，最后将build 之后的静态资源 deploy 到他们的 app，用户就可以通过配置的域名进行访问了。

发布到 github.io 要复杂一些。由于 github pages 只支持 jekyll 项目，使用 hugo 创建的项目不会被 build。因此需要在自己的机器上执行 build 操作，然后将 build 出来的静态文件提交到 gh-pages 分支。

这个过程的脚本怎么写呢？

1. 文章写完
2. git commit && push 到 `hugo-loveit` 分支。此时 netlify、vercel 已经触发 build 和 deploy 了，不用操心
3. 执行 hugo，编译的结果在 public/ 目录下
4. 切换到 gh-pages 分支，删除除 public/ 目录外的所有文件，然后将 public/ 的全部内容剪切到 gh-pages 根目录下，最后删除空的 public/ 目录
5. commit && push，将内容发布到 gh-pages 分支。