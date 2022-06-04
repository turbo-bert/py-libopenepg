# OpenEPG

It is a parser for german tv announcements.

This is the core library without the UI.

If you looking for the UI/Windows application, take a look at

https://github.com/turbo-bert/tvepg

# How does it work

The library ships code that is able to get the key information out of the broadcasters website.

`openepg` requires `requests` or alternatively commandline access to `curl` which comes with Windows since version 10.

It works completely anonymous. There are no callbacks and there is no data access necessary to the project site.

This is the only way to avoid legal copyright implications.


# Data Format



# Example

## List available channels

    import openepg
    
    print(openepg.list_channels())

will output something like

    ['ard']
    

# Troubleshooting

## Purified Content

Special characters will be stripped, sorry. I aim for maximum compatibility. Do not rely on consistency. The results are human-understandable - not totally stable. It will mainly be a..z, A..Z, 0..9 plus dashes and spaces.

## Frequent Updates

As you can imagine, website do change. So the definitions for information extraction must be updated from time to time.

# Contribute

## Add New Broadcasters

You want to help? You want to see another channel listed? If you're capable you can submit the URL parameterized to the date how to retrieve the day's program announcements. Create an issue for that.

## Support

You think this is useful? You want to support the effort? Send money :) https://www.paypal.me/turbobert82?country.x=DE&locale.x=de_DE
