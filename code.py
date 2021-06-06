import ssl
import wifi
import socketpool
import displayio
import adafruit_requests
from adafruit_magtag.magtag import MagTag
from secrets import secrets


SLEEP_SECS = 15 * 60
magtag = MagTag()

wifi.radio.connect(secrets['ssid'], secrets['password'])
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# ip addresses won't work with this get method at the time of writing
# url also requires 3 / chars to do some splitting...
response = requests.get(secrets['keps_url'])
rawbytes = response.content
if len(rawbytes) != 9472:
    raise RuntimeError('Response does not have the expected size!')

bitmap = displayio.Bitmap(296, 128, 4)
palette = displayio.Palette(4)
palette[0] = 0x000000
palette[1] = 0x333333
palette[2] = 0x666666
palette[3] = 0xffffff
# I think there is a bug with bitmaptools for this version
# import io
# import bitmaptools
# file = io.BytesIO(rawbytes)
# bitmaptools.readinto(
#     bitmap,
#     file,
#     bits_per_pixel=2,
#     element_size=1,
#     reverse_pixels_in_element=True,
#     reverse_rows=True
# )
for i, b in enumerate(list(rawbytes)):
    bitmap[i * 4] = (b & 0b11000000) >> 6
    bitmap[i * 4 + 1] = (b & 0b00110000) >> 4
    bitmap[i * 4 + 2] = (b & 0b00001100) >> 2
    bitmap[i * 4 + 3] = b & 0b00000011

group = displayio.Group()
tilegrid = displayio.TileGrid(bitmap, pixel_shader=palette)
group.append(tilegrid)
magtag.display.show(group)
magtag.display.refresh()

magtag.exit_and_deep_sleep(SLEEP_SECS)
