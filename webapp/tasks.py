# import time
# from celery import shared_task, group

# from webapp import models



# a = models.Task.objects.filter(jobid='be895ec8-d7b3-4a98-ba91-2ad16dd03577').exists()


# @shared_task
# def hello(a):
#     print(f"debug {a}")
#     return

# @shared_task
# def task_unit(a):
#     print('unit - ', a)
#     return
    

# @shared_task
# def hello_world2():
#     print('from hello_world before group')
#     group_results = group([task_unit.s(i) for i in range(50)])
#     results = group_results.delay()
#     print('results - id ', results.id)
#     # print(results)
#     print('from hello_world after group')
#     # while not results.ready():
#     #     time.sleep(1)
#     #     print('not ready yet')
#     # else:
#     #     print('ready')
#     out = results.get()
#     return out