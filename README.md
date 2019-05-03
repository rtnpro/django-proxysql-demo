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

### Run

```
docker-compose up -d
```


### Run tests

#### 1. app_db with tx_isolation READ-COMMITTED

```
docker-compose exec app_db bash -c "./manage.py test_savepoints"
```

```
[2019-05-03 15:29:14,367 counter 40 INFO] ATOMIC    	200       	main      	enter     	203
[2019-05-03 15:29:14,377 counter 41 INFO] SAVEPOINT 	1         	outer     	enter     	203
[2019-05-03 15:29:15,373 counter 40 INFO] ATOMIC    	200       	main      	save      	200
[2019-05-03 15:29:15,884 counter 41 INFO] SAVEPOINT 	1         	outer     	          	203
[2019-05-03 15:29:16,378 counter 40 INFO] ATOMIC    	200       	main      	exit      	200
[2019-05-03 15:29:16,889 counter 41 INFO] SAVEPOINT 	1         	outer     	          	200
[2019-05-03 15:29:16,893 counter 41 INFO] SAVEPOINT 	1         	outer     	          	1
[2019-05-03 15:29:16,898 counter 41 INFO] SAVEPOINT 	1         	inner     	enter     	1
[2019-05-03 15:29:16,902 counter 41 INFO] SAVEPOINT 	1         	inner     	save      	2
[2019-05-03 15:29:16,906 counter 41 INFO] SAVEPOINT 	1         	inner     	exit      	2
[2019-05-03 15:29:17,383 counter 40 INFO] ATOMIC    	200       	main      	          	200
[2019-05-03 15:29:17,912 counter 41 INFO] SAVEPOINT 	1         	outer     	          	2
[2019-05-03 15:29:17,914 counter 41 INFO] SAVEPOINT 	1         	outer     	exit      	2
[2019-05-03 15:29:18,391 counter 40 INFO] ATOMIC    	201       	main      	enter     	2
[2019-05-03 15:29:18,426 counter 41 INFO] SAVEPOINT 	2         	outer     	enter     	2
[2019-05-03 15:29:19,397 counter 40 INFO] ATOMIC    	201       	main      	save      	201
[2019-05-03 15:29:19,935 counter 41 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:29:20,403 counter 40 INFO] ATOMIC    	201       	main      	exit      	201
[2019-05-03 15:29:20,942 counter 41 INFO] SAVEPOINT 	2         	outer     	          	201
[2019-05-03 15:29:20,946 counter 41 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:29:20,948 counter 41 INFO] SAVEPOINT 	2         	inner     	enter     	2
[2019-05-03 15:29:20,951 counter 41 INFO] SAVEPOINT 	2         	inner     	save      	3
[2019-05-03 15:29:20,954 counter 41 INFO] SAVEPOINT 	2         	inner     	exit      	2
[2019-05-03 15:29:21,408 counter 40 INFO] ATOMIC    	201       	main      	          	201
[2019-05-03 15:29:21,960 counter 41 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:29:21,962 counter 41 INFO] SAVEPOINT 	2         	outer     	exit      	2
[2019-05-03 15:29:22,421 counter 40 INFO] ATOMIC    	202       	main      	enter     	2
[2019-05-03 15:29:22,474 counter 41 INFO] SAVEPOINT 	3         	outer     	enter     	2
[2019-05-03 15:29:23,426 counter 40 INFO] ATOMIC    	202       	main      	save      	202
[2019-05-03 15:29:23,979 counter 41 INFO] SAVEPOINT 	3         	outer     	          	2
[2019-05-03 15:29:24,431 counter 40 INFO] ATOMIC    	202       	main      	exit      	202
[2019-05-03 15:29:24,986 counter 41 INFO] SAVEPOINT 	3         	outer     	          	202
[2019-05-03 15:29:24,992 counter 41 INFO] SAVEPOINT 	3         	outer     	          	3
[2019-05-03 15:29:24,996 counter 41 INFO] SAVEPOINT 	3         	inner     	enter     	3
[2019-05-03 15:29:25,001 counter 41 INFO] SAVEPOINT 	3         	inner     	save      	4
[2019-05-03 15:29:25,005 counter 41 INFO] SAVEPOINT 	3         	inner     	exit      	4
[2019-05-03 15:29:25,436 counter 40 INFO] ATOMIC    	202       	main      	          	202
[2019-05-03 15:29:26,015 counter 41 INFO] SAVEPOINT 	3         	outer     	          	4
[2019-05-03 15:29:26,017 counter 41 INFO] SAVEPOINT 	3         	outer     	exit      	4
[2019-05-03 15:29:26,449 counter 40 INFO] ATOMIC    	203       	main      	enter     	4
[2019-05-03 15:29:27,454 counter 40 INFO] ATOMIC    	203       	main      	save      	203
[2019-05-03 15:29:28,466 counter 40 INFO] ATOMIC    	203       	main      	exit      	203
[2019-05-03 15:29:29,471 counter 40 INFO] ATOMIC    	203       	main      	          	203
```

