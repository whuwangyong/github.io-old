---
title: "ant design pro 整合springboot后刷新404问题"
date: 2023-10-11
tags: ["ant design pro","umi","react", "springboot","刷新","404"]
categories: ["前端","react"]
---

ant 官方指南，`npm run build` 之后将生成的文件放到spring项目 `/src/main/resources/static`目录下即可。

为了方便做整合，最好使用 hash 路由。如果你想使用 browserHistory ，可以创建一个 controller ，并添加如下代码：

```java
@RequestMapping(value="/**", method=HTTPMethod.GET)
public String index(){
    return "index" // 或者 index.html
}
```

测试后发现页面无法访问，后端报错：

```java
Error resolving template [index]
```

因为spring thymeleaf 使用的模板需要放在`resources/templates`目录下。如果不使用thymeleaf模板，也会有其他的报错。

针对刷新这个问题，网络上一般有3种方案：

1. 不要使用browser，使用hash。但是由于我在ant design pro 的ProTable中启用url地址栏同步，改为hash后，带参数跳转时，地址栏混乱，地址栏参数无法正确同步到表单，故放弃
2. config/config.js 里配exportStatic，这个ant design pro 的模板本来就是启用的，无效

    ```java
    export default {
      // ...
      exportStatic: {}
    }
    ```
3. 服务端配置路由 fallback 到 index.html。但是如前文所示的配置不对的，最后在StackOverflow上找到正确配置：

    ```java
    @Configuration
    public class WebConfiguration extends WebMvcConfigurerAdapter {

      @Override
      public void addViewControllers(ViewControllerRegistry registry) {
          registry.addViewController("/{spring:\\w+}")
                .setViewName("forward:/");
          registry.addViewController("/**/{spring:\\w+}")
                .setViewName("forward:/");
          registry.addViewController("/{spring:\\w+}/**{spring:?!(\\.js|\\.css)$}")
                .setViewName("forward:/");
      }
    }
    ```


参考链接：

1. [部署 - Ant Design Pro (gitee.io)](https://ant-design-pro.gitee.io/zh-CN/docs/deploy)
2. [Spring catch all route for index.html - Stack Overflow](https://stackoverflow.com/questions/39331929/spring-catch-all-route-for-index-html/42998817#42998817)