# magtag-keps
 

over-engineered way to get the top post from reddit r/worldnews without using reddit's api


code.py is the circuit python code that should go into magtag. magtag will also need a secrets.py file which should have the ssid/password for the wifi connection and a url for where keps.server.py is serving to.


keps_server.py implements a simple flask server that also has a repeating timer thread. repeaeting timer thread will load "https://www.reddit.com/r/worldnews/top/?t=hour" and it will resize the article elements to the screen size of magtag to take a screen shot of that element. flask server will serve this screen shot after some bit-stuff to convert image into bytes. these bytes signify a color on screen per 2 bits. 2 bits is enough for magtag as it can only display 4 shades.


you can modify the function _keps to have it load/resize/crop another element from another page without needing an api, but you will endd up serving data on your own, which may be defeating the purpose of having that magtag.
