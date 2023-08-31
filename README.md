## a11yGPT
This repo contains everything you need to launch a ChatGPT integrated service that interacts with website code. Particularly, I am publishing this work so others create a ChatGPT-powered integration for [Equalify](http://github.com/bbertucc/equalify). 

## Getting Started
To get started:
1. Pull down repo.
2. Search and replace "YOUR_API_KEY" with a ChatGPT and ScapingBee key.
3. Update any prompts in `utils.py` under `messages`.
2. Run `python3 -m venv venv`
3. Run `source venv/bin/activate`
4. If you haven't already, install libraries, `pip install -r requirements.txt`
5. Run `python3 app.py`

Check it out!

Sample request: `curl -X POST -d "token=[YOUR_TOKEN]&url=https://htmlpreview.github.io/?https://raw.githubusercontent.com/bbertucc/equalify-a11yGPT-tests/main/1.1.1-fail.html" http://localhost:5000/api/start_session`

You can get the YOUR_TOKEN by logging into the service.

The sample user is in `utils.py`.

## Project Goal
I hope this project inspires a service that can integrate with [equalify.app](http://equalify.app). Ideally, this service would use ChatGPT to detect issues that services like axe cannot test.

If you successfully create that service, get in touch! I'm [on TwXtter](https://x.com/bbertucc) and can pinged on GitHub, [@bbertucc](https://github.com/bbertucc/).