#### 2. app_proxysql with proxysql TX_ISOLATION set to REPEATABLE-READ

```
docker-compose exec app_proxysql bash -c "./manage.py test_savepoints"
```

**OUTPUT**

```
[2019-05-03 15:30:49,175 counter 60 INFO] ATOMIC    	200       	main      	enter     	203
[2019-05-03 15:30:49,186 counter 61 INFO] SAVEPOINT 	1         	outer     	enter     	203
[2019-05-03 15:30:50,182 counter 60 INFO] ATOMIC    	200       	main      	save      	200
[2019-05-03 15:30:50,691 counter 61 INFO] SAVEPOINT 	1         	outer     	          	203
[2019-05-03 15:30:51,187 counter 60 INFO] ATOMIC    	200       	main      	exit      	200
[2019-05-03 15:30:51,697 counter 61 INFO] SAVEPOINT 	1         	outer     	          	200
[2019-05-03 15:30:51,701 counter 61 INFO] SAVEPOINT 	1         	outer     	          	1
[2019-05-03 15:30:51,704 counter 61 INFO] SAVEPOINT 	1         	inner     	enter     	1
[2019-05-03 15:30:51,708 counter 61 INFO] SAVEPOINT 	1         	inner     	save      	2
[2019-05-03 15:30:51,711 counter 61 INFO] SAVEPOINT 	1         	inner     	exit      	2
[2019-05-03 15:30:52,192 counter 60 INFO] ATOMIC    	200       	main      	          	200
[2019-05-03 15:30:52,715 counter 61 INFO] SAVEPOINT 	1         	outer     	          	2
[2019-05-03 15:30:52,716 counter 61 INFO] SAVEPOINT 	1         	outer     	exit      	2
[2019-05-03 15:30:53,202 counter 60 INFO] ATOMIC    	201       	main      	enter     	2
[2019-05-03 15:30:53,227 counter 61 INFO] SAVEPOINT 	2         	outer     	enter     	2
[2019-05-03 15:30:54,215 counter 60 INFO] ATOMIC    	201       	main      	save      	201
[2019-05-03 15:30:54,734 counter 61 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:30:55,227 counter 60 INFO] ATOMIC    	201       	main      	exit      	201
[2019-05-03 15:30:55,740 counter 61 INFO] SAVEPOINT 	2         	outer     	          	201
[2019-05-03 15:30:55,745 counter 61 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:30:55,750 counter 61 INFO] SAVEPOINT 	2         	inner     	enter     	2
[2019-05-03 15:30:55,755 counter 61 INFO] SAVEPOINT 	2         	inner     	save      	3
[2019-05-03 15:30:55,758 counter 61 INFO] SAVEPOINT 	2         	inner     	exit      	2
[2019-05-03 15:30:56,236 counter 60 INFO] ATOMIC    	201       	main      	          	201
[2019-05-03 15:30:56,765 counter 61 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:30:56,768 counter 61 INFO] SAVEPOINT 	2         	outer     	exit      	2
[2019-05-03 15:30:57,245 counter 60 INFO] ATOMIC    	202       	main      	enter     	2
[2019-05-03 15:30:57,280 counter 61 INFO] SAVEPOINT 	3         	outer     	enter     	2
[2019-05-03 15:30:58,251 counter 60 INFO] ATOMIC    	202       	main      	save      	202
[2019-05-03 15:30:58,786 counter 61 INFO] SAVEPOINT 	3         	outer     	          	2
[2019-05-03 15:30:59,260 counter 60 INFO] ATOMIC    	202       	main      	exit      	202
[2019-05-03 15:30:59,791 counter 61 INFO] SAVEPOINT 	3         	outer     	          	202
[2019-05-03 15:30:59,795 counter 61 INFO] SAVEPOINT 	3         	outer     	          	3
[2019-05-03 15:30:59,799 counter 61 INFO] SAVEPOINT 	3         	inner     	enter     	3
[2019-05-03 15:30:59,802 counter 61 INFO] SAVEPOINT 	3         	inner     	save      	4
[2019-05-03 15:30:59,805 counter 61 INFO] SAVEPOINT 	3         	inner     	exit      	4
[2019-05-03 15:31:00,264 counter 60 INFO] ATOMIC    	202       	main      	          	202
[2019-05-03 15:31:00,812 counter 61 INFO] SAVEPOINT 	3         	outer     	          	4
[2019-05-03 15:31:00,814 counter 61 INFO] SAVEPOINT 	3         	outer     	exit      	4
[2019-05-03 15:31:01,278 counter 60 INFO] ATOMIC    	203       	main      	enter     	4
[2019-05-03 15:31:02,288 counter 60 INFO] ATOMIC    	203       	main      	save      	203
[2019-05-03 15:31:03,300 counter 60 INFO] ATOMIC    	203       	main      	exit      	203
[2019-05-03 15:31:04,308 counter 60 INFO] ATOMIC    	203       	main      	          	203
```

