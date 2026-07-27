import urllib.request, json, time

data=json.dumps({'variables':{'Marketing Budget': 50000, 'Product Price': 199, 'Discount Rate': 15, 'Customer Churn Rate': 3.5}}).encode('utf-8')
req=urllib.request.Request('http://localhost:8000/api/v1/simulator/run', data=data, headers={'Content-Type': 'application/json'})

end_time=time.time()+30
while time.time()<end_time:
    try:
        res = urllib.request.urlopen(req).read().decode('utf-8')
        print(res)
        break
    except Exception as e:
        time.sleep(2)
