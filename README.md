# Django ProxySQL Demo

This is a demo project to test a Django application with ProxySQL.


# Test environment

## docker-compose

services:

- db1 (mysql running with `repeatable-read` transaction isolation)
- proxysql

  - connected to db1
  - `mysql-init_connect` set to `SET SESSION TX_ISOLATION='REPEATABLE-READ'`
  - `mysql-autocommit_is_transaction` set to `true`
- app_db (django app connected to `db1`)
- app_proxysql (django app connected to `proxysql`)

## Test script

```
./manage.py test_savepoints
```

This command tests running two processes in parallel running transactions.
`run_atomic_transactions` or `T1` runs plain `atomic` transactions and
`run_savepoints` or `T2` runs nested `atomic` transactions which internally uses
`SAVEPOINT` queries.

This is how the script should work.

At t=0, `T1` and `T2` starts almost together
and they both read the same `count` value from `count` row with `bucket` id `1`.
In this case, count is `0`

At t=1, `T1` updates `count` field.

At t=1.5, `T2` reads `count` for `bucket` id 1. It will see different values
of count based on what tx_isolation is used.

- `read-uncommitted`: 200
- `read-committed`: 0
- `repeatable-read`: 0

At t=2, `T1` successfully commits the atomic transaction
and sets count to 200.

At t=2.5, `T2` reads count for bucket_id 1, and sees the
newly committed value by `T1`, which is 200. It then
goes ahead and updates the count value to 1. It then enters the inner
transaction block and increment count value by 1, which means count becomes
2. Since count is even, it gets committed in the inner transaction block
(if count were odd, it would have been rollbacked to value set by
the outer transaction). Please not that the outer block transaction has
not yet been committed.

At t=3, `T1` reads count for bucket_id 1 sees the following values of count for different tx_isolation levels:

- `read-uncommitted`: 2
- `read-committed`: 200
- `repeatable-read`: 200

At t=3.5, `T2` exits the outer transaction block by setting count to 2.

At t=4, next iteration for both processes start.


## Run test environment

```
docker-compose up -d
```


## Run tests

### 1. READ UNCOMMITTED

#### 1.1 db

```
docker-compose exec app_db bash -c "TX_ISOLATION='read uncommitted' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:16:31,978 counter 234 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:16:31,982 counter 235 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:16:32,988 counter 235 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:16:33,482 counter 234 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:16:33,994 counter 235 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:16:34,486 counter 234 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:16:34,492 counter 234 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:16:34,495 counter 234 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:16:34,497 counter 234 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:16:34,499 counter 234 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:16:35,000 counter 235 INFO] T1      	200     	main    	        	2
[2019-05-04 17:16:35,504 counter 234 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:16:35,504 counter 234 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:16:36,012 counter 235 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:16:36,016 counter 234 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:16:37,021 counter 235 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:16:37,521 counter 234 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:16:38,027 counter 235 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:16:38,526 counter 234 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:16:38,529 counter 234 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:16:38,532 counter 234 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:16:38,535 counter 234 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:16:38,537 counter 234 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:16:39,032 counter 235 INFO] T1      	201     	main    	        	2
[2019-05-04 17:16:39,543 counter 234 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:16:39,544 counter 234 INFO] T2      	2       	outer   	exit    	2
```

#### 1.2 proxysql

Set `mysql-init_connect` in ProxySQL to `SET SESSION TX_ISOLATION='READ-UNCOMMITTED'`

```
docker-compose exec proxysql mysql -h 127.0.0.1 -P 6032 -uadmin -padmin -D main -e "UPDATE global_variables SET variable_value=\"SET SESSION TX_ISOLATION='READ-UNCOMMITTED'\" WHERE variable_name='mysql-init_connect'; SAVE MYSQL VARIABLES TO DISK; LOAD MYSQL VARIABLES TO RUNTIME; SELECT * FROM runtime_global_variables WHERE variable_name='mysql-init_connect';"
```

