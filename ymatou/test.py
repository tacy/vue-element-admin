import aiomysql
import asyncio


async def select(loop, sql, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            r = await cur.fetchone()
            print(r[0], r)
            print(type(r[0]))


async def insert(loop, sql, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.executemany(sql, [(None, 1, 'a?'), (None, 3, '')])
            await conn.commit()


async def main(loop):
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='12345678',
        db='ymatou',
        loop=loop)
    c1 = select(loop=loop, sql='select max(a) from test limit 1', pool=pool)
    c2 = insert(
        loop=loop,
        sql="insert into test (a,b,c ) values (%s, %s,%s)",
        pool=pool)

    tasks = [asyncio.ensure_future(c1), asyncio.ensure_future(c2)]
    return await asyncio.gather(*tasks)


if __name__ == '__main__':
    cur_loop = asyncio.get_event_loop()
    cur_loop.run_until_complete(main(cur_loop))

# import asyncio

# async def msg(text):
#     await asyncio.sleep(0.1)
#     print(text)

# async def long_operation():
#     print('long_operation started')
#     await asyncio.sleep(3)
#     print('long_operation finished')

# async def main():
#     await msg('first')

#     # Now you want to start long_operation, but you don't want to wait it finised:
#     # long_operation should be started, but second msg should be printed immediately.
#     # Create task to do so:
#     # task = asyncio.ensure_future(long_operation())
#     await long_operation()

#     await msg('second')

#     # Now, when you want, you can await task finised:
#     # await task

# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())
