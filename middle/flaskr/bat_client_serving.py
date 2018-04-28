import time
while True:
	start_time = time.time()
	time.sleep(10)
	print("bat is alive: " + str(time.time()-start_time))