```
docker-compose exec app_proxysql bash -c "TX_ISOLATION='read uncommitted' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:18:22,184 counter 72 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:18:22,185 counter 73 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:18:23,191 counter 72 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:18:23,689 counter 73 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:18:24,197 counter 72 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:18:24,693 counter 73 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:18:24,697 counter 73 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:18:24,699 counter 73 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:18:24,703 counter 73 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:18:24,705 counter 73 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:18:25,201 counter 72 INFO] T1      	200     	main    	        	2
[2019-05-04 17:18:25,709 counter 73 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:18:25,713 counter 73 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:18:26,208 counter 72 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:18:26,229 counter 73 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:18:27,215 counter 72 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:18:27,734 counter 73 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:18:28,220 counter 72 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:18:28,740 counter 73 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:18:28,744 counter 73 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:18:28,747 counter 73 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:18:28,751 counter 73 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:18:28,762 counter 73 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:18:29,225 counter 72 INFO] T1      	201     	main    	        	2
[2019-05-04 17:18:29,768 counter 73 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:18:29,769 counter 73 INFO] T2      	2       	outer   	exit    	2
```

### 2. READ-COMMITTED

#### 2.1 db

```
docker-compose exec app_db bash -c "TX_ISOLATION='read committed' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:28:43,943 counter 249 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:28:43,943 counter 248 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:28:44,949 counter 249 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:28:45,448 counter 248 INFO] T2      	1       	outer   	        	0
[2019-05-04 17:28:45,955 counter 249 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:28:46,453 counter 248 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:28:46,457 counter 248 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:28:46,459 counter 248 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:28:46,461 counter 248 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:28:46,464 counter 248 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:28:46,960 counter 249 INFO] T1      	200     	main    	        	200
[2019-05-04 17:28:47,467 counter 248 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:28:47,468 counter 248 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:28:47,979 counter 249 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:28:47,979 counter 248 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:28:48,986 counter 249 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:28:49,485 counter 248 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:28:49,991 counter 249 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:28:50,488 counter 248 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:28:50,491 counter 248 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:28:50,494 counter 248 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:28:50,498 counter 248 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:28:50,501 counter 248 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:28:50,995 counter 249 INFO] T1      	201     	main    	        	201
[2019-05-04 17:28:51,505 counter 248 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:28:51,506 counter 248 INFO] T2      	2       	outer   	exit    	2
```

#### 2.2 proxysql

Set `mysql-init_connect` ProxySQL global variable to `SET SESSION TX_ISOLATION='READ-COMMITTED'`

```
docker-compose exec proxysql mysql -h 127.0.0.1 -P 6032 -uadmin -padmin -D main -e "UPDATE global_variables SET variable_value=\"SET SESSION TX_ISOLATION='READ-COMMITTED'\" WHERE variable_name='mysql-init_connect'; SAVE MYSQL VARIABLES TO DISK; LOAD MYSQL VARIABLES TO RUNTIME; SELECT * FROM runtime_global_variables WHERE variable_name='mysql-init_connect';"
```

```
docker-compose exec app_proxysql bash -c "TX_ISOLATION='read committed' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:31:00,238 counter 182 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:31:00,238 counter 183 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:31:01,245 counter 182 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:31:01,744 counter 183 INFO] T2      	1       	outer   	        	0
[2019-05-04 17:31:02,251 counter 182 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:31:02,750 counter 183 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:31:02,754 counter 183 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:31:02,757 counter 183 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:31:02,760 counter 183 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:31:02,764 counter 183 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:31:03,256 counter 182 INFO] T1      	200     	main    	        	200
[2019-05-04 17:31:03,769 counter 183 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:31:03,770 counter 183 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:31:04,267 counter 182 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:31:04,280 counter 183 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:31:05,277 counter 182 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:31:05,787 counter 183 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:31:06,282 counter 182 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:31:06,791 counter 183 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:31:06,802 counter 183 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:31:06,804 counter 183 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:31:06,808 counter 183 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:31:06,812 counter 183 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:31:07,288 counter 182 INFO] T1      	201     	main    	        	201
[2019-05-04 17:31:07,816 counter 183 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:31:07,817 counter 183 INFO] T2      	2       	outer   	exit    	2
```

### 3. REPEATABLE-READ

#### 3.1 db

```
docker-compose exec app_db bash -c "TX_ISOLATION='repeatable read' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:34:17,157 counter 264 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:34:17,158 counter 263 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:34:18,161 counter 264 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:34:18,662 counter 263 INFO] T2      	1       	outer   	        	0
[2019-05-04 17:34:19,167 counter 264 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:34:19,666 counter 263 INFO] T2      	1       	outer   	        	0
[2019-05-04 17:34:19,670 counter 263 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:34:19,672 counter 263 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:34:19,674 counter 263 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:34:19,676 counter 263 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:34:20,171 counter 264 INFO] T1      	200     	main    	        	200
[2019-05-04 17:34:20,681 counter 263 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:34:20,682 counter 263 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:34:21,183 counter 264 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:34:21,193 counter 263 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:34:22,189 counter 264 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:34:22,698 counter 263 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:34:23,196 counter 264 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:34:23,705 counter 263 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:34:23,710 counter 263 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:34:23,714 counter 263 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:34:23,718 counter 263 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:34:23,722 counter 263 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:34:24,202 counter 264 INFO] T1      	201     	main    	        	201
[2019-05-04 17:34:24,726 counter 263 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:34:24,727 counter 263 INFO] T2      	2       	outer   	exit    	2
```