#### 3. app_db with TX_ISOLATION set to REPEATABLE-READ

```
docker-compose exec app_db bash -c "TX_ISOLATION='repeatable read' ./manage.py test_savepoints"
```

**OUTPUT**

```
[2019-05-03 15:33:40,675 counter 54 INFO] ATOMIC    	200       	main      	enter     	203
[2019-05-03 15:33:40,679 counter 55 INFO] SAVEPOINT 	1         	outer     	enter     	203
[2019-05-03 15:33:41,681 counter 54 INFO] ATOMIC    	200       	main      	save      	200
[2019-05-03 15:33:42,187 counter 55 INFO] SAVEPOINT 	1         	outer     	          	203
[2019-05-03 15:33:42,689 counter 54 INFO] ATOMIC    	200       	main      	exit      	200
[2019-05-03 15:33:43,191 counter 55 INFO] SAVEPOINT 	1         	outer     	          	203
[2019-05-03 15:33:43,194 counter 55 INFO] SAVEPOINT 	1         	outer     	          	1
[2019-05-03 15:33:43,196 counter 55 INFO] SAVEPOINT 	1         	inner     	enter     	1
[2019-05-03 15:33:43,199 counter 55 INFO] SAVEPOINT 	1         	inner     	save      	2
[2019-05-03 15:33:43,200 counter 55 INFO] SAVEPOINT 	1         	inner     	exit      	2
[2019-05-03 15:33:43,695 counter 54 INFO] ATOMIC    	200       	main      	          	200
[2019-05-03 15:33:44,204 counter 55 INFO] SAVEPOINT 	1         	outer     	          	2
[2019-05-03 15:33:44,205 counter 55 INFO] SAVEPOINT 	1         	outer     	exit      	2
[2019-05-03 15:33:44,704 counter 54 INFO] ATOMIC    	201       	main      	enter     	2
[2019-05-03 15:33:44,715 counter 55 INFO] SAVEPOINT 	2         	outer     	enter     	2
[2019-05-03 15:33:45,710 counter 54 INFO] ATOMIC    	201       	main      	save      	201
[2019-05-03 15:33:46,222 counter 55 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:33:46,717 counter 54 INFO] ATOMIC    	201       	main      	exit      	201
[2019-05-03 15:33:47,228 counter 55 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:33:47,233 counter 55 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:33:47,236 counter 55 INFO] SAVEPOINT 	2         	inner     	enter     	2
[2019-05-03 15:33:47,240 counter 55 INFO] SAVEPOINT 	2         	inner     	save      	3
[2019-05-03 15:33:47,243 counter 55 INFO] SAVEPOINT 	2         	inner     	exit      	2
[2019-05-03 15:33:47,721 counter 54 INFO] ATOMIC    	201       	main      	          	201
[2019-05-03 15:33:48,246 counter 55 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:33:48,248 counter 55 INFO] SAVEPOINT 	2         	outer     	exit      	2
[2019-05-03 15:33:48,728 counter 54 INFO] ATOMIC    	202       	main      	enter     	2
[2019-05-03 15:33:48,755 counter 55 INFO] SAVEPOINT 	3         	outer     	enter     	2
[2019-05-03 15:33:49,734 counter 54 INFO] ATOMIC    	202       	main      	save      	202
[2019-05-03 15:33:50,260 counter 55 INFO] SAVEPOINT 	3         	outer     	          	2
[2019-05-03 15:33:50,746 counter 54 INFO] ATOMIC    	202       	main      	exit      	202
[2019-05-03 15:33:51,264 counter 55 INFO] SAVEPOINT 	3         	outer     	          	2
[2019-05-03 15:33:51,268 counter 55 INFO] SAVEPOINT 	3         	outer     	          	3
[2019-05-03 15:33:51,272 counter 55 INFO] SAVEPOINT 	3         	inner     	enter     	3
[2019-05-03 15:33:51,275 counter 55 INFO] SAVEPOINT 	3         	inner     	save      	4
[2019-05-03 15:33:51,280 counter 55 INFO] SAVEPOINT 	3         	inner     	exit      	4
[2019-05-03 15:33:51,750 counter 54 INFO] ATOMIC    	202       	main      	          	202
[2019-05-03 15:33:52,287 counter 55 INFO] SAVEPOINT 	3         	outer     	          	4
[2019-05-03 15:33:52,289 counter 55 INFO] SAVEPOINT 	3         	outer     	exit      	4
[2019-05-03 15:33:52,759 counter 54 INFO] ATOMIC    	203       	main      	enter     	4
[2019-05-03 15:33:53,766 counter 54 INFO] ATOMIC    	203       	main      	save      	203
[2019-05-03 15:33:54,773 counter 54 INFO] ATOMIC    	203       	main      	exit      	203
[2019-05-03 15:33:55,777 counter 54 INFO] ATOMIC    	203       	main      	          	203
```

