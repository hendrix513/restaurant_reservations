# restaurant_reservations
app for reserving tables at a restaurant

to use, run command 'docker-compose -f heroku.yml up -d --build --force-recreate' from top level directory. This will deploy the app on localhost:8000

APIs:
(POST) /reservation      required arguments: 'size' - number of people to make reservation for 
                         returns {'success' : True/False, 'reservation_num': id of reservation if success, otherwise None}
(POST) /cancel_reservation      required arguments: 'reservation_num' - id of reservation to cancel
(GET) /available_tables         returns dictionary of table names mapped to the number of seats for that table

examples:

from command line:
curl localhost:8000/available_tables

curl --request POST --data '{"size":10}' http://localhost:8000/reservation

curl --request POST --data '{"reservation_num":1}' http://localhost:8000/cancel_reservation
