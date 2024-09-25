# ptcg_event_finder

This Bot is able to go through the event finder portion of the pokemon website and extract the data, and post it in discord.

The only command it has is *!events*.

This command will take all of the most recent event data and display it in the channel it was called from. There are a few other things it does as well.

First, if the calling channel has a name that contains "cup" in it, it will only print out info on cups, and the same is for challenges. otherwise, it does both.

Second, it takes the relevant months worth of current data, and deletes any of its old messages that contain data from those months, that way it is cleaner and less spammy.

Here is an example of the output format:
![image](https://github.com/user-attachments/assets/1bcd2360-a991-420f-9f31-2eef0e0f3f61)