#### 4. app_proxysql with app TX_ISOLATION set to REPEATABLE-READ, and same in ProxySQL

```
docker-compose exec app_proxysql bash -c "TX_ISOLATION='repeatable read' ./manage.py test_savepoints"
```

**OUTPUT**

```
[2019-05-03 15:35:56,221 counter 74 INFO] ATOMIC    	200       	main      	enter     	203
[2019-05-03 15:35:56,226 counter 75 INFO] SAVEPOINT 	1         	outer     	enter     	203
[2019-05-03 15:35:57,229 counter 74 INFO] ATOMIC    	200       	main      	save      	200
[2019-05-03 15:35:57,731 counter 75 INFO] SAVEPOINT 	1         	outer     	          	203
[2019-05-03 15:35:58,236 counter 74 INFO] ATOMIC    	200       	main      	exit      	200
[2019-05-03 15:35:58,736 counter 75 INFO] SAVEPOINT 	1         	outer     	          	200
[2019-05-03 15:35:58,740 counter 75 INFO] SAVEPOINT 	1         	outer     	          	1
[2019-05-03 15:35:58,743 counter 75 INFO] SAVEPOINT 	1         	inner     	enter     	1
[2019-05-03 15:35:58,746 counter 75 INFO] SAVEPOINT 	1         	inner     	save      	2
[2019-05-03 15:35:58,748 counter 75 INFO] SAVEPOINT 	1         	inner     	exit      	2
[2019-05-03 15:35:59,241 counter 74 INFO] ATOMIC    	200       	main      	          	200
[2019-05-03 15:35:59,755 counter 75 INFO] SAVEPOINT 	1         	outer     	          	2
[2019-05-03 15:35:59,757 counter 75 INFO] SAVEPOINT 	1         	outer     	exit      	2
[2019-05-03 15:36:00,250 counter 74 INFO] ATOMIC    	201       	main      	enter     	2
[2019-05-03 15:36:00,266 counter 75 INFO] SAVEPOINT 	2         	outer     	enter     	2
[2019-05-03 15:36:01,258 counter 74 INFO] ATOMIC    	201       	main      	save      	201
[2019-05-03 15:36:01,771 counter 75 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:36:02,265 counter 74 INFO] ATOMIC    	201       	main      	exit      	201
[2019-05-03 15:36:02,776 counter 75 INFO] SAVEPOINT 	2         	outer     	          	201
[2019-05-03 15:36:02,780 counter 75 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:36:02,783 counter 75 INFO] SAVEPOINT 	2         	inner     	enter     	2
[2019-05-03 15:36:02,787 counter 75 INFO] SAVEPOINT 	2         	inner     	save      	3
[2019-05-03 15:36:02,790 counter 75 INFO] SAVEPOINT 	2         	inner     	exit      	2
[2019-05-03 15:36:03,272 counter 74 INFO] ATOMIC    	201       	main      	          	201
[2019-05-03 15:36:03,794 counter 75 INFO] SAVEPOINT 	2         	outer     	          	2
[2019-05-03 15:36:03,795 counter 75 INFO] SAVEPOINT 	2         	outer     	exit      	2
[2019-05-03 15:36:04,283 counter 74 INFO] ATOMIC    	202       	main      	enter     	2
[2019-05-03 15:36:04,304 counter 75 INFO] SAVEPOINT 	3         	outer     	enter     	2
[2019-05-03 15:36:05,289 counter 74 INFO] ATOMIC    	202       	main      	save      	202
[2019-05-03 15:36:05,811 counter 75 INFO] SAVEPOINT 	3         	outer     	          	2
[2019-05-03 15:36:06,296 counter 74 INFO] ATOMIC    	202       	main      	exit      	202
[2019-05-03 15:36:06,815 counter 75 INFO] SAVEPOINT 	3         	outer     	          	202
[2019-05-03 15:36:06,819 counter 75 INFO] SAVEPOINT 	3         	outer     	          	3
[2019-05-03 15:36:06,821 counter 75 INFO] SAVEPOINT 	3         	inner     	enter     	3
[2019-05-03 15:36:06,824 counter 75 INFO] SAVEPOINT 	3         	inner     	save      	4
[2019-05-03 15:36:06,827 counter 75 INFO] SAVEPOINT 	3         	inner     	exit      	4
[2019-05-03 15:36:07,301 counter 74 INFO] ATOMIC    	202       	main      	          	202
[2019-05-03 15:36:07,831 counter 75 INFO] SAVEPOINT 	3         	outer     	          	4
[2019-05-03 15:36:07,833 counter 75 INFO] SAVEPOINT 	3         	outer     	exit      	4
[2019-05-03 15:36:08,309 counter 74 INFO] ATOMIC    	203       	main      	enter     	4
[2019-05-03 15:36:09,317 counter 74 INFO] ATOMIC    	203       	main      	save      	203
[2019-05-03 15:36:10,324 counter 74 INFO] ATOMIC    	203       	main      	exit      	203
[2019-05-03 15:36:11,327 counter 74 INFO] ATOMIC    	203       	main      	          	203
```
