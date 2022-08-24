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
    public void testInsert(){
        appRepository.add(...)
        // ...
    }
}
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

## 提示

上面两种方法都指定了`utf-8`编码。当表里面有中文时，需要注意。

案例：

有这样一个表，

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

env字段为枚举类型，通过本文提到的两种方法建表后，在插入数据时报错：

```sql
> INSERT app(name, env) VALUES ('app-1', '生产');

PreparedStatementCallback; Data truncated for column 'env' at row 1; 
nested exception is java.sql.SQLException: Data truncated for column 'env' at row 1
```

## Reference

1. [Guide on Loading Initial Data with Spring Boot | Baeldung](https://www.baeldung.com/spring-boot-data-sql-and-schema-sql)
2. [java执行SQL脚本文件 - 足下之路 - 博客园 (cnblogs.com)](https://www.cnblogs.com/fangyan1994/p/14123592.html)