---
title: "如何在Spring Boot代码中执行sql脚本"
date: 2022-08-24
tags: ["springboot", "mysql"]
categories: ["springboot", "mysql"]
---

在spring应用运行时，有一些建表语句，或则初始化数据，需要从sql脚本导入。

本文推荐以下两种方法。

假设脚本位于`/resources/ddl.sql`

## 1 使用@sql注解

该注解可用于类和方法。

```java
@Sql(scripts = {"/ddl.sql"}, 
    config = @SqlConfig(encoding = "utf-8", 
        transactionMode = SqlConfig.TransactionMode.ISOLATED))
@SpringBootTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@Slf4j
public class RepositoryTest {
  
    @Autowired
    AppRepository appRepository;
  
    @Test
    @Order(1)
    public void insertApp(){
        appRepository.add(...)
        // ...
    }
}
```

注意，如果`@Sql`用于class，那么测试类里面的**每个测试方法在运行之前都会跑一次这个脚本**。

@sql上的注释有说明：

> @Sql is used to annotate a test class or test method to configure SQL scripts and statements to be executed against a given database during integration tests.
>
> ...
>
> Script execution is performed by the SqlScriptsTestExecutionListener...

看见`during integration tests`了吧。

另外，从注释可知，脚本是被`SqlScriptsTestExecutionListener`执行的。打开这个类，可以看到里面有一些方法和debug级别的日志。将这个包的日志级别设为debug：

```properties
logging.level.root=info
logging.level.org.springframework.test.context.jdbc=debug
```

然后运行，即可看到类似下面的日志：

```plaintext
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : Started RepositoryTest in 1.959 seconds (JVM running for 2.746)
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@e4927bb dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Starting...
 INFO [    Test worker] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Start completed.
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertApp
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@5e704109 dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertArtifact
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@701e3274 dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertHost
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@48ab1f96 dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertLicense
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@67d2c696 dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertTag
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@2473bf20 dataSource = '', transactionManager = '', transactionMode = ISOLATED, encoding = 'utf-8', separator = ';',...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertVulnerability
 INFO [ionShutdownHook] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Shutdown initiated...
 INFO [ionShutdownHook] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Shutdown completed.
BUILD SUCCESSFUL in 7s

```

从日志可见，确实在每个测试用例之前执行了脚本：

> Executing SQL scripts: [class path resource [ddl.sql]]

如果只需要该脚本执行一次该怎么做呢？将`@Sql(....)`注解放在某个`@Test`方法上，比如init方法，那么该脚本只会在执行init方法之前执行一次：

```java
@Sql(scripts = {"/ddl.sql"}, config = @SqlConfig(encoding = "utf-8", transactionMode = SqlConfig.TransactionMode.ISOLATED))
@Test
void init() {
    log.info("createTableUseAnno");
}
```

日志：

```plaintext
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : Started RepositoryTest in 1.916 seconds (JVM running for 2.683)
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Processing [MergedSqlConfig@6367d99b dataSource = '', transactionManager = ...
DEBUG [    Test worker] .s.t.c.j.SqlScriptsTestExecutionListener : Executing SQL scripts: [class path resource [ddl.sql]]
 INFO [    Test worker] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Starting...
 INFO [    Test worker] com.zaxxer.hikari.HikariDataSource       : HikariPool-1 - Start completed.
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : createTableUseAnno
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertApp
 INFO [    Test worker] cn.whu.wy.osgov.test.RepositoryTest      : insertArtifact
...

```

## 2 使用ScriptUtils.executeSqlScript

```java

@Autowired
DataSource dataSource;

void createTable() throws SQLException {
    Resource classPathResource = new ClassPathResource("ddl.sql");
    EncodedResource encodedResource = new EncodedResource(classPathResource, "utf-8");
    ScriptUtils.executeSqlScript(dataSource.getConnection(), encodedResource);
}
```

这种方式更加灵活，DataSource可以是自己创建的。

## 中文编码

上面两种方法都指定了`utf-8`编码。当表里面有中文时，不指定时会报错。

案例：有这样一个表，

```sql
CREATE TABLE app
(
    id   int                  NOT NULL AUTO_INCREMENT,
    name varchar(50)          NOT NULL,
    env  enum ('生产','测试') NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_name (name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;
```

env字段为枚举类型，通过本文提到的两种方法建表后（未指定`utf-8`编码），在插入数据时报错：

```sql
> INSERT app(name, env) VALUES ('app-1', '生产');

PreparedStatementCallback; Data truncated for column 'env' at row 1; 
nested exception is java.sql.SQLException: Data truncated for column 'env' at row 1
```

## 代码

我的[这个](https://github.com/whuwangyong/os-gov/blob/main/src/test/java/cn/whu/wy/osgov/test/RepositoryTest.java)项目使用了本文提到的内容，可以参考。

## Reference

1. [Guide on Loading Initial Data with Spring Boot | Baeldung](https://www.baeldung.com/spring-boot-data-sql-and-schema-sql)
2. [java执行SQL脚本文件 - 足下之路 - 博客园 (cnblogs.com)](https://www.cnblogs.com/fangyan1994/p/14123592.html)