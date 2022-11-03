# unbotapp

This app allows the user to either enter lines separated by carriage returns in a text field or in an uploaded text file. The app uses an api key to request a number of photos between 1 and 10 from unsplash with or without a search term. The app then uses the PIL library and various possible fonts to overlay each of the lines of input text in the order they were entered over randomly returned images. If one image is requested this way, it is presented as a download. If more than one image is requested a zip file is presented for download.

![](https://github.com/bfinelli1/unbotapp/blob/main/index.png?raw=true)
