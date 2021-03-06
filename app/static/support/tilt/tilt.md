# Using Tilt with picobrew_pico server

## Configuring Tilt for Use with Server

Tilt support is based on using pytilt to get the data from the tilt using bluetooth and send to picobrew via an API call.

See [pytilt on github](https://github.com/atlefren/pytilt) for details on how to install and set it up, but all you have to do is set the environment variable

>PYTILT_URL=http://your-picobrew_pico-server/API/tilt

and setup pytilt as usual and picobrew will get the data.

## Setup the Server Devices Page
Now that your tilt is configured and sending data to your server, let's add it to the server's device list. On a browser connected to the server's AP, open the server. Under the **System** pulldown menu, select **Devices**. After clicking **+ Add New Device** you should see a page similar to this:

  ![Server Setup](/static/support/tilt/Server_Devices.png)

Perform the following steps:
  * Under the **Machine Type** pulldown select *tilt*
  * In the **Machine/Product ID** box, enter the tilt type ("Red", "Green", "Black", "Purple", "Orange", "Blue", "Yellow", "Pink")
  * In the Alias box, add any fun or useful name you'd like.
  * Click **Save**

## Additional References

The Tilt website is pretty comprehensive and has additional guides at [TiltHydrometer.com](https://tilthydrometer.com/pages/guide)

That's it! Have fun monitoring your fermentation and go make some great beer!