#### 3.1 proxysql

Set `mysql-init_connect` ProxySQL global variable to `SET SESSION TX_ISOLATION='REPEATABLE-READ'`

```
docker-compose exec proxysql mysql -h 127.0.0.1 -P 6032 -uadmin -padmin -D main -e "UPDATE global_variables SET variable_value=\"SET SESSION TX_ISOLATION='REPEATABLE-READ'\" WHERE variable_name='mysql-init_connect'; SAVE MYSQL VARIABLES TO DISK; LOAD MYSQL VARIABLES TO RUNTIME; SELECT * FROM runtime_global_variables WHERE variable_name='mysql-init_connect';"
```

```
docker-compose exec app_proxysql bash -c "TX_ISOLATION='repeatable read' ./manage.py test_savepoints --trials 2"
```

**OUTPUT**

```
[2019-05-04 17:36:02,592 counter 196 INFO] T1      	200     	main    	enter   	0
[2019-05-04 17:36:02,595 counter 197 INFO] T2      	1       	outer   	enter   	0
[2019-05-04 17:36:03,600 counter 196 INFO] T1      	200     	main    	save    	200
[2019-05-04 17:36:04,099 counter 197 INFO] T2      	1       	outer   	        	0
[2019-05-04 17:36:04,607 counter 196 INFO] T1      	200     	main    	exit    	200
[2019-05-04 17:36:05,105 counter 197 INFO] T2      	1       	outer   	        	200
[2019-05-04 17:36:05,109 counter 197 INFO] T2      	1       	outer   	        	1
[2019-05-04 17:36:05,112 counter 197 INFO] T2      	1       	inner   	enter   	1
[2019-05-04 17:36:05,115 counter 197 INFO] T2      	1       	inner   	save    	2
[2019-05-04 17:36:05,118 counter 197 INFO] T2      	1       	inner   	exit    	2
[2019-05-04 17:36:05,611 counter 196 INFO] T1      	200     	main    	        	200
[2019-05-04 17:36:06,122 counter 197 INFO] T2      	1       	outer   	        	2
[2019-05-04 17:36:06,123 counter 197 INFO] T2      	1       	outer   	exit    	2
[2019-05-04 17:36:06,621 counter 196 INFO] T1      	201     	main    	enter   	2
[2019-05-04 17:36:06,631 counter 197 INFO] T2      	2       	outer   	enter   	2
[2019-05-04 17:36:07,626 counter 196 INFO] T1      	201     	main    	save    	201
[2019-05-04 17:36:08,137 counter 197 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:36:08,632 counter 196 INFO] T1      	201     	main    	exit    	201
[2019-05-04 17:36:09,144 counter 197 INFO] T2      	2       	outer   	        	201
[2019-05-04 17:36:09,148 counter 197 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:36:09,151 counter 197 INFO] T2      	2       	inner   	enter   	2
[2019-05-04 17:36:09,154 counter 197 INFO] T2      	2       	inner   	save    	3
[2019-05-04 17:36:09,157 counter 197 INFO] T2      	2       	inner   	exit    	2
[2019-05-04 17:36:09,637 counter 196 INFO] T1      	201     	main    	        	201
[2019-05-04 17:36:10,161 counter 197 INFO] T2      	2       	outer   	        	2
[2019-05-04 17:36:10,162 counter 197 INFO] T2      	2       	outer   	exit    	2
```

## Conclusions

We see from the above results from **1** and **2** is that ProxySQL works quite well
with `SAVEPOINTS` as expected with `TX_ISOLATION` levels: `READ-UNCOMMITTTED`, `READ-COMMITTED`.

However, with `TX_ISOLATION` level `REPEATABLE-READ` in **3**, ProxySQL seems to behave
as if the `TX_ISOLATION` level were `READ-COMMITTED`. This is a problem. We have
not been able to workaround this issue yet.
