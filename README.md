<h1 align="center">Test Task Doc Process</h1> 
        
<h2 align="center">Скрипт для обработки документов</h2>

 Cтек проекта:
  
      1. Python==3.11
      
      2. PostgreSQL

-------------------------------------
<h2 align="left">Для запуска скрипта необходимо:</h2>
  
• Установить виртуальное окружение в корневой папке проекта командой:
```shell
python3.11 -m venv venv
```
• Запустить виртуальное окружение командой:
```shell
source venv/bin/activate
```
• Создать базу данных PostgreSQL

• Создайте таблицы в базе данных:
```shell
CREATE TABLE IF NOT EXISTS public.data
(
    object character varying(50) COLLATE pg_catalog."default" NOT NULL,
    status integer,
    level integer,
    parent character varying COLLATE pg_catalog."default",
    owner character varying(14) COLLATE pg_catalog."default",
    CONSTRAINT data_pkey PRIMARY KEY (object)
)
```
```shell
CREATE TABLE IF NOT EXISTS public.documents
(
    doc_id character varying COLLATE pg_catalog."default" NOT NULL,
    recieved_at timestamp without time zone,
    document_type character varying COLLATE pg_catalog."default",
    document_data jsonb,
    processed_at timestamp without time zone,
    CONSTRAINT documents_pkey PRIMARY KEY (doc_id)
)
```
• Создать в корне проекта файл ```.env``` и заполнить данные по образцу из файла ```.env.sample```

• Установить все необходимые зависимости, указанные в файле ```requirements.txt```:
```shell
pip install -r requirements.txt
```

• Запустить скрипт ```data_filler.py``` для заполнения базы данных:
```shell
python data_filler.py
```

• Запустить скрипт ```main.py``` для обработки документов:
```shell
python main.py
```
-------------------------------------
<h2 align="left">Логика работы:</h2>

После запуска скрипт берет из таблицы ```documents``` 1 необработанный документ (сортировка по полю ```recived_at ASC```) с типом ```transfer_document``` и обрабатывает по алгоритму:

1. Взять объекты из ключа objects

2. Собрать полный список объектов из таблицы ```data```, учитывая, что в ключе ```objects``` содержатся объекты, у которых есть связанные дочерние объекты (связь по полю parent таблицы ```datа```)

3. Изменить данные для объектов в таблице ```data```, если они подходят под условие блока ```operation_details```, где каждый ключ это название поля, внутри блок со старым значением в ключе ```old```, которое нужно проверить, и новое значение в ключе ```new```, на которое нужно изменить данные.

Пример:

    "owner": {
        "new": "owner_4",
        "old": "owner_3"
    },
    "название поля в бд": {
        "new": "значение, на которое меняем",
        "old": "старое значение, которе нужно проверить, может быть массивом"
    }
3. После обработки документа в таблице ```documents``` поставить отметку времени в поле ```processed_at```, это означает, что документ обработан

4. Если всё завершилось успешно, возвращаем ```True```, если нет - ```False```
