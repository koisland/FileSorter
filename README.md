# FileSorter
A file sorter built in PyQt. I started working on this around 10/2020 right after getting hired at CAHFS San Bernardino. 
Their file organization was in bad shape, so I thought this would help; I scrapped that thought after realizing that running 
scripts on company networks seemed like a bad idea. While functional, I would only really use this if there was no prior 
folders/organization as I didn't implement a way to revert changes. :P

<p align="center">
    <img src=""/>

</p>

## Sorting
Sorts based on three categories: **date**, **file type**, and **keywords**.

Categories can be omitted or reordered and will result in different nested arrangement of files.

<p align="middle">
   <img src="/docs/date_keyword.png"/>

   
</p>

1. Date
   * Sorts based on the day, month or year a file was created, accessed, or modified.
   * Date can be optionally provided to only sort files that fall within a timeframe.
2. File Type
   * Sorts based on file types defined by mimetypes.
   * File extensions can be optionally added and used as sort parameters.
3. Keyword
   * Sorts based on provided keywords which can be grouped in folders.
