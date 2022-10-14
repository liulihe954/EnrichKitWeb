import time
from celery import shared_task, group
# from webapp.run_loci import task_unit


# @shared_task
# def hello_world2():
#     print('from hello_world before group')
#     group_results = group([task_unit.s(i) for i in range(50)])
#     results = group_results.delay()
#     print('from hello_world after group')
#     while not results.ready():
#         time.sleep(1)
#         print('not ready yet')
#     else:
#         print('ready')
#     out = results.get()
#     return out

# @shared_task
# def hello_world(num=2):
#     time.sleep(num)
#     print(f'from hello_world: {num}')
