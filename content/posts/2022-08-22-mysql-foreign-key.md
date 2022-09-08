---
title: "MySQL外键"
date: 2022-08-22
tags: ["mysql", "外键"]
categories: ["mysql"]
---

## 语法

在创建表的时候指定外键约束

```sql
CREATE TABLE 表名
(
    column1 datatype null/not null,
    column2 datatype null/not null,
    ...
    CONSTRAINT 外键约束名 FOREIGN KEY  (column1,column2,... column_n) 
    REFERENCES 外键依赖的表 (column1,column2,...column_n)
    ON DELETE CASCADE--级联删除
    ON UPDATE CASCADE--级联更新
);
```

## 测试

有如下2个表：

```sql
CREATE TABLE t_product
(
    id    int         NOT NULL AUTO_INCREMENT,
    name  varchar(50) NOT NULL,
    price double      NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_name (name)
);



CREATE TABLE t_order
(
    id         int NOT NULL AUTO_INCREMENT,
    product_id int NOT NULL,
    amount     int NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_pid FOREIGN KEY (product_id) REFERENCES t_product (id)
    // 这里未启用级联删除
);
```

### 删表的顺序

删表时，要先删子表`t_order`，再删父表`t_product`

### 级联删除

被子表引用的记录，无法直接从父表删除

```sql
INSERT INTO t_product (name, price) VALUES ('xiaomi', 1999.99);
INSERT INTO t_product (name, price) VALUES ('redmi', 999.99);
INSERT INTO t_order(product_id, amount) VALUES (1, 10);

// 失败，被子表引用
// [23000][1451] Cannot delete or update a parent row: a foreign key constraint fails
DELETE FROM t_product WHERE name='xiaomi';

// 成功，未被引用
DELETE FROM t_product WHERE name='redmi';
```

如何实现删除父表记录时，**级联删除**子表的记录？定义外键时指定`ON DELETE CASCADE`：

建表时申明：

```sql
CREATE TABLE t_order
(
    id         int NOT NULL AUTO_INCREMENT,
    product_id int NOT NULL,
    amount     int NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_pid FOREIGN KEY (product_id) REFERENCES t_product (id) 
        ON DELETE CASCADE
);
```

修改已有的表：

```sql
alter table test.t_order
    drop foreign key fk_pid;

alter table test.t_order
    add constraint fk_pid
        foreign key (product_id) references test.t_product (id)
            on delete cascade;

```

### drop/truncate父表

设置了级联关系的表，可以直接`drop/truncate`父表吗？不行。即使子表里面已经没有引用父表的记录，子表为空表也不行。

如何解决：

#### 临时关闭外键约束

缺点：可能破坏完整性。删表之后务必手动清理关联的子表里面的记录。

```sql
SET FOREIGN_KEY_CHECKS = 0; 
TRUNCATE table $table_name; 
SET FOREIGN_KEY_CHECKS = 1;
```

#### 使用delete

优点是保证了完整性，缺点是数据量大时很慢。

```sql
DELETE FROM mytest.instance;
ALTER TABLE mytest.instance AUTO_INCREMENT = 1;
```

## 是否推荐使用外键

> 《高性能MySQL》7.3节
>
> InnoDB是目前MySQL中唯一支持外键的内置存储引擎，所以如果需要外键支持那选择就不多了（PBXT也有外键支持）。
>
> 使用外键是有成本的。比如外键通常都要求每次在修改数据时都要在另外一张表中多执行一次查找操作。虽然InnoDB强制外键使用索引，但还是无法消除这种约束检查的开销。如果外键列的选择性很低，则会导致一个非常大且选择性很低的索引。例如，在一个非常大的表上有status列，并希望限制这个状态列的取值，如果该列只能取三个值——虽然这个列本身很小，但是如果主键很大，那么这个索引就会很大——而且这个索引除了做这个外键限制，也没有任何其他的作用了。
>
> 不过，在某些场景下，外键会提升一些性能。如果想确保两个相关表始终有一致的数据，那么使用外键比在应用程序中检查一致性的性能要高得多，此外，外键在相关数据的删除和更新上，也比在应用中维护要更高效，不过，外键维护操作是逐行进行的，所以这样的更新会比批量删除和更新要慢些。
>
> 外键约束使得查询需要额外访问一些别的表，这也意味着需要额外的锁。如果向子表中写入一条记录，外键约束会让InnoDB检查对应的父表的记录，也就需要对父表对应记录进行加锁操作，来确保这条记录不会在这个事务完成之时就被删除了。这会导致额外的锁等待，甚至会导致一些死锁。因为没有直接访问这些表，所以这类死锁问题往往难以排查。
>
> 有时，可以使用触发器来代替外键。对于相关数据的同时更新外键更合适，但是如果外键只是用作数值约束，那么触发器或者显式地限制取值会更好些。（这里，可以直接使用ENUM类型。）
>
> 如果只是使用外键做约束，那通常在应用程序里实现该约束会更好。外键会带来很大的额外消耗。这里没有相关的基准测试的数据，不过我们碰到过很多案例，在对性能进行剖析时发现外键约束就是瓶颈所在，删除外键后性能立即大幅提升。
>
> **总结**
>
> 外键限制会将约束放到MySQL中，这对于必须维护外键的场景，性能会更高。
> 不过这也会带来额外的复杂性和额外的索引消耗，还会增加多表之间的交互，会导致系统中更多的锁和竞争。外键可以被看作是一个确保系统完整性的额外的特性，但是如果设计的是一个高性能的系统，那么外键就显得很臃肿了。很多人在更在意系统的性能的时候都不会使用外键，而是通过应用程序来维护。