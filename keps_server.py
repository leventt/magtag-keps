import os
import io
from threading import Timer
import numpy as np
from PIL import Image
from matplotlib import image
from flask import Flask
from flask import send_file
from selenium import webdriver


# magtag screen resolution
WIDTH = 296
HEIGHT = 128
# where to save the cropped image
KEPS = 'keps.png'
# how frequently to capture image from selenium
KEPS_REPEAT_MINUTES = 15


def _keps():
    chrome_options = webdriver.ChromeOptions()
    # notification pop-up will tint the image dark gray
    # so blocking it as a pref is important
    prefs = {'profile.default_content_setting_values.notifications': 2}
    chrome_options.add_experimental_option('prefs', prefs)
    # put the chrome driver next to this file
    driver = webdriver.Chrome(
        os.path.join(os.path.dirname(__file__), 'chromedriver.exe'),
        chrome_options=chrome_options
    )
    driver.maximize_window()
    # you can change this part to adpat to other pages and elements
    driver.get('https://www.reddit.com/r/worldnews/top/?t=hour')
    driver.execute_script(
        'article = document.getElementsByTagName("article")[0];'
        f'article.style.width = "{WIDTH}px";'
        f'article.style.height = "{HEIGHT}px";'
    )
    element = driver.find_element_by_tag_name('article')
    crop = (
        int(element.location['x']),
        int(element.location['y']),
        int(element.location['x'] + WIDTH),
        int(element.location['y'] + HEIGHT),
    )
    driver.save_screenshot(KEPS)
    driver.close()

    if crop is not None:
        with Image.open(KEPS) as im:
            im = im.crop(crop)
            im.save(KEPS)


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def _lumibits(brightness):
    # numpy will probably put these in memory as bytes
    # but it is clearer to write them this way
    if brightness < .25:
        return 0b00  # black
    elif brightness < .5:
        return 0b01  # dark gray
    elif brightness < .75:
        return 0b10  # light gray
    else:
        return 0b11  # white


def _prep_pixels(luminance):
    s = luminance.shape
    _s = set((WIDTH, HEIGHT))
    # i never tested rotated images so it may need more work to make it work
    if s[0] not in _s or s[1] not in [i for i in _s if i != s[0]]:
        raise RuntimeError(
            f'Required dimensions: {WIDTH}x{HEIGHT} or {HEIGHT}x{WIDTH}! {s}'
        )

    return np.vectorize(_lumibits)(luminance)


def _screen_image(image_path):
    rgb = image.imread(image_path)
    if rgb.dtype == np.uint8:
        rgb = rgb.astype(np.float32) / 256
    # this is to get luminance values
    luminance = np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    pixels_2bit = _prep_pixels(luminance)

    bitstring = ''.join(map(lambda x: '{:02b}'.format(x), pixels_2bit.flatten().tolist()))

    if len(bitstring) % 8 != 0:
        raise NotImplementedError()
    return io.BytesIO(int(bitstring, 2).to_bytes(len(bitstring) // 8, 'big'))


if __name__ == '__main__':
    _keps()
    repeat_timer = RepeatTimer(KEPS_REPEAT_MINUTES * 60.0, _keps)
    repeat_timer.start()

    app = Flask(__name__)

    @app.route('/')
    def default_route():
        return send_file(_screen_image(KEPS), mimetype='text/plain')

    app.run(host='0.0.0.0', port=80)
    repeat_timer.cancel()
