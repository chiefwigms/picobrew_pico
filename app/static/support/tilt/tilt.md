# Using Tilt with picobrew_pico server

## Configuring Tilt for Use with Server

Tilt support is provided in two ways

- Natively via bluetooth in the picobrew_pico server. This should work out of the box for linux/windows/mac as long as the tilt is within range of the picobrew_pico server.
- Using pytilt to send to picobrew via an API call. This is just a backup/alternative and only needed if you can't use bluetooth on the server, or you don't ferment within range of the server.

### Pytilt
See [pytilt on github](https://github.com/atlefren/pytilt) for details on how to install and setup pytilt if needed, but all you have to do is set the environment variable

>PYTILT_URL=http://your-picobrew_pico-server/API/tilt

and setup pytilt as usual and picobrew will get the data.

Please note that if using pytilt you will be limited to only one Tilt of each color, and no RSSI will be reported.

## Setup the Server Devices Page
Now that your tilt is configured and sending data to your server, let's add it to the server's device list. On a browser connected to the server's AP, open the server. Under the **System** pulldown menu, select **Devices**. After clicking **+ Add New Device** you should see a page similar to this:

  ![Server Setup](/static/support/tilt/Server_Devices.png)

Perform the following steps:
  * Under the **Machine Type** pulldown select *Tilt*
  * In the **Machine/Product ID** box, enter the ID from the [home page](/)
  * In the Alias box, add any fun or useful name you'd like.
  * Click **Save**

## Additional References

The Tilt website is pretty comprehensive and has additional guides at [TiltHydrometer.com](https://tilthydrometer.com/pages/guide)

That's it! Have fun monitoring your fermentation and go make some great beer!
