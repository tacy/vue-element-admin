import csv
import pymysql.cursors

# Connect to the database
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='asd12288',
    db='ymatou',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor)

with open('./kuwei.csv', newline='') as f:
    reader = csv.reader(f)
    location = ''
    sql = 'update stock_stock s inner join stock_product p on s.product_id=p.id set location=%s where p.jancode=%s and s.inventory_id=4'
    query_sql = 'select p.jancode, s.location from stock_stock s inner join stock_product p on s.product_id=p.id where s.inventory_id=4 and p.jancode=%s'
    product_sql = 'select id,jancode from stock_product where jancode=%s'
    insert_sql = 'insert into stock_stock (quantity, inflight, preallocation, inventory_id,product_id) values(0,0,0,4,%s)'

    try:
        with connection.cursor() as cursor:
            for row in reader:
                if row[1]:
                    location = row[1]
                # Create a new record

                cursor.execute(query_sql, (row[0]))
                result = cursor.fetchall()
                if not result:
                    cursor.execute(product_sql, (row[0]))
                    result = cursor.fetchall()
                    if not result:
                        print('jancode does not exist: %s' % (row[0]))
                        continue
                    else:
                        cursor.execute(insert_sql, (result[0]['id']))
                        result[0]['location'] = None
                db_location = result[0]['location']
                if db_location and location not in db_location:
                    db_location = db_location + ',' + location
                else:
                    db_location = location
                cursor.execute(sql, (db_location, row[0]))
                connection.commit()

        # connection is not autocommit by default. So you must commit to save
        # your changes.

    finally:
        connection.close()
