# KommBot (or Gordon's Bot)
Or, a rude awakening to asynchronous coroutines and how to make mistakes around every corner.

## Last time on Kommbot:
So yeah. It kind of worked before this update. As in, it would grab tweets and repost them. There definitely were some problems though. The most annoying one was how closing the bot with ctrl-c was a pain. Like sometimes the bot would disconnect but command prompt just wouldn't return. That's fixed now with a 'daemon' flag. Now the full text is posted into Discord, since apparently the 'text' field is (sometimes) a shortened version of the tweet (why though). Also, I forgot to include the sample config. Woops.

## New with this update
The big change this time is that tweets are now translated. This is done by sending the text of the tweet to Microsoft Azure translate. I wanted to use Google Cloud Translate but I got confused on the pricing and sales never got back to me. Azure is apparently free if you don't use it too much so I went with that. This does mean the bot now requires 3 different sets of authorization keys. Anyways, Microsoft translate is kinda finnicky, especially with hashtags (normally not a problem, but really sucks when translating tweets) so a bit of tweaking is done to the text before sending it over. Also there's a last minute change to try to fix the stupid incomplete read bug. Hope it doesn't blow everything up.

## Going forward
I'm going to keep testing it locally as I prepare to host it on Google cloud since apparently you can run a small instance for free. As of right now, it kind of does everything I wanted it to. I just need to get it off my computer so I can turn it off at night.
