import csv
import pymysql.cursors

# Connect to the database
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='12345678',
    db='ymatou',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor)

with open('/home/tacy/kuwei.csv', newline='') as f:
    reader = csv.reader(f)
    locale = ''
    sql = 'update stock_stock s inner join stock_product p on s.product_id=p.id set location=%s where p.jancode=%s and s.inventory_id=4'

    try:
        with connection.cursor() as cursor:
            for row in reader:
                if row[1]:
                    locate = row[1]
                # Create a new record
                affected_rows = cursor.execute(sql, (locate, row[0]))
                if not affected_rows:
                    print('update locate failed, jancode:{}, locate:{}'.format(
                        row[0], locate))

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        connection.commit()
    finally:
        connection.close()